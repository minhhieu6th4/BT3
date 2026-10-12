import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, insert, event
from sqlalchemy.pool import StaticPool

from backend.config import Settings
from backend.main import create_app
from backend.models.tables import competitions, metadata, schema_migrations, users
from backend.security import hash_password


@pytest.fixture
def engine():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    @event.listens_for(engine, "connect")
    def foreign_keys(connection, _record):
        connection.execute("PRAGMA foreign_keys=ON")
    metadata.create_all(engine)
    with engine.begin() as connection:
        connection.execute(insert(schema_migrations).values(version="0001_initial"))
        connection.execute(insert(competitions).values(code="demo", name="Demo", mode="DEMO",
            status="DRAFT", max_teams=6, format_config={}))
        connection.execute(insert(users).values(username="admin", password_hash=hash_password("admin-test-password"),
            account_type="ADMIN", active=True))
    yield engine
    engine.dispose()


@pytest.fixture
def settings():
    return Settings(_env_file=None, jwt_secret="test-only-secret-" * 4)


@pytest.fixture
def client(engine, settings):
    with TestClient(create_app(settings, engine)) as client:
        yield client


@pytest.fixture
def admin_headers(client):
    response = client.post("/api/auth/login", json={"username": "admin", "password": "admin-test-password"})
    assert response.status_code == 200
    return {"Authorization": "Bearer " + response.json()["access_token"]}


@pytest.fixture
def opened(client, admin_headers):
    assert client.put("/api/admin/registration", json={"open": True}, headers=admin_headers).status_code == 200
