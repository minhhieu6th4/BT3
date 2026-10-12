"""Optional integration test against a dedicated, preinitialized MySQL database.
Never uses the configured application database. Enable BT3_TEST_MYSQL_DATABASE.
"""
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from fastapi import HTTPException
from sqlalchemy import delete, insert, select, func
from sqlalchemy.exc import IntegrityError

from backend.config import Settings
from backend.database.connection import create_mysql_engine
from backend.models.tables import audit_logs, competitions, teams, users
from backend.security import hash_password
from backend.services.registration import register_team


@pytest.fixture
def mysql_case():
    database = os.getenv("BT3_TEST_MYSQL_DATABASE")
    if not database:
        pytest.skip("Dedicated MySQL test database not configured")
    if not database.startswith("bt3_test_"):
        pytest.fail("Test database name must start with bt3_test_; main/demo are forbidden")
    settings = Settings(_env_file=None, db_name=database,
        db_host=os.getenv("BT3_TEST_MYSQL_HOST", "localhost"),
        db_port=int(os.getenv("BT3_TEST_MYSQL_PORT", "3306")),
        db_user=os.environ["BT3_TEST_MYSQL_USER"],
        db_password=os.environ["BT3_TEST_MYSQL_PASSWORD"], jwt_secret="test-only-" * 8)
    engine = create_mysql_engine(settings)
    code = "test_" + uuid.uuid4().hex
    with engine.begin() as connection:
        result = connection.execute(insert(competitions).values(code=code, name="Concurrency test",
            mode="DEMO", status="REGISTRATION", max_teams=1,
            registration_open=True, submission_open=False, format_config={}))
        competition_id = result.inserted_primary_key[0]
    yield engine, code, competition_id
    # Remove only rows created for this unique test, retaining preexisting rows.
    with engine.begin() as connection:
        user_ids = connection.scalars(select(teams.c.owner_user_id).where(
            teams.c.competition_id == competition_id)).all()
        connection.execute(delete(audit_logs).where(audit_logs.c.competition_id == competition_id))
        connection.execute(delete(teams).where(teams.c.competition_id == competition_id))
        connection.execute(delete(competitions).where(competitions.c.id == competition_id))
        if user_ids:
            connection.execute(delete(users).where(users.c.id.in_(user_ids)))
    engine.dispose()


def test_mysql_concurrent_last_slot(mysql_case):
    engine, code, competition_id = mysql_case
    barrier = Barrier(2)
    password_hash = hash_password("test-only-password")
    prefix = "t_" + uuid.uuid4().hex[:16]
    def attempt(n):
        barrier.wait(timeout=10)
        try:
            register_team(engine, code, f"{prefix}_{n}", password_hash)
            return 201
        except HTTPException as exc:
            return exc.status_code
    with ThreadPoolExecutor(max_workers=2) as executor:
        assert sorted(executor.map(attempt, [1, 2])) == [201, 409]
    with engine.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(teams).where(
            teams.c.competition_id == competition_id)) == 1
        assert connection.scalar(select(func.count()).select_from(users).where(
            users.c.username.like(prefix + "%"))) == 1


def test_mysql_duplicate_rolls_back(mysql_case):
    engine, code, competition_id = mysql_case
    # Raise capacity so duplicate check, not capacity, is exercised.
    from sqlalchemy import update
    with engine.begin() as connection:
        connection.execute(update(competitions).where(competitions.c.id == competition_id).values(max_teams=6))
    name = "t_" + uuid.uuid4().hex[:16]
    hashed = hash_password("test-only-password")
    register_team(engine, code, name, hashed)
    with pytest.raises(HTTPException) as error:
        register_team(engine, code, name, hashed)
    assert error.value.status_code == 409
    with engine.connect() as connection:
        assert connection.scalar(select(func.count()).select_from(teams).where(
            teams.c.competition_id == competition_id)) == 1
