import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.db import Base
from app.main import create_app


@pytest.fixture
def client(tmp_path):
    app = create_app(Settings(database_url=f'sqlite:///{tmp_path}/test.db'))
    Base.metadata.create_all(app.state.engine)
    with TestClient(app) as client:
        yield client
    app.state.engine.dispose()


def login(client, role='Manager'):
    return client.post('/api/v1/auth/login', json={'role': role, 'password': 'synthetic-demo-only'},
                       headers={'x-csrf-protection': '1'})
