"""Isolated internal-mode browser fixture. Never loads integration credentials."""
import os
import subprocess
import sys
from pathlib import Path

root=Path(__file__).resolve().parents[1]
os.chdir(root);os.umask(0o077)
path=root/'.runtime/browser-fixture.db'
os.environ.update(APP_MODE='internal',AUTO_SYNC='false',APP_ORIGIN='http://localhost:8002',
                  DATABASE_URL='sqlite:///'+str(path),STATIC_DIRECTORY=str(root/'frontend/dist'),PYTHONPATH=str(root/'backend'))
sys.path.insert(0,str(root/'backend'))
subprocess.run([sys.executable,'-m','alembic','-c','backend/alembic.ini','upgrade','head'],check=True)
from app.db import database,User,Call,IntegrationState
from app.crm import enrich
from types import SimpleNamespace
from app.passwords import hash_password
from app.cdr import store_record
from datetime import datetime,timedelta,UTC
from zoneinfo import ZoneInfo
from sqlalchemy import select
engine,sessions=database(os.environ['DATABASE_URL'])
with sessions.begin() as db:
    account=db.scalar(select(User).where(User.username=='browseradmin'))
    if not account:
        account=User(username='browseradmin',display_name='Browser Test Admin',role='Admin',active=True,failed_attempts=0)
        db.add(account)
    account.password_hash=hash_password('fixture-temporary-password');account.must_change_password=True
    day=datetime.now(ZoneInfo('Asia/Kolkata')).replace(hour=10,minute=0,second=0,microsecond=0)-timedelta(days=1)
    stamp=int(day.timestamp())
    for outcome,phone,index in [('answered','+12025550110',0),('missed','+12025550111',1)]:
        start=stamp+index*600
        flow=[{'type':'init','time':start},{'type':'Department','name':'Admissions','time':start+2},
              {'type':'Agent','id':'fixture-agent-1','name':'First Fixture Agent','num':'+12025550120','dialst':'Dialed','time':start+5}]
        if outcome=='answered':
            flow.extend([{'type':'Agent','id':'fixture-agent-2','name':'Final Fixture Agent','num':'+12025550121','dialst':'Dialed','time':start+20},
                         {'type':'Agent','id':'fixture-agent-2','name':'Final Fixture Agent','number':'+12025550121','dialst':'Answered','time':start+25}])
        flow.append({'type':'hangup','time':start+90})
        store_record(db,{'call_id':'fixture-'+outcome,'direction':'inbound','client_number':phone,'did_number':'+12025550199',
            'status':outcome,'date':day.date().isoformat(),'time':datetime.fromtimestamp(start,ZoneInfo('Asia/Kolkata')).strftime('%H:%M:%S'),
            'call_duration':90,'agent_name':'Final Fixture Agent' if outcome=='answered' else None,'call_flow':flow,
            'missed_agents':[{'name':'First Fixture Agent','number':'+12025550120'}]})
    answered_call=db.scalar(select(Call).where(Call.provider_call_id=='fixture-answered'))
    enrich(db,answered_call,SimpleNamespace(lookup=lambda phone:[{
        'id':'fixture-lead','display_name':'Fixture Existing Lead','created_at':'2026-01-01T00:00:00Z',
        'current_stage':'Qualified','current_owner':'11111111-2222-3333-4444-555555555555','source':'Synthetic browser fixture',
        'phones':['+12025550110']}]),force=True)
    db.merge(IntegrationState(provider='leadsquared-users',status='HEALTHY',details={'owners':{'11111111-2222-3333-4444-555555555555':'Fixture Owner'}}))
    store_record(db,{'call_id':'fixture-ivr-exit','direction':'inbound','client_number':'+12025550112','did_number':'+12025550199',
        'status':'missed','date':day.date().isoformat(),'time':day.strftime('%H:%M:%S'),'call_duration':30,
        'call_flow':[{'type':'init','time':stamp},{'type':'IVR','name':'Fixture menu','time':stamp+2},{'type':'hangup','time':stamp+30}],
        'missed_agents':[]})
engine.dispose()
os.execv(sys.executable,[sys.executable,'-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8002','--no-access-log'])
