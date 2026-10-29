import io

from sqlalchemy import select

from app.db import AuditLog
from app.seed import seed
from conftest import login


def seeded(client, role='Manager'):
    seed(client.app.state.sessions)
    login(client, role)
    return client


def test_dashboard_counts_logical_inbound_calls(client):
    c = seeded(client)
    result = c.get('/api/v1/metrics/overview').json()
    assert result['total'] == 8  # outbound callback excluded
    assert result['ANSWERED'] == 3
    assert result['MISSED'] == 1
    assert result['IVR_ONLY'] == 1
    assert result['ABANDONED'] == 1
    assert result['IN_PROGRESS'] == 1
    assert result['UNKNOWN'] == 1
    assert result['answer_rate'] == 3/8
    assert result['hourly'][0]['at'] == '2026-10-27T04:30:00+00:00'  # 10:00 IST hour boundary
    assert result['hourly'][0]['total'] == 5


def test_filters_pagination_and_crm_matches(client):
    c = seeded(client)
    page = c.get('/api/v1/calls?page_size=2').json()
    assert page['total'] == 9 and len(page['items']) == 2 and page['next_page'] == 2
    assert 'events' not in page['items'][0]
    filtered = c.get('/api/v1/calls?agent=Dev%20Patel&department=Sales').json()
    assert {r['id'] for r in filtered['items']} == {'demo-four-agents', 'demo-transfer'}
    assert c.get('/api/v1/calls?stage=Contacted').json()['total'] == 2
    assert c.get('/api/v1/calls?owner=Rohan%20Das').json()['total'] == 2  # outage call not yet enriched
    assert c.get('/api/v1/calls?start=2026-10-27T04:30:00Z&end=2026-10-27T04:31:00Z').json()['total'] == 1
    assert c.get('/api/v1/calls?outcome=BAD').status_code == 422
    assert c.get('/api/v1/calls?page_size=1000').status_code == 422
    crm = c.get('/api/v1/calls/demo-missed/crm').json()
    assert crm['status'] == 'MULTIPLE_MATCHES' and len(crm['candidates']) == 2


def test_I_viewer_cannot_access_numbers_recordings_secrets_or_admin(client):
    c = seeded(client, 'Viewer')
    for path in ['/api/v1/admin', '/api/v1/admin/raw-events', '/api/v1/calls/demo-four-agents/recording',
                 '/api/v1/reports/exports']:
        assert c.get(path).status_code == 403
    for path in ['/api/v1/calls', '/api/v1/calls/demo-four-agents/journey', '/api/v1/metrics/overview',
                 '/api/v1/reports/missed-calls', '/api/v1/calls/demo-missed/crm']:
        response = c.get(path)
        assert response.status_code == 200
        assert '+1202555' not in response.text
        assert 'synthetic-demo-only' not in response.text
        assert 'Avery Morgan' not in response.text


def test_exports_filtered_audited_and_formula_safe(client):
    c = seeded(client)
    response = c.get('/api/v1/reports/exports?q=four-agents')
    assert response.status_code == 200
    assert len(response.text.splitlines()) == 2
    assert "'+12025550101" in response.text
    from openpyxl import load_workbook
    xlsx = c.get('/api/v1/reports/exports?format=xlsx&q=four-agents')
    book = load_workbook(io.BytesIO(xlsx.content), read_only=True)
    rows = list(book.active.values)
    assert len(rows) == 2
    assert rows[1][0] == 'demo-four-agents'
    with c.app.state.sessions() as db:
        assert len(db.scalars(select(AuditLog).where(AuditLog.action.like('export_%'))).all()) == 2


def test_recording_absence_and_live_webhook_disabled(client):
    c = seeded(client, 'Admin')
    assert c.get('/api/v1/calls/demo-four-agents/recording').status_code == 404
    assert c.post('/api/v1/webhooks/acefone', headers={'x-csrf-protection': '1'}).status_code == 503


def test_live_token_is_single_use_and_not_in_url(client):
    c = seeded(client)
    token = c.post('/api/v1/live-token', headers={'x-csrf-protection': '1'}).json()['token']
    with c.websocket_connect('/api/v1/live') as socket:
        socket.send_text(token)
        assert socket.receive_json() == {'type': 'invalidate', 'synthetic': True}
    with c.websocket_connect('/api/v1/live') as socket:
        socket.send_text(token)
        message = socket.receive()
        assert message['type'] == 'websocket.close' and message['code'] == 4401


def test_crm_recovery_is_explicitly_simulated(client):
    c = seeded(client)
    assert c.get('/api/v1/calls/demo-no-ring-data/crm').json()['status'] == 'ERROR'
    assert c.post('/api/v1/demo/retry-crm', headers={'x-csrf-protection': '1'}).json()['synthetic']
    assert c.get('/api/v1/calls/demo-no-ring-data/crm').json()['status'] == 'MATCHED'
