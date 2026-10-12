from datetime import datetime, timedelta, timezone
import hashlib
import pytest
from sqlalchemy import select, func, event
from sqlalchemy.exc import OperationalError
from backend.models.tables import submissions, competitions
from backend.services.windows import is_open

BOT = b"class Bot:\n    def get_move(self, state):\n        return {}\n"


@pytest.fixture
def team_headers(client, opened):
    assert client.post("/api/teams", json={"username":"submitteam", "password":"test-only-password"}).status_code == 201
    token = client.post("/api/auth/login", json={"username":"submitteam", "password":"test-only-password"}).json()["access_token"]
    return {"Authorization":"Bearer " + token}


def send(client, headers, content=BOT, name="student_bot.py"):
    return client.post("/api/submissions", files={"file":(name, content, "text/x-python")}, headers=headers)


def test_upload_versions_private_files_and_history(client, team_headers, admin_headers, engine, settings):
    assert send(client, team_headers).status_code == 409
    client.put("/api/admin/registration", json={"open":False}, headers=admin_headers)
    assert client.put("/api/admin/submission", json={"open":True}, headers=admin_headers).status_code == 200
    for version in [1,2]:
        response = send(client, team_headers)
        assert response.status_code == 201
        assert response.json()["version"] == version
        assert response.json()["validation_status"] == "PENDING"
        assert "source_file_path" not in response.text
    history = client.get("/api/submissions/me", headers=team_headers).json()
    assert [r["version"] for r in history] == [2,1]
    with engine.connect() as connection:
        rows = connection.execute(select(submissions)).mappings().all()
        for row in rows:
            assert (settings.submission_dir / row["source_file_path"]).read_bytes() == BOT
            assert row["source_sha256"] == hashlib.sha256(BOT).hexdigest()
    assert client.put("/api/admin/submission", json={"open":False}, headers=admin_headers).status_code == 200
    assert send(client, team_headers).status_code == 409
    assert len(client.get("/api/submissions/me", headers=team_headers).json()) == 2


def test_upload_auth_validation_limits(client, team_headers, admin_headers, settings):
    client.put("/api/admin/registration", json={"open":False}, headers=admin_headers)
    client.put("/api/admin/submission", json={"open":True}, headers=admin_headers)
    assert send(client, {}).status_code == 401
    assert send(client, admin_headers).status_code == 403
    assert client.get("/api/submissions/me", headers=admin_headers).status_code == 403
    for name, content in [("bot.py", BOT),("../student_bot.py",BOT),("student_bot.py",b""),("student_bot.py",b"\xff"),("student_bot.py",b"\0")]:
        assert send(client, team_headers, content, name).status_code == 422
    assert client.post("/api/submissions", files=[("file",("student_bot.py", BOT)),("file",("student_bot.py",BOT))],headers=team_headers).status_code == 422
    settings.max_submission_bytes = 4
    assert send(client, team_headers).status_code == 413
    assert not settings.submission_dir.exists()


def test_request_body_limit(client, team_headers):
    assert send(client, team_headers, b"x" * (1048576+65537)).status_code == 413


def test_upload_rolls_back_file_on_database_failure(client, team_headers, admin_headers, engine, settings):
    client.put("/api/admin/registration", json={"open":False}, headers=admin_headers)
    client.put("/api/admin/submission", json={"open":True}, headers=admin_headers)
    def break_insert(_conn, _cursor, statement, _parameters, _context, _many):
        if statement.startswith("INSERT INTO submissions"):
            raise OperationalError("test insert",{},Exception("test failure"))
    event.listen(engine,"before_cursor_execute",break_insert)
    try:
        assert send(client,team_headers).status_code == 503
    finally:
        event.remove(engine,"before_cursor_execute",break_insert)
    assert list(settings.submission_dir.glob("*.py")) == []
    with engine.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(submissions)) == 0


def test_team_cannot_see_other_team_or_schedule(client, team_headers, admin_headers):
    client.put("/api/admin/registration", json={"open":False}, headers=admin_headers)
    client.put("/api/admin/submission", json={"open":True}, headers=admin_headers)
    assert send(client,team_headers).status_code == 201
    client.put("/api/admin/submission",json={"open":False},headers=admin_headers)
    client.put("/api/admin/registration",json={"open":True},headers=admin_headers)
    assert client.post("/api/teams",json={"username":"otherteam","password":"test-only-password"}).status_code == 201
    token=client.post("/api/auth/login",json={"username":"otherteam","password":"test-only-password"}).json()["access_token"]
    other={"Authorization":"Bearer "+token}
    assert client.get("/api/submissions/me",headers=other).json() == []
    assert client.put("/api/admin/submission",json={"open":False},headers=other).status_code == 403


def test_exclusive_windows_and_manual_override(client, admin_headers, opened):
    assert client.put("/api/admin/submission",json={"open":True},headers=admin_headers).status_code == 409
    view=client.get("/api/competition").json()
    assert view["registration_open"] and not view["submission_open"]
    start=datetime.now(timezone.utc)+timedelta(hours=1)
    end=start+timedelta(hours=1)
    schedule={"mode":"SCHEDULED","opens_at":start.isoformat(),"closes_at":end.isoformat()}
    assert client.put("/api/admin/submission",json=schedule,headers=admin_headers).status_code == 409
    assert client.put("/api/admin/registration",json={"open":False},headers=admin_headers).status_code == 200
    assert client.put("/api/admin/submission",json=schedule,headers=admin_headers).status_code == 200
    assert not client.get("/api/competition").json()["submission_open"]
    assert client.put("/api/admin/submission",json={"open":True},headers=admin_headers).status_code == 200
    window=client.get("/api/competition").json()["submission_window"]
    assert window["mode"] == "MANUAL" and window["open"] and window["opens_at"] is None


def test_adjacent_schedules_allowed_overlap_rejected(client,admin_headers):
    now=datetime.now(timezone.utc)
    start=now+timedelta(hours=1)
    middle=start+timedelta(hours=1)
    end=middle+timedelta(hours=1)
    def schedule(a,b):
        return {"mode":"SCHEDULED","opens_at":a.isoformat(),"closes_at":b.isoformat()}
    assert client.put("/api/admin/registration",json=schedule(start,middle),headers=admin_headers).status_code == 200
    assert client.put("/api/admin/submission",json=schedule(middle,end),headers=admin_headers).status_code == 200
    assert client.put("/api/admin/submission",json=schedule(middle-timedelta(seconds=1),end),headers=admin_headers).status_code == 409
    assert client.get("/api/competition").json()["submission_window"]["opens_at"] == middle.isoformat()


def test_elapsed_schedule_does_not_block_manual_open(client,admin_headers):
    now=datetime.now(timezone.utc)
    old={"mode":"SCHEDULED","opens_at":(now-timedelta(hours=2)).isoformat(),"closes_at":(now-timedelta(hours=1)).isoformat()}
    assert client.put("/api/admin/registration",json=old,headers=admin_headers).status_code == 200
    assert client.put("/api/admin/submission",json={"open":True},headers=admin_headers).status_code == 200


def test_schedule_validates_timezone_and_order(client,admin_headers):
    for body in [{"mode":"SCHEDULED"}, {"mode":"SCHEDULED","opens_at":"2026-10-12T10:00:00","closes_at":"2026-10-12T11:00:00"},
                 {"mode":"SCHEDULED","opens_at":"2026-10-12T10:00:00+07:00","closes_at":"2026-10-12T09:00:00+07:00"}]:
        assert client.put("/api/admin/submission",json=body,headers=admin_headers).status_code == 422
    body={"mode":"SCHEDULED","opens_at":"2026-10-12T10:00:00+07:00","closes_at":"2026-10-12T11:00:00+07:00"}
    response=client.put("/api/admin/submission",json=body,headers=admin_headers)
    assert response.status_code == 200 and response.json()["opens_at"].startswith("2026-10-12T03:")


def test_schedule_boundaries():
    start=datetime(2026,1,1,1)
    end=start+timedelta(hours=1)
    c={"submission_mode":"SCHEDULED","submission_open":False,"submission_opens_at":start,"submission_closes_at":end}
    assert not is_open(c,"submission",start-timedelta(microseconds=1))
    assert is_open(c,"submission",start)
    assert is_open(c,"submission",end-timedelta(microseconds=1))
    assert not is_open(c,"submission",end)


def test_cannot_remove_team_with_submission(client,team_headers,admin_headers):
    client.put("/api/admin/registration",json={"open":False},headers=admin_headers)
    client.put("/api/admin/submission",json={"open":True},headers=admin_headers)
    send(client,team_headers)
    team=client.get("/api/teams/me",headers=team_headers).json()
    assert client.delete(f"/api/admin/teams/{team['id']}",headers=admin_headers).status_code == 409


def test_pending_does_not_execute_source(client,team_headers,admin_headers,tmp_path):
    client.put("/api/admin/registration",json={"open":False},headers=admin_headers)
    client.put("/api/admin/submission",json={"open":True},headers=admin_headers)
    marker=tmp_path / "must-not-exist"
    source=f"open({str(marker)!r}, 'w').write('executed')".encode()
    response=send(client,team_headers,source)
    assert response.status_code == 201
    assert response.json()["validation_status"] == "PENDING"
    assert not marker.exists()


def test_chunked_request_body_is_bounded(client,team_headers):
    # No Content-Length header: the ASGI receive guard must enforce the limit.
    def chunks():
        for _ in range(20):
            yield b"x" * 65536
    response=client.post("/api/submissions",headers={**team_headers,
        "Content-Type":"multipart/form-data; boundary=boundary"},content=chunks())
    assert response.status_code == 413
