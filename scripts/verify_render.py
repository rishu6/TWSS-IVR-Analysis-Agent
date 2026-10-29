"""Ephemeral Viewer checks against the live app; never prints customer values."""
import json
import secrets
import sys
from pathlib import Path
from sqlalchemy import select,delete
import httpx

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.credentials import read_env
from app.db import database,User,SessionToken,LiveTicket
from app.passwords import hash_password


def verify():
    values=read_env(ROOT/'.env.render')
    url=values['DATABASE_URL']
    if url.startswith('postgresql://'):url=url.replace('postgresql://','postgresql+psycopg://',1)
    if url.startswith('postgres://'):url=url.replace('postgres://','postgresql+psycopg://',1)
    state=json.loads((ROOT/'.runtime/render/deployment.json').read_text())
    engine,sessions=database(url)
    username='verify-'+secrets.token_hex(8);password=secrets.token_urlsafe(32);account_id=None
    try:
        with sessions.begin() as db:
            account=User(username=username,display_name='Temporary cloud verification',role='Viewer',active=True,
                must_change_password=False,failed_attempts=0,password_hash=hash_password(password))
            db.add(account);db.flush();account_id=account.id
        with httpx.Client(base_url=state['url'],timeout=60,trust_env=False) as client:
            response=client.get('/healthz');assert response.status_code==200
            response=client.post('/api/v1/auth/login',headers={'x-csrf-protection':'1'},
                json={'username':username,'password':password,'role':'Admin'})
            assert response.status_code==200 and response.json()['role']=='Viewer'
            cookie=response.headers.get('set-cookie','').lower()
            assert 'secure' in cookie and 'httponly' in cookie
            response=client.get('/api/v1/calls?page_size=1')
            assert response.status_code==200
            for call in response.json()['items']:
                assert not call['caller'] or call['caller'].startswith('••••')
                assert not call['did'] or call['did'].startswith('••••')
            response=client.get('/api/v1/reports/leadsquared?page_size=1')
            assert response.status_code==200
            for row in response.json()['items']:
                assert not row['caller'] or row['caller'].startswith('••••')
                assert all(lead['display_name']=='Restricted lead' for lead in row['candidates'])
            overview=client.get('/api/v1/metrics/overview')
            assert overview.status_code==200
            metric=overview.json()
            assert 0<=metric['unique_callers']<=metric['total']
            assert 0<=metric['department_answered']<=metric['department_calls']<=metric['total']
            expected=metric['department_answered']/metric['department_calls'] if metric['department_calls'] else None
            assert metric['answer_rate']==expected
            assert metric['customer_missed']+metric['missed_without_department']==metric['MISSED']
            departments=client.get('/api/v1/reports/departments')
            assert departments.status_code==200
            assert all(0<=row['missed_primary']<=row['primary_calls'] for row in departments.json()['items'])
            print({'live_dashboard_metrics':'passed'})
            health=client.get('/api/v1/integrations/health')
            assert health.status_code==200
            print({'provider_states':{key:health.json().get(key) for key in ('acefone','leadsquared','system')}})
            for path in ['/api/v1/admin/users','/api/v1/admin/audit','/api/v1/reports/exports']:
                assert client.get(path).status_code==403
            assert client.post('/api/v1/history/import',headers={'x-csrf-protection':'1'},
                json={'from_date':'2026-10-01','through_date':'2026-10-01'}).status_code==403
            print({'live_checks':'passed','https':True,'named_login':True,'viewer_masking':True,'admin_access_denied':True})
    finally:
        if account_id:
            with sessions.begin() as db:
                tokens=select(SessionToken.token_hash).where(SessionToken.user_id==account_id)
                db.execute(delete(LiveTicket).where(LiveTicket.session_hash.in_(tokens)))
                db.execute(delete(SessionToken).where(SessionToken.user_id==account_id))
                db.execute(delete(User).where(User.id==account_id))
        engine.dispose()


if __name__=='__main__':
    try:verify()
    except Exception as exc:
        print({'live_checks':'failed','error_type':type(exc).__name__});raise SystemExit(1)
