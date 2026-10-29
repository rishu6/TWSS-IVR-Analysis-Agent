import asyncio
import csv
import io
import secrets
from datetime import UTC, datetime, timedelta
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import Response, StreamingResponse
from pydantic import AwareDatetime, BaseModel, Field
from sqlalchemy import func, select

from .auth import digest, principal, require, session_db, utc
from .db import AuditLog, Call, CallEvent, CallLeg, CallParticipant, IntegrationEvent, Lead, LiveTicket, SessionToken, SyncJob, User
from .domain import Event
from .ingestion import ingest
from .reports import exclude_department_calls, has_department_flow, agent_report, department_report, filtered_query, mask_phone, overview, present, recovery_candidates

router = APIRouter(prefix='/api/v1')


@router.post('/admin/sync')
def request_sync(request:Request,tasks:BackgroundTasks,user=Depends(require('Admin')),db=Depends(session_db)):
    worker=getattr(request.app.state,'live_sync',None)
    if not worker:raise HTTPException(409,'Live sync is not running in this mode')
    if worker.lock.locked():return {'status':'ALREADY_RUNNING'}
    db.add(AuditLog(role=user.role,user_id=user.user_id,action='sync_requested',resource='providers'));db.commit()
    tasks.add_task(worker.run)
    return {'status':'REQUESTED'}


def filters(q: str | None = Query(None, max_length=120), department: str | None = None,
            agent: str | None = None, did: str | None = None,
            outcome: Literal['ANSWERED', 'MISSED', 'IVR_ONLY', 'ABANDONED', 'IN_PROGRESS', 'UNKNOWN'] | None = None,
            stage: str | None = None, owner: str | None = None, start: AwareDatetime | None = None,
            end: AwareDatetime | None = None, direction: Literal['inbound', 'outbound'] | None = None):
    if start and end and start >= end:
        raise HTTPException(422, 'Date range must have start before end')
    return dict(q=q, department=department, agent=agent, did=did, outcome=outcome,
                stage=stage, owner=owner, start=start, end=end, direction=direction)


def find_call(db, id):
    call = db.get(Call, id)
    if not call:
        raise HTTPException(404, 'Call not found')
    return call


@router.get('/filter-options')
def filter_options(user=Depends(principal),db=Depends(session_db)):
    def unique(column):return sorted(v for v in db.scalars(select(column).distinct()) if v)
    return {'departments':unique(Call.projection['primary_department'].as_string()),
            'agents':sorted(set(unique(Call.projection['answering_agent'].as_string())+unique(CallLeg.agent)+unique(CallParticipant.agent_name))),
            'stages':unique(Lead.current_stage),'owners':unique(Lead.current_owner)}


@router.get('/metrics/overview')
def metrics(f=Depends(filters), user=Depends(principal), db=Depends(session_db)):
    result = overview(db.scalars(filtered_query(**f)).all())
    if user.role == 'Viewer':
        result['by_did'] = [{**row, 'did': mask_phone(row['did'])} for row in result['by_did']]
    result['synthetic'] = db.info.get('mode', 'demo') == 'demo'
    return result


@router.get('/reports/leadsquared')
def leadsquared_analytics(f=Depends(filters),department_selected:bool=True,
                         page:int=Query(1,ge=1),page_size:int=Query(20,ge=1,le=100),show_all:bool=False,
                         user=Depends(principal),db=Depends(session_db)):
    from .crm_analytics import analytics
    f={**f,'direction':f['direction'] or 'inbound'}
    calls=db.scalars(filtered_query(**f)).all()
    if department_selected:calls=[c for c in calls if has_department_flow(c.projection)]
    summary,items=analytics(db,calls,user.role,False)
    ranking_items=agent_report(exclude_department_calls(calls,'Support'))
    start=0 if show_all else (page-1)*page_size
    return {'summary':summary,'items':items if show_all else items[start:start+page_size],'total':len(items),'ranking_items':ranking_items,
            'next_page':page+1 if not show_all and start+page_size<len(items) else None,
            'scope':'Saved default LeadSquared lead-type index; phone matches only. Call activity logging and historical lead stages are not verified.'}


@router.get('/calls')
def calls(f=Depends(filters), missed_department:bool=False, department_selected:bool=False, show_all:bool=False, page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100),
          user=Depends(principal), db=Depends(session_db)):
    if missed_department or department_selected:
        scope={**f,'outcome':'MISSED'} if missed_department else f
        selected=[c for c in db.scalars(filtered_query(**scope)) if has_department_flow(c.projection)]
        offset=0 if show_all else (page-1)*page_size
        return {'items':[present(c,user.role) for c in (selected if show_all else selected[offset:offset+page_size])],
                'total':len(selected),'page':page,'page_size':page_size,
                'next_page':page+1 if not show_all and offset+page_size<len(selected) else None,'synthetic':db.info.get('mode','demo')=='demo'}
    stmt = filtered_query(**f)
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery()))
    rows = db.scalars(stmt if show_all else stmt.offset((page-1)*page_size).limit(page_size)).all()
    return {'items': [present(c, user.role) for c in rows], 'total': total, 'page': page,
            'page_size': page_size, 'next_page': page+1 if not show_all and page*page_size < total else None, 'synthetic': db.info.get('mode', 'demo') == 'demo'}


@router.get('/calls-summary')
def calls_summary(f=Depends(filters),department_selected:bool=False,user=Depends(principal),db=Depends(session_db)):
    if department_selected:
        selected=[c for c in db.scalars(filtered_query(**{**f,'outcome':None})) if has_department_flow(c.projection)]
        counts={}
        for call in selected:counts[call.final_status]=counts.get(call.final_status,0)+1
        return {'total':len(selected),'outcomes':counts,'missed_department':counts.get('MISSED',0)}
    stmt=filtered_query(**{**f,'outcome':None}).order_by(None).with_only_columns(Call.final_status).subquery()
    counts=dict(db.execute(select(stmt.c.final_status,func.count()).group_by(stmt.c.final_status)).all())
    department_missed=sum(has_department_flow(c.projection) for c in db.scalars(filtered_query(**{**f,'outcome':'MISSED'})))
    return {'total':sum(counts.values()),'outcomes':counts,'missed_department':department_missed}


@router.get('/calls/{id}')
def detail(id: str, user=Depends(principal), db=Depends(session_db)):
    call = find_call(db, id)
    data = present(call, user.role, db=db)
    older = db.scalar(select(func.count()).select_from(Call).where(Call.caller_e164 == call.caller_e164,
                        Call.started_at < call.started_at)) if call.started_at and call.caller_e164 else None
    data['first_observed_in_dataset'] = older == 0 if older is not None else None
    return data


@router.get('/calls/{id}/journey')
def journey(id: str, user=Depends(principal), db=Depends(session_db)):
    return present(find_call(db, id), user.role, journey=True, db=db)


@router.get('/calls/{id}/crm')
def crm(id: str, user=Depends(principal), db=Depends(session_db)):
    return present(find_call(db, id), user.role, db=db)['crm']


@router.get('/calls/{id}/recording')
def recording(id: str, user=Depends(require('Admin', 'Manager')), db=Depends(session_db)):
    find_call(db, id)
    db.add(AuditLog(role=user.role,user_id=user.user_id, action='recording_unavailable', resource=id))
    db.commit()
    raise HTTPException(404, 'Recording unavailable from provider; no URL has been supplied')


@router.get('/reports/agents')
def agents(f=Depends(filters), ranking_exclude_department:str|None=Query(None,max_length=120),
           user=Depends(principal), db=Depends(session_db)):
    calls=db.scalars(filtered_query(**f)).all()
    result={'items':agent_report(calls),'synthetic':db.info.get('mode','demo')=='demo'}
    if ranking_exclude_department:
        eligible=exclude_department_calls(calls,ranking_exclude_department)
        result['ranking_items']=agent_report(eligible)
        result['ranking_excluded_department']=ranking_exclude_department
    return result


@router.get('/reports/departments')
def departments(f=Depends(filters), user=Depends(principal), db=Depends(session_db)):
    return {'items': department_report(db.scalars(filtered_query(**f)).all()),
            'policy': 'Primary department counts once; involvement across departments is not additive', 'synthetic': db.info.get('mode', 'demo') == 'demo'}


@router.get('/reports/missed-calls')
def recovery(request: Request, f=Depends(filters), user=Depends(principal), db=Depends(session_db)):
    # Evaluate against the complete dataset so filters cannot hide eligible callbacks.
    candidates = recovery_candidates(db.scalars(select(Call)).all(), request.app.state.settings.recovery_hours)
    ids = set(db.scalars(filtered_query(**f).with_only_columns(Call.id)).all())
    items = [r for r in candidates if r['call_id'] in ids]
    if user.role == 'Viewer':
        items = [{**r, 'caller': mask_phone(r['caller'])} for r in items]
    return {'items': items, 'synthetic': db.info.get('mode', 'demo') == 'demo', 'matching': 'Candidates require review, not confirmed recovery'}


def csv_safe(value):
    value = '' if value is None else str(value)
    return "'" + value if value.lstrip().startswith(('=', '+', '-', '@', '\t', '\r', '\n')) else value


@router.get('/reports/exports')
def export(request: Request, format: Literal['csv', 'xlsx'] = 'csv', missed_department:bool=False, f=Depends(filters),
           user=Depends(require('Admin', 'Manager')), db=Depends(session_db)):
    db.add(AuditLog(role=user.role,user_id=user.user_id, action=f'export_{format}', resource='filtered_calls'))
    db.commit()
    if missed_department:f={**f,'outcome':'MISSED'}
    columns = ['call_id', 'caller', 'did', 'direction', 'outcome', 'started_at_utc', 'department', 'answering_agent']
    sessions = request.app.state.sessions
    filename='synthetic-calls' if db.info.get('mode')=='demo' else 'calls'

    def rows():
        yield columns
        offset = 0
        with sessions() as export_db:
            while True:
                page = export_db.scalars(filtered_query(**f).offset(offset).limit(250)).all()
                if not page:
                    break
                for call in page:
                    if missed_department and not has_department_flow(call.projection):continue
                    c = call.projection
                    yield [c['id'], c['caller'], c['did'], c['direction'], c['status'], c['started_at'],
                           c['primary_department'], c['answering_agent']]
                offset += len(page)
                export_db.expunge_all()
    if format == 'csv':
        def stream():
            for row in rows():
                buffer = io.StringIO()
                csv.writer(buffer).writerow([csv_safe(v) for v in row])
                yield buffer.getvalue()
        return StreamingResponse(stream(), media_type='text/csv',
                                 headers={'Content-Disposition': f'attachment; filename="{filename}.csv"'})
    from openpyxl import Workbook
    book = Workbook(write_only=True)
    sheet = book.create_sheet('Synthetic calls')
    for row in rows():
        sheet.append([csv_safe(v) for v in row])
    output = io.BytesIO()
    book.save(output)
    return Response(output.getvalue(), media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    headers={'Content-Disposition': f'attachment; filename="{filename}.xlsx"'})


@router.get('/integrations/status')
def sync_status(user=Depends(principal), db=Depends(session_db)):
    job = db.scalar(select(SyncJob).where(SyncJob.status.in_(['SUCCEEDED','PARTIAL']),SyncJob.kind!='history').order_by(SyncJob.completed_at.desc()).limit(1))
    if db.info.get('mode')=='internal':
        from .db import IntegrationState
        rows=db.scalars(select(IntegrationState)).all()
        return {'last_successful_sync':utc(job.completed_at).isoformat() if job else None,
                'dataset_at':None,'mode':'live CDR polling','poll_seconds':60,'live_provider_connected':bool(job),
                'providers':{r.provider:{'status':r.status,'message':r.message,'last_success_at':r.last_success_at} for r in rows}}
    return {'last_successful_sync': utc(job.completed_at).isoformat() if job else None,
            'dataset_at': '2026-10-27T05:50:00+00:00', 'mode': 'synthetic replay',
            'poll_seconds': 30, 'live_provider_connected': False}


class Batch(BaseModel):
    events: list[Event] = Field(min_length=1, max_length=250)


@router.post('/demo/events')
def demo_events(body: Batch, user=Depends(require('Admin')), db=Depends(session_db)):
    if db.info.get('mode')!='demo':raise HTTPException(403,'Synthetic intake disabled for real data')
    try:
        result = ingest(db, body.events)
        db.add(AuditLog(role=user.role,user_id=user.user_id, action='demo_ingest', resource='synthetic_events'))
        db.commit()
        return result
    except ValueError as exc:
        db.rollback()
        db.add(IntegrationEvent(provider='synthetic', payload=body.model_dump(mode='json'), status='REJECTED', error=str(exc)))
        db.commit()
        raise HTTPException(409, str(exc)) from exc


@router.post('/demo/retry-crm')
def retry_crm(user=Depends(require('Admin', 'Manager')), db=Depends(session_db)):
    if db.info.get('mode')!='demo':raise HTTPException(403,'Synthetic CRM actions disabled for real data')
    from .adapters import SyntheticLeadSquaredClient
    from .crm import enrich
    from .demo_data import leads
    for call in db.scalars(select(Call)):
        enrich(db, call, SyntheticLeadSquaredClient(leads()), force=True)
    db.add(AuditLog(role=user.role,user_id=user.user_id, action='simulate_crm_recovery', resource='synthetic_crm'))
    db.commit()
    return {'synthetic': db.info.get('mode', 'demo') == 'demo', 'status': 'Simulated CRM recovery applied'}


@router.post('/webhooks/acefone')
def webhook_disabled(user=Depends(require('Admin'))):
    raise HTTPException(503, 'Live Acefone intake disabled pending documented payload and authentication')


@router.get('/admin/raw-events')
def raw_events(page: int = Query(1, ge=1), user=Depends(require('Admin')), db=Depends(session_db)):
    db.add(AuditLog(role=user.role,user_id=user.user_id, action='raw_events_access', resource='synthetic_events'))
    db.commit()
    return {'items': [r.payload for r in db.scalars(select(CallEvent).order_by(CallEvent.received_at, CallEvent.id)
                                                   .offset((page-1)*50).limit(50))]}


@router.get('/admin/import-issues')
def import_issues(page:int=Query(1,ge=1),user=Depends(require('Admin')),db=Depends(session_db)):
    stmt=select(IntegrationEvent).where(IntegrationEvent.status=='QUARANTINED')
    total=db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows=db.scalars(stmt.order_by(IntegrationEvent.received_at.desc(),IntegrationEvent.id.desc()).offset((page-1)*25).limit(25)).all()
    db.add(AuditLog(role=user.role,user_id=user.user_id,action='import_issues_access',resource='quarantine'));db.commit()
    return {'total':total,'page':page,'items':[{'id':row.id,'received_at':row.received_at,'reason':row.error,
                 'provider_call_id':row.payload.get('call_id'),'direction':row.payload.get('direction')} for row in rows]}


@router.get('/admin/audit')
def audit(page:int=Query(1,ge=1),page_size:int=Query(25,ge=1,le=100),show_all:bool=False,user=Depends(require('Admin')),db=Depends(session_db)):
    stmt=select(AuditLog,User.display_name).outerjoin(User,AuditLog.user_id==User.id).order_by(AuditLog.at.desc(),AuditLog.id.desc())
    total=db.scalar(select(func.count()).select_from(AuditLog))
    rows=db.execute(stmt if show_all else stmt.offset((page-1)*page_size).limit(page_size)).all()
    return {'items':[{'at':row.at,'actor':name or 'System / demo','role':row.role,'action':row.action,
                      'resource':row.resource} for row,name in rows],'page':page,'total':total,'next_page':page+1 if not show_all and page*page_size<total else None}


@router.post('/live-token')
def live_token(user=Depends(principal), db=Depends(session_db)):
    token = secrets.token_urlsafe(32)
    db.add(LiveTicket(token_hash=digest(token), session_hash=user.token_hash,
                      expires_at=datetime.now(UTC) + timedelta(seconds=30)))
    db.commit()
    return {'token': token, 'expires_in': 30}


@router.websocket('/live')
async def live(ws: WebSocket):
    # First frame carries a one-use token; never put credentials in the URL/access log.
    origin = ws.headers.get('origin')
    if origin and origin != ws.app.state.settings.origin:
        await ws.close(code=4403)
        return
    await ws.accept()
    try:
        token = await asyncio.wait_for(ws.receive_text(), timeout=5)
        with ws.app.state.sessions.begin() as db:
            ticket = db.scalar(select(LiveTicket).where(LiveTicket.token_hash == digest(token)).with_for_update())
            session = db.get(SessionToken, ticket.session_hash) if ticket else None
            if (not ticket or not session or utc(ticket.expires_at) <= datetime.now(UTC) or
                    utc(session.expires_at) <= datetime.now(UTC) or
                    digest(ws.cookies.get('session', '')) != session.token_hash):
                await ws.close(code=4401)
                return
            session_hash = session.token_hash
            db.delete(ticket)
        # The demo emits invalidations, never raw customer payloads. Polling remains active in the UI.
        for _ in range(12):
            with ws.app.state.sessions() as db:
                session = db.get(SessionToken, session_hash)
                if not session or utc(session.expires_at) <= datetime.now(UTC):
                    await ws.close(code=4401)
                    return
            await ws.send_json({'type': 'invalidate', 'synthetic': ws.app.state.settings.mode == 'demo'})
            await asyncio.sleep(5)
        await ws.close(code=1000)
    except (WebSocketDisconnect, TimeoutError):
        return
