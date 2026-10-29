from app.db import AuditLog
from test_api import seeded


def test_calls_page_size_and_all_keep_totals_and_masking(client):
    seeded(client,'Viewer')
    small=client.get('/api/v1/calls?page_size=1').json()
    assert len(small['items'])==1 and small['next_page']==2
    all_rows=client.get('/api/v1/calls?page_size=1&show_all=true').json()
    assert len(all_rows['items'])==all_rows['total']==9 and all_rows['next_page'] is None
    assert all(not c['caller'] or c['caller'].startswith('••••') for c in all_rows['items'])
    selected=client.get('/api/v1/calls?missed_department=true&page_size=1&show_all=true').json()
    assert len(selected['items'])==selected['total'] and selected['next_page'] is None


def test_ls_all_returns_every_caller_without_changing_summary(client):
    seeded(client)
    small=client.get('/api/v1/reports/leadsquared?page_size=1').json()
    all_rows=client.get('/api/v1/reports/leadsquared?page_size=1&show_all=true').json()
    assert len(small['items'])==1
    assert len(all_rows['items'])==all_rows['total'] and all_rows['next_page'] is None
    assert all_rows['summary']==small['summary']


def test_audit_sizes_and_all_remain_admin_only(client):
    seeded(client,'Admin')
    with client.app.state.sessions.begin() as db:
        for i in range(37):db.add(AuditLog(role='Admin',action='fixture',resource=str(i)))
    small=client.get('/api/v1/admin/audit?page_size=10').json()
    assert len(small['items'])==10 and small['next_page']==2
    all_rows=client.get('/api/v1/admin/audit?page_size=10&show_all=true').json()
    assert len(all_rows['items'])==all_rows['total'] and all_rows['next_page'] is None
