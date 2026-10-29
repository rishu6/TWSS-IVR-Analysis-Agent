"""Queue a bounded historical import locally; the running service performs provider reads."""
import argparse
import sys
from datetime import UTC,date,datetime,time,timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'backend'))
from sqlalchemy import select
from app.db import AuditLog,SyncJob,database,now

parser=argparse.ArgumentParser()
parser.add_argument('--from-date',type=date.fromisoformat)
parser.add_argument('--through-date',type=date.fromisoformat)
args=parser.parse_args()
zone=ZoneInfo('Asia/Kolkata');today=datetime.now(zone).date()
start_day=args.from_date or today-timedelta(days=29)
end_day=args.through_date or today
if not today-timedelta(days=89)<=start_day<=end_day<=today:raise SystemExit('Choose an ordered range within the last 90 days')
start=datetime.combine(start_day,time.min,zone)
end=min(datetime.combine(end_day+timedelta(days=1),time.min,zone),now().astimezone(zone))
engine,sessions=database('sqlite:///'+str(root/'.runtime/internal.db'))
with sessions.begin() as db:
    existing=next((j for j in db.scalars(select(SyncJob).where(SyncJob.provider=='acefone',SyncJob.kind=='history',
        SyncJob.status.in_(['QUEUED','RUNNING']))) if j.details.get('from_date')==str(start_day)
            and j.details.get('through_date')==str(end_day)),None)
    if existing:print('Matching import is already queued/running:',existing.id)
    else:
        job=SyncJob(provider='acefone',kind='history',status='QUEUED',details={
            'from_date':str(start_day),'through_date':str(end_day),
            'range_start':start.astimezone(UTC).isoformat(),'range_end':end.astimezone(UTC).isoformat(),
            'next_date':str(start_day),'direction_index':0,'next_page':1,'records_seen':0,
            'changed_calls':0,'rejected_records':0,'completed_days':[]})
        db.add(job);db.flush();db.add(AuditLog(role='Admin',action='history_import_requested_locally',resource=str(job.id)))
        print('Queued calendar-day history import:',job.id,str(start_day),'through',str(end_day))
engine.dispose()
