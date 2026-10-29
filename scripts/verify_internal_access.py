"""Ephemeral Viewer check against the running local app. Never prints customer values."""
import secrets
import sys
from pathlib import Path

import httpx
from sqlalchemy import delete

root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'backend'))
from app.db import LiveTicket,SessionToken,User,database
from app.passwords import hash_password

engine,sessions=database('sqlite:///'+str(root/'.runtime/internal.db'))
username='verification-'+secrets.token_hex(8)
password=secrets.token_urlsafe(32)
with sessions.begin() as db:
    account=User(username=username,display_name='Temporary access verification',role='Viewer',active=True,
                 must_change_password=False,failed_attempts=0,password_hash=hash_password(password))
    db.add(account);db.flush();account_id=account.id
try:
    with httpx.Client(base_url='http://localhost:8001',timeout=30,trust_env=False,follow_redirects=False) as client:
        response=client.post('/api/v1/auth/login',headers={'x-csrf-protection':'1'},
                             json={'username':username,'password':password,'role':'Admin'})
        assert response.status_code==200 and response.json()['role']=='Viewer'
        calls=client.get('/api/v1/calls?page_size=10')
        assert calls.status_code==200
        body=calls.json()
        assert body['synthetic'] is False
        for call in body['items']:
            assert not call['caller'] or call['caller'].startswith('••••')
            assert not call['did'] or call['did'].startswith('••••')
            assert all(lead['display_name']=='Restricted lead' for lead in call['crm']['candidates'])
            for participant in call.get('participants',[]):
                assert not participant.get('agent_number') or participant['agent_number'].startswith('••••')
        if body['items']:
            journey=client.get('/api/v1/calls/'+body['items'][0]['id']+'/journey').json()
            assert all(not e.get('agent_number') or e['agent_number'].startswith('••••') for e in journey['events'])
        for path in ('/api/v1/admin/users','/api/v1/admin/audit','/api/v1/reports/exports'):
            assert client.get(path).status_code==403
        from datetime import date
        assert client.post('/api/v1/history/import',headers={'x-csrf-protection':'1'},
            json={'from_date':str(date.today()),'through_date':str(date.today())}).status_code==403
        print('Live localhost checks passed: named login, role escalation denied, Viewer phone/name masking, admin/audit/export access denied.')
        print('Customer values and passwords were not printed.')
finally:
    with sessions.begin() as db:
        tokens=db.query(SessionToken.token_hash).filter(SessionToken.user_id==account_id).subquery()
        from sqlalchemy import select
        db.execute(delete(LiveTicket).where(LiveTicket.session_hash.in_(select(tokens.c.token_hash))))
        db.execute(delete(SessionToken).where(SessionToken.user_id==account_id))
        db.execute(delete(User).where(User.id==account_id))
    engine.dispose()
    print('Temporary verification account and sessions removed.')
