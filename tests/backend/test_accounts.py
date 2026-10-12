from datetime import timedelta, datetime, timezone

import jwt
from sqlalchemy import func, insert, select, update
from sqlalchemy.exc import OperationalError

from backend.main import create_app
from backend.models.tables import audit_logs, competitions, teams, users
from backend.security import verify_password
from fastapi.testclient import TestClient


def credentials(name="team01"):
    return {"username": name, "password": "team-test-password"}


def test_health_and_default_closed(client):
    assert client.get("/api/health").json()["schema"] == "0001_initial"
    state = client.get("/api/competition").json()
    assert state["team_count"] == 0 and not state["registration_available"]
    assert client.post("/api/teams", json=credentials()).status_code == 409


def test_open_register_login_close(client, engine, admin_headers):
    assert client.put("/api/admin/registration", json={"open": True}, headers=admin_headers).status_code == 200
    result = client.post("/api/teams", json=credentials(" TEAM01 "))
    assert result.status_code == 201
    assert result.json()["team"]["name"] == "team01"
    assert "password" not in result.text
    with engine.connect() as connection:
        user = connection.execute(select(users).where(users.c.username == "team01")).mappings().one()
        assert user["password_hash"] != credentials()["password"]
        assert verify_password(credentials()["password"], user["password_hash"])
    login = client.post("/api/auth/login", json=credentials())
    assert login.status_code == 200
    headers = {"Authorization": "Bearer " + login.json()["access_token"]}
    assert client.get("/api/auth/me", headers=headers).json()["account_type"] == "TEAM"
    assert client.get("/api/teams/me", headers=headers).json()["name"] == "team01"
    assert client.put("/api/admin/registration", json={"open": False}, headers=headers).status_code == 403
    assert client.put("/api/admin/registration", json={"open": False}, headers=admin_headers).status_code == 200
    assert client.post("/api/teams", json=credentials("team02")).status_code == 409
    with engine.connect() as connection:
        actions = connection.scalars(select(audit_logs.c.action)).all()
        assert actions == ["REGISTRATION_OPENED", "TEAM_REGISTERED", "REGISTRATION_CLOSED"]


def test_duplicate_registration_rolls_back(client, engine, opened):
    assert client.post("/api/teams", json=credentials()).status_code == 201
    assert client.post("/api/teams", json=credentials("TEAM01")).status_code == 409
    with engine.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(teams)) == 1
        assert connection.scalar(select(func.count()).select_from(users)) == 2


def test_capacity_six_and_no_orphan_account(client, engine, opened):
    for n in range(6):
        assert client.post("/api/teams", json=credentials(f"team{n:02}")).status_code == 201
    assert client.post("/api/teams", json=credentials("team07")).status_code == 409
    with engine.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(teams)) == 6
        assert connection.scalar(select(func.count()).select_from(users)) == 7
    assert not client.get("/api/competition").json()["registration_available"]


def test_protected_endpoints_and_bad_login(client):
    assert client.put("/api/admin/registration", json={"open": True}).status_code == 401
    for path in ["/api/auth/me", "/api/teams/me"]:
        assert client.get(path, headers={"Authorization": "Bearer not-a-token"}).status_code == 401
    for name, password in [("admin", "wrong-password"), ("unknown", "wrong-password")]:
        assert client.post("/api/auth/login", json={"username": name, "password": password}).status_code == 401


def test_inactive_and_changed_role_checked_on_each_request(client, engine, admin_headers):
    with engine.begin() as connection:
        connection.execute(update(users).where(users.c.username == "admin").values(account_type="TEAM"))
    assert client.put("/api/admin/registration", json={"open": True}, headers=admin_headers).status_code == 403
    with engine.begin() as connection:
        connection.execute(update(users).where(users.c.username == "admin").values(active=False))
    assert client.get("/api/auth/me", headers=admin_headers).status_code == 401
    assert client.post("/api/auth/login", json={"username": "admin", "password": "admin-test-password"}).status_code == 401


def test_expired_token(client, settings):
    now = datetime.now(timezone.utc)
    token = jwt.encode({"sub": "1", "iat": now-timedelta(hours=2), "exp": now-timedelta(hours=1),
                        "iss": "bt3-backend", "aud": "bt3-api"}, settings.jwt_secret.get_secret_value(), algorithm="HS256")
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer " + token}).status_code == 401


def test_registration_dates_and_later_phases(client, engine, admin_headers, opened):
    with engine.begin() as connection:
        connection.execute(update(competitions).values(registration_closes_at=datetime(2000, 1, 1)))
    assert client.post("/api/teams", json=credentials()).status_code == 409
    assert not client.get("/api/competition").json()["registration_available"]
    with engine.begin() as connection:
        connection.execute(update(competitions).values(status="CODING", registration_open=False))
    assert client.put("/api/admin/registration", json={"open": True}, headers=admin_headers).status_code == 409


def test_validation_cannot_assign_admin_or_echo_password(client, opened):
    assert client.post("/api/teams", json={**credentials(), "account_type": "ADMIN"}).status_code == 422
    response = client.post("/api/teams", json={"username": "team01", "password": "x7!"})
    assert response.status_code == 422 and "x7!" not in response.text
    assert client.post("/api/teams", json=credentials("bad name")).status_code == 422


def test_missing_competition(client, engine):
    with engine.begin() as connection:
        connection.execute(update(competitions).values(code="other"))
    assert client.get("/api/competition").status_code == 404


def test_database_error_is_sanitized(settings):
    class BrokenEngine:
        def connect(self):
            raise OperationalError("SELECT", {}, Exception("secret-database-password"))
    with TestClient(create_app(settings, BrokenEngine())) as client:
        response = client.get("/api/health")
        assert response.status_code == 503
        assert "secret-database-password" not in response.text


def test_simple_registration_cannot_bypass_main_student_rules(client, engine, opened):
    with engine.begin() as connection:
        connection.execute(update(competitions).values(mode="MAIN"))
    assert client.post("/api/teams", json=credentials()).status_code == 409


def test_team_insert_failure_rolls_back_new_user(client, engine, opened):
    with engine.begin() as connection:
        competition_id = connection.scalar(select(competitions.c.id))
        admin_id = connection.scalar(select(users.c.id).where(users.c.username == "admin"))
        connection.execute(insert(teams).values(competition_id=competition_id,
            name="team01", owner_user_id=admin_id, status="REGISTERED"))
    assert client.post("/api/teams", json=credentials()).status_code == 409
    with engine.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(users)) == 1
        assert connection.scalar(select(func.count()).select_from(teams)) == 1


def test_admin_remove_frees_name_capacity_and_revokes_token(client, engine, admin_headers, opened):
    registered = client.post("/api/teams", json=credentials()).json()
    team_id = registered["team"]["id"]
    token = client.post("/api/auth/login", json=credentials()).json()["access_token"]
    headers = {"Authorization": "Bearer " + token}
    assert client.delete(f"/api/admin/teams/{team_id}", headers=headers).status_code == 403
    assert client.delete(f"/api/admin/teams/{team_id}").status_code == 401
    assert client.delete(f"/api/admin/teams/{team_id}", headers=admin_headers).status_code == 200
    assert client.get("/api/teams").json() == []
    assert client.get("/api/competition").json()["team_count"] == 0
    assert client.get("/api/auth/me", headers=headers).status_code == 401
    assert client.post("/api/auth/login", json=credentials()).status_code == 401
    new = client.post("/api/teams", json=credentials())
    assert new.status_code == 201 and new.json()["team"]["id"] != team_id
    with engine.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(teams)) == 2
        assert "DEMO_TEAM_REMOVED" in connection.scalars(select(audit_logs.c.action)).all()


def test_remove_blocks_main_late_phase_and_unknown_team(client, engine, admin_headers, opened):
    team_id = client.post("/api/teams", json=credentials()).json()["team"]["id"]
    assert client.delete("/api/admin/teams/999", headers=admin_headers).status_code == 404
    with engine.begin() as connection:
        connection.execute(update(competitions).values(mode="MAIN"))
    assert client.delete(f"/api/admin/teams/{team_id}", headers=admin_headers).status_code == 409
    with engine.begin() as connection:
        connection.execute(update(competitions).values(mode="DEMO", status="CODING"))
    assert client.delete(f"/api/admin/teams/{team_id}", headers=admin_headers).status_code == 409
    assert len(client.get("/api/teams").json()) == 1
