import importlib.util
from datetime import UTC,datetime,timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from app.config import Settings
from app.credentials import load_credentials
from app.db import Base,User,SessionToken,database
from app.main import create_app

spec=importlib.util.spec_from_file_location('cloud_start',Path('scripts/cloud.py'))
cloud=importlib.util.module_from_spec(spec);spec.loader.exec_module(cloud)


def test_render_configuration_keeps_storage_and_https(tmp_path):
    env={'RENDER_EXTERNAL_URL':'https://twss-ivr.onrender.com','RUNTIME_DIRECTORY':str(tmp_path),'PORT':'10000','MIGRATION_PENDING':'true','AUTO_SYNC':'true','DATABASE_URL':'postgresql://fixture:password@db.example/neondb?sslmode=require'}
    runtime,port=cloud.configure(env)
    assert runtime==tmp_path and port==10000
    assert env['DATABASE_URL']=='postgresql+psycopg://fixture:password@db.example/neondb?sslmode=require'
    assert env['APP_MODE']=='internal' and env['SECURE_COOKIES']=='true' and env['AUTO_SYNC']=='false'
    assert env['APP_ORIGIN']=='https://twss-ivr.onrender.com'
    with pytest.raises(ValueError):cloud.configure({'RENDER_EXTERNAL_URL':'http://twss-ivr.onrender.com'})
    with pytest.raises(ValueError):cloud.configure({'APP_ORIGIN':'https://user:password@site.example'})


def test_provider_environment_credentials_without_file(tmp_path,monkeypatch):
    values={'ACEFONE_API_TOKEN':'fixture-token','LEADSQUARED_API_HOST':'https://api-in21.leadsquared.com','LEADSQUARED_ACCESS_KEY':'fixture-access','LEADSQUARED_SECRET_KEY':'fixture-secret'}
    for key,value in values.items():monkeypatch.setenv(key,value)
    assert load_credentials(tmp_path/'absent.env')==values


def test_migration_gate_and_health_are_available_without_login(tmp_path):
    settings=Settings(mode='internal',database_url='sqlite:///'+str(tmp_path/'internal.db'),origin='https://twss-ivr.onrender.com',secure_cookies=True,auto_sync=False,migration_pending=True)
    app=create_app(settings);Base.metadata.create_all(app.state.engine)
    with TestClient(app) as client:
        assert client.get('/healthz').json()=={'status':'ok'}
        assert client.get('/api/v1/auth/configuration').status_code==503
        assert client.get('/api/v1/calls').status_code==503

