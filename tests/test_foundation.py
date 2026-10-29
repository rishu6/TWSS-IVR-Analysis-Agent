import pytest
from sqlalchemy import inspect
from alembic import command
from alembic.config import Config

from app.config import Settings
from app.db import database
from app.main import create_app
from conftest import login


def test_demo_cannot_be_enabled_as_live():
    with pytest.raises(RuntimeError, match='Live mode disabled'):
        create_app(Settings(mode='live'))


def test_auth_csrf_and_roles(client):
    assert client.get('/api/v1/integrations/health').status_code == 401
    assert client.post('/api/v1/auth/login', json={'role': 'Admin', 'password': 'x'}).status_code == 403
    assert login(client, 'Viewer').status_code == 200
    assert client.get('/api/v1/admin').status_code == 403
    assert client.get('/api/v1/integrations/health').json()['live_verified'] is False
    assert 'httponly' in str(client.cookies).lower() or client.cookies.get('session')
    assert login(client, 'Admin').status_code == 200
    assert 'password' not in client.get('/api/v1/admin').text


def test_migration_upgrade_downgrade(tmp_path, monkeypatch):
    url = f'sqlite:///{tmp_path}/migration.db'
    monkeypatch.setenv('DATABASE_URL', url)
    config = Config('backend/alembic.ini')
    command.upgrade(config, 'head')
    engine, _ = database(url)
    assert {'calls', 'call_events', 'leads', 'sessions', 'audit_logs'} <= set(inspect(engine).get_table_names())
    command.check(config)  # Ensure migration and ORM schema agree.
    command.downgrade(config, 'base')
    assert 'calls' not in inspect(engine).get_table_names()
    engine.dispose()
