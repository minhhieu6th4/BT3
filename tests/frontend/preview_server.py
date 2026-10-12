"""Isolated UI QA server: python -m tests.frontend.preview_server (port 8001).
Disposable SQLite in memory, fake credentials only; never accesses MySQL/.env.
"""
import uvicorn
from sqlalchemy import create_engine, insert
from sqlalchemy.pool import StaticPool
from backend.config import Settings
from backend.main import create_app
from backend.models.tables import metadata, users, competitions, schema_migrations
from backend.security import hash_password


def preview_app():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    metadata.create_all(engine)
    with engine.begin() as connection:
        connection.execute(insert(schema_migrations).values(version="0001_initial"))
        connection.execute(insert(competitions).values(code="demo", name="BT3 Demo · Kiểm thử giao diện",
            mode="DEMO", status="DRAFT", max_teams=6, registration_open=False,
            submission_open=False, format_config={}))
        connection.execute(insert(users).values(username="preview-admin", account_type="ADMIN",
            active=True, password_hash=hash_password("preview-password-only")))
    return create_app(Settings(_env_file=None, jwt_secret="preview-only-secret-" * 4), engine)


if __name__ == "__main__":
    uvicorn.run(preview_app(), host="127.0.0.1", port=8001)
