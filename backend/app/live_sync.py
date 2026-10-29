import threading
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select,delete,func,insert

from .cdr import store_record,restricted_payload
from .credentials import load_credentials
from .crm import enrich, normalize_phone, store_leads
from .db import Call, CRMScanRow, IntegrationEvent, IntegrationState, Lead, LeadPhone, SyncJob, now
from .provider_clients import LiveAcefoneClient, LiveLeadSquaredClient, ProviderError


class CachedCRM:
    def __init__(self, db, available):
        self.db, self.available = db,available

    def lookup(self, phone):
        if not self.available:
            raise ConnectionError('CRM cache is not complete')
        rows = self.db.scalars(select(Lead).join(LeadPhone).where(LeadPhone.normalized_number==phone)).unique().all()
        return [dict(id=l.id,display_name=l.display_name,current_stage=l.current_stage,current_owner=l.current_owner,
                     source=l.source,created_at=l.created_at.replace(tzinfo=UTC).isoformat(),
                     phones=list(self.db.scalars(select(LeadPhone.normalized_number).where(LeadPhone.lead_id==l.id)))) for l in rows]


def normalized_lead(row):
    phones = []
    for key in ('Phone','Mobile'):
        try:
            number = normalize_phone(row.get(key) or '')
            if number not in phones: phones.append(number)
        except ValueError:
            pass
    created = datetime.fromisoformat(row['CreatedOn']).replace(tzinfo=UTC).isoformat()
    return dict(id=row['ProspectID'],display_name=(' '.join(str(row.get(k) or '') for k in ('FirstName','LastName')).strip() or 'Unnamed lead')[:120],
                current_stage=str(row.get('ProspectStage') or 'Unknown')[:80],
                current_owner=str(row.get('OwnerId') or 'Unknown')[:120],source=str(row.get('Source') or 'Unknown')[:120],
                created_at=created,phones=phones)


class LiveSync:
    def __init__(self, settings, sessions):
        self.settings, self.sessions = settings,sessions
        self.lock = threading.Lock()
        self.crm_lock = threading.Lock()
        self.match_lock = threading.Lock()
        self.separate_crm = settings.database_url.startswith(('postgres://','postgresql://','postgresql+'))

    def state(self, provider, status, message=None, details=None):
        with self.sessions.begin() as db:
            row = db.get(IntegrationState, provider)
            if not row:
                row = IntegrationState(provider=provider,status=status,details={})
                db.add(row)
            row.status,row.last_attempt_at,row.message = status,now(),message
            if status in ('HEALTHY','PARTIAL'): row.last_success_at=now()
            if details is not None: row.details=details

    def run(self):
        if not self.lock.acquire(blocking=False):
            return {'status':'ALREADY_RUNNING'}
        try:
            credentials = load_credentials(self.settings.integrations_file)
            if not self.separate_crm:
                from .owner_directory import refresh_owner_directory
                refresh_owner_directory(self.sessions,credentials,client_factory=LiveLeadSquaredClient)
            from .history import process_history
            if process_history(self,credentials):
                with self.sessions() as db:
                    cached=db.get(IntegrationState,'leadsquared')
                    last=cached.last_success_at.replace(tzinfo=UTC) if cached and cached.last_success_at else None
                self.enrich_calls(bool(last),last)
            else:
                self.telephony(credentials)
                if not self.separate_crm:
                    self.crm(credentials)
            from .maintenance import maintain
            maintain(self.settings,self.sessions)
            self.state('system','HEALTHY','Sync and maintenance cycle completed')
            return {'status':'FINISHED'}
        except Exception:
            # Exception messages may include third-party URLs/values. Never surface them.
            self.state('system','ERROR','Sync configuration failed; inspect local setup')
            return {'status':'ERROR'}
        finally:
            self.lock.release()

    def run_crm(self):
        """Cloud CRM indexing must never hold up the next telephony poll."""
        if not self.crm_lock.acquire(blocking=False):
            return {'status':'ALREADY_RUNNING'}
        try:
            credentials=load_credentials(self.settings.integrations_file)
            from .owner_directory import refresh_owner_directory
            refresh_owner_directory(self.sessions,credentials,client_factory=LiveLeadSquaredClient)
            self.crm(credentials)
            return {'status':'FINISHED'}
        except Exception:
            self.state('leadsquared','ERROR','CRM refresh interrupted; retries automatically')
            return {'status':'ERROR'}
        finally:
            self.crm_lock.release()

    def run_matches(self):
        """Resolve recent unmatched callers without waiting for the full CRM scan."""
        if not self.match_lock.acquire(blocking=False):return {'status':'ALREADY_RUNNING'}
        client=None
        try:
            credentials=load_credentials(self.settings.integrations_file)
            client=LiveLeadSquaredClient(credentials)
            from .reports import has_department_flow
            with self.sessions() as db:
                calls=db.scalars(select(Call).where(Call.provider=='acefone').order_by(Call.started_at.desc())).all()
                phones=[]
                for call in calls:
                    crm=call.projection.get('crm',{})
                    checked=crm.get('phone_checked_at')
                    if (call.caller_e164 and has_department_flow(call.projection) and not crm.get('candidates')
                        and call.caller_e164 not in phones
                        and (not checked or now()-datetime.fromisoformat(checked)>timedelta(minutes=15))):
                        phones.append(call.caller_e164)
                    if len(phones)==10:break
            class PhoneLookup:
                def lookup(self,phone):
                    candidates=[normalized_lead(row) for row in client.phone_candidates(phone)]
                    return [lead for lead in candidates if phone in lead['phones']]
            checked=matched=failed=0
            for phone in phones:
                # Fetch outside a DB transaction; network retries must not hold call locks.
                try:candidates=PhoneLookup().lookup(phone)
                except (ProviderError,ValueError):
                    failed+=1
                    continue
                checked+=1
                matched+=bool(candidates)
                with self.sessions.begin() as db:
                    calls=db.scalars(select(Call).where(Call.caller_e164==phone).with_for_update()).all()
                    class SavedLookup:
                        def lookup(self,_):return candidates
                    for call in calls:
                        result=enrich(db,call,SavedLookup(),force=True)
                        call.projection={**call.projection,'crm':{**result,'stale':False,
                            'phone_checked_at':now().isoformat(),'matching_scope':'Default LeadSquared lead type'}}
            self.state('leadsquared-matches','PARTIAL' if failed else 'HEALTHY','Caller phone checks completed',
                {'checked_callers':checked,'matched_callers':matched,'failed_checks':failed})
            return {'status':'FINISHED'}
        except Exception:
            self.state('leadsquared-matches','ERROR','Caller checks interrupted; retrying automatically')
            return {'status':'ERROR'}
        finally:
            if client:client.close()
            self.match_lock.release()

    def telephony(self, credentials):
        self.state('acefone','SYNCING')
        client = LiveAcefoneClient(credentials['ACEFONE_API_TOKEN'])
        with self.sessions.begin() as db:
            job=SyncJob(provider='acefone',kind='reconciliation',status='RUNNING')
            db.add(job); db.flush(); job_id=job.id
            previous=db.scalar(select(SyncJob).where(SyncJob.provider=='acefone',SyncJob.status=='SUCCEEDED')
                                .order_by(SyncJob.completed_at.desc()).limit(1))
            last = previous.completed_at.replace(tzinfo=UTC) if previous else None
        end=now()
        # A daily overlap reconciles late CDR updates; initial history is configurable.
        start=max(end-timedelta(days=self.settings.initial_sync_days), last-timedelta(days=1)) if last else end-timedelta(days=self.settings.initial_sync_days)
        accepted=quarantined=0
        quarantine_reasons={}
        try:
            completed=False
            completed=True
            for direction in ('inbound','outbound'):
                previous_signature=None
                for page in range(1,self.settings.max_provider_pages+1):
                    result=client.record_page(start.astimezone(ZoneInfo(self.settings.source_timezone)),
                        end.astimezone(ZoneInfo(self.settings.source_timezone)),page=page,direction=direction)
                    rows=result['rows']
                    signature=tuple(str(r.get('call_id')) for r in rows)
                    if rows and signature==previous_signature:raise ProviderError('Repeated Acefone page; sync is incomplete')
                    previous_signature=signature
                    with self.sessions.begin() as db:
                        for record in rows:
                            try:
                                with db.begin_nested(): accepted += store_record(db,record,self.settings.source_timezone)
                            except (ValueError,TypeError,KeyError):
                                quarantined+=1
                                reason='unsupported_direction' if record.get('direction') not in ('inbound','outbound') else 'invalid_phone_or_root_identity'
                                quarantine_reasons[reason]=quarantine_reasons.get(reason,0)+1
                                db.add(IntegrationEvent(provider='acefone',status='QUARANTINED',payload=restricted_payload(record),error=reason))
                        db.get(SyncJob,job_id).cursor=f'{direction}:{page}'
                    if not result['has_more']:break
                else:completed=False
            with self.sessions.begin() as db:
                from .mappings import apply_mappings
                apply_mappings(db)
                job=db.get(SyncJob,job_id)
                job.status='SUCCEEDED' if completed and quarantined==0 else 'PARTIAL'
                job.completed_at=now()
                job.details={'range_start':start.isoformat(),'range_end':end.isoformat(),'rows_changed':accepted,
                             'rejected_records':quarantined,'coverage_complete':completed and not quarantined}
                if not completed: job.error='Page limit reached; history is partial'
            self.state('acefone','HEALTHY' if completed and not quarantined else 'PARTIAL',
                       'CDR polling; ring attempts unavailable. Timezone configured as '+self.settings.source_timezone,
                       {'updated_calls':accepted,'quarantined_records':quarantined,'quarantine_reasons':quarantine_reasons,'history_complete':completed,
                        'initial_history_days':self.settings.initial_sync_days})
        except Exception:
            with self.sessions.begin() as db:
                job=db.get(SyncJob,job_id);job.status='ERROR';job.completed_at=now();job.error='Acefone read-only sync failed'
            self.state('acefone','ERROR','CDR sync failed; previous data retained')
        finally: client.close()

    def crm(self, credentials):
        with self.sessions() as db:
            previous=db.get(IntegrationState,'leadsquared')
            last_success=previous.last_success_at.replace(tzinfo=UTC) if previous and previous.last_success_at else None
            details=dict(previous.details or {}) if previous else {}
            recent=bool(last_success and (now()-last_success).total_seconds()<900)
        complete=bool(last_success)
        if not recent:
            from sqlalchemy.dialects.sqlite import insert as sqlite_insert
            from sqlalchemy.dialects.postgresql import insert as pg_insert
            page=int(details.get('next_page') or 1)
            if page==1:
                with self.sessions.begin() as db:db.execute(delete(CRMScanRow))
            self.state('leadsquared','SYNCING','Building complete Phone/Mobile index',details)
            client=LiveLeadSquaredClient(credentials)
            try:
                finished=False
                # Bounded work per cycle. Each page is durable; retries/restarts resume.
                for _ in range(20):
                    if page>self.settings.max_provider_pages:
                        raise ProviderError('CRM scan page limit reached; increase MAX_PROVIDER_PAGES')
                    rows=client.page(page,size=1000)
                    normalized={}
                    for row in rows:
                        lead=normalized_lead(row);normalized[lead['id']]=lead
                    with self.sessions.begin() as db:
                        dialect_insert=sqlite_insert if db.bind.dialect.name=='sqlite' else pg_insert
                        if normalized:
                            statement=dialect_insert(CRMScanRow).values([
                                {'lead_id':key,'payload':value} for key,value in normalized.items()])
                            db.execute(statement.on_conflict_do_update(index_elements=['lead_id'],
                                set_={'payload':statement.excluded.payload}))
                        count=db.scalar(select(func.count()).select_from(CRMScanRow))
                        state=db.get(IntegrationState,'leadsquared')
                        state.details={'next_page':page+1,'pages_read':page,'leads_scanned':count,'scan_complete':False}
                    details={'next_page':page+1,'pages_read':page,'leads_scanned':count,'scan_complete':False}
                    if len(rows)<1000:
                        finished=True;break
                    page+=1
                if finished:
                    self.promote_index()
                    complete=True;last_success=now()
                    self.state('leadsquared','HEALTHY','Current-only CRM snapshot; complete Phone/Mobile scan',
                               {'indexed_leads':count,'complete_scan':True,'historical_snapshots':False})
                else:
                    self.state('leadsquared','INDEXING','Initial/refresh index in progress; resumes automatically',details)
            except Exception as exc:
                message=str(exc) if isinstance(exc,ProviderError) else 'CRM index processing failed ('+type(exc).__name__+'); prior data retained'
                self.state('leadsquared','ERROR',message,details)
            finally:client.close()
        self.enrich_calls(complete,last_success)

    def enrich_calls(self,complete,last_success):
        with self.sessions() as db:
            call_ids=list(db.scalars(select(Call.id).where(Call.provider=='acefone')))
        for call_id in call_ids:
            # Keep locks short so CRM projection writes cannot overwrite newer CDR data.
            with self.sessions.begin() as db:
                call=db.scalar(select(Call).where(Call.id==call_id).with_for_update())
                if call is None: continue
                state=db.get(IntegrationState,'leadsquared')
                previous=call.projection.get('crm',{})
                if previous.get('phone_checked_at') and (not last_success or datetime.fromisoformat(previous['phone_checked_at'])>last_success):
                    continue  # A direct phone check is newer than the completed index.
                stale=bool(state and state.status!='HEALTHY')
                if (complete and previous.get('synced_at')==last_success.isoformat() and previous.get('stale')==stale
                    and previous.get('status') not in ('PENDING','ERROR')
                    and not(previous.get('status')=='INVALID_PHONE' and call.caller_e164)):
                    continue
                if not complete:
                    call.projection={**call.projection,'crm':{'status':'PENDING','candidates':[],
                        'snapshot_source':'current only','error':'CRM index is not complete yet; no unique match inferred',
                        'synced_at':None,'attempts':0,'next_retry_at':None}}
                else:
                    result=enrich(db,call,CachedCRM(db,True),force=True)
                    result={**result,'synced_at':last_success.isoformat() if last_success else None,
                            'stale':bool(state and state.status!='HEALTHY'),
                            'matching_scope':'Default LeadSquared lead type; custom object types are not verified'}
                    call.projection={**call.projection,'crm':result}

    def promote_index(self):
        from sqlalchemy.dialects.sqlite import insert as sqlite_insert
        from sqlalchemy.dialects.postgresql import insert as pg_insert
        with self.sessions.begin() as db:
            dialect_insert=sqlite_insert if db.bind.dialect.name=='sqlite' else pg_insert
            db.execute(delete(LeadPhone))
            offset=0
            while True:
                batch=db.scalars(select(CRMScanRow).order_by(CRMScanRow.lead_id).offset(offset).limit(1000)).all()
                if not batch:break
                values=[];phones=[]
                for row in batch:
                    lead=row.payload
                    values.append({**{k:lead[k] for k in ('id','display_name','current_stage','current_owner','source')},
                                   'created_at':datetime.fromisoformat(lead['created_at']),'last_synced_at':now()})
                    phones.extend({'lead_id':lead['id'],'normalized_number':phone} for phone in lead['phones'])
                statement=dialect_insert(Lead).values(values)
                db.execute(statement.on_conflict_do_update(index_elements=['id'],set_={
                    key:getattr(statement.excluded,key) for key in values[0] if key!='id'}))
                if phones:db.execute(insert(LeadPhone),phones)
                offset+=len(batch)
            # Keep the completed staging generation until the next scan starts;
            # a crash between promotion and health update can safely re-promote it.
