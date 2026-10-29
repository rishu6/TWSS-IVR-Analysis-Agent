"""Bounded, resumable calendar-day CDR imports using documented provider queries."""
import hashlib
import json
from datetime import UTC,date,datetime,time,timedelta
from zoneinfo import ZoneInfo

from fastapi import APIRouter,BackgroundTasks,Depends,HTTPException,Request
from pydantic import BaseModel
from sqlalchemy import func,select

from .auth import principal,require,session_db,utc
from .cdr import restricted_payload,store_record
from .db import AuditLog,Call,IntegrationEvent,SyncJob,now
from .mappings import apply_mappings
from .provider_clients import LiveAcefoneClient,ProviderError

router=APIRouter(prefix='/api/v1/history')


class ImportRange(BaseModel):
    from_date:date
    through_date:date


def public_job(job):
    return {'id':job.id,'status':job.status,'started_at':utc(job.started_at).isoformat() if job.started_at else None,
            'completed_at':utc(job.completed_at).isoformat() if job.completed_at else None,
            'error':job.error,'details':job.details}


@router.post('/import')
def request_import(body:ImportRange,request:Request,tasks:BackgroundTasks,
                   user=Depends(require('Admin','Manager')),db=Depends(session_db)):
    worker=getattr(request.app.state,'live_sync',None)
    if not worker:raise HTTPException(409,'History import requires the internal live installation')
    today=datetime.now(ZoneInfo(request.app.state.settings.source_timezone)).date()
    if body.from_date>body.through_date or body.through_date>today:
        raise HTTPException(422,'Choose a valid historical date range ending today or earlier')
    if body.from_date<today-timedelta(days=89):
        raise HTTPException(422,'Live imports support the last 90 days; older records need a verified archive import')
    for job in db.scalars(select(SyncJob).where(SyncJob.provider=='acefone',SyncJob.kind=='history',
                                               SyncJob.status.in_(['QUEUED','RUNNING']))):
        if job.details.get('from_date')==str(body.from_date) and job.details.get('through_date')==str(body.through_date):
            return public_job(job)
    zone=ZoneInfo(request.app.state.settings.source_timezone)
    start=datetime.combine(body.from_date,time.min,zone)
    end=min(datetime.combine(body.through_date+timedelta(days=1),time.min,zone),now().astimezone(zone))
    job=SyncJob(provider='acefone',kind='history',status='QUEUED',details={
        'from_date':str(body.from_date),'through_date':str(body.through_date),
        'range_start':start.astimezone(UTC).isoformat(),'range_end':end.astimezone(UTC).isoformat(),
        'next_date':str(body.from_date),'direction_index':0,'next_page':1,
        'records_seen':0,'changed_calls':0,'rejected_records':0,'completed_days':[]})
    db.add(job);db.flush()
    db.add(AuditLog(role=user.role,user_id=user.user_id,action='history_import_requested',resource=str(job.id)))
    db.commit();result=public_job(job)
    tasks.add_task(worker.run)
    return result


@router.get('/imports')
def imports(user=Depends(principal),db=Depends(session_db)):
    rows=db.scalars(select(SyncJob).where(SyncJob.provider=='acefone',SyncJob.kind=='history')
                    .order_by(SyncJob.id.desc()).limit(10)).all()
    earliest,latest=db.execute(select(func.min(Call.started_at),func.max(Call.started_at)).where(Call.provider=='acefone')).one()
    return {'items':[public_job(row) for row in rows],'earliest_call':utc(earliest).isoformat() if earliest else None,
            'latest_call':utc(latest).isoformat() if latest else None,
            'note':'Call timestamps do not prove complete coverage. Completed import jobs describe the ranges actually fetched.'}


@router.post('/imports/{id}/retry')
def retry(id:int,request:Request,tasks:BackgroundTasks,user=Depends(require('Admin','Manager')),db=Depends(session_db)):
    worker=getattr(request.app.state,'live_sync',None)
    if not worker:raise HTTPException(409,'Live sync is unavailable')
    job=db.get(SyncJob,id)
    if not job or job.provider!='acefone' or job.kind!='history':raise HTTPException(404,'History import not found')
    if job.status!='ERROR':raise HTTPException(409,'Only failed imports can be resumed')
    job.status='QUEUED';job.error=None;job.completed_at=None
    db.add(AuditLog(role=user.role,user_id=user.user_id,action='history_import_resumed',resource=str(id)))
    db.commit();result=public_job(job);tasks.add_task(worker.run)
    return result


def process_history(worker,credentials):
    with worker.sessions.begin() as db:
        job=db.scalar(select(SyncJob).where(SyncJob.provider=='acefone',SyncJob.kind=='history',
            SyncJob.status.in_(['QUEUED','RUNNING'])).order_by(SyncJob.id).limit(1).with_for_update())
        if not job:return False
        job.status='RUNNING';job_id=job.id;details=dict(job.details)
    client=LiveAcefoneClient(credentials['ACEFONE_API_TOKEN'])
    zone=ZoneInfo(worker.settings.source_timezone)
    worker.state('history','SYNCING','Importing selected calendar days',{'job_id':job_id})
    try:
        for _ in range(10):
            day=date.fromisoformat(details['next_date'])
            start=datetime.combine(day,time.min,zone)
            end=min(start+timedelta(days=1),datetime.fromisoformat(details['range_end']).astimezone(zone))
            page=int(details['next_page']);direction=('inbound','outbound')[details['direction_index']]
            if page>worker.settings.max_provider_pages:raise ProviderError('Daily history page limit reached')
            result=client.record_page(start,end-timedelta(seconds=1),page=page,direction=direction)
            rows=result['rows']
            signature=hashlib.sha256(json.dumps([r.get('call_id') for r in rows],separators=(',',':')).encode()).hexdigest()
            if page>1 and rows and signature==details.get('previous_page_signature'):
                raise ProviderError('Provider repeated the previous history page; coverage is incomplete')
            with worker.sessions.begin() as db:
                changed=rejected=0
                for record in rows:
                    try:
                        with db.begin_nested():changed+=store_record(db,record,worker.settings.source_timezone)
                    except (ValueError,TypeError,KeyError):
                        rejected+=1
                        db.add(IntegrationEvent(provider='acefone',status='QUARANTINED',
                            payload=restricted_payload(record),error='Historical record could not be normalized'))
                details['records_seen']+=len(rows);details['changed_calls']+=changed;details['rejected_records']+=rejected
                details['previous_page_signature']=signature
                if result['has_more']:
                    details['next_page']=page+1
                else:
                    details['next_page']=1;details.pop('previous_page_signature',None)
                    details['direction_index']+=1
                    if details['direction_index']==2:
                        details['completed_days']=[*details['completed_days'],str(day)]
                        details['next_date']=str(day+timedelta(days=1));details['direction_index']=0
                done=datetime.combine(date.fromisoformat(details['next_date']),time.min,zone)>=datetime.fromisoformat(details['range_end']).astimezone(zone)
                row=db.get(SyncJob,job_id);row.details=dict(details);row.cursor=f'{details["next_date"]}:{details["direction_index"]}:{details["next_page"]}'
                if done:
                    row.status='PARTIAL' if details['rejected_records'] else 'SUCCEEDED';row.completed_at=now()
                apply_mappings(db)
            if done:
                worker.state('history','PARTIAL' if details['rejected_records'] else 'HEALTHY',
                             'Selected history range imported',{'job_id':job_id,**details})
                break
        return True
    except Exception as exc:
        message=str(exc) if isinstance(exc,ProviderError) else 'Historical import failed; saved progress can be resumed'
        with worker.sessions.begin() as db:
            job=db.get(SyncJob,job_id);job.status='ERROR';job.error=message;job.completed_at=now()
        worker.state('history','ERROR',message,{'job_id':job_id})
        return True
    finally:client.close()
