"""SQLAlchemy Core mappings of existing tables. Application never creates tables.

Only columns needed by this milestone are mapped; database/schema.sql remains
canonical. Test-only create_all creates isolated SQLite tables, not MySQL schema.
"""
from sqlalchemy import (MetaData, Table, Column, Integer, String, Boolean,
                        DateTime, ForeignKey, JSON, UniqueConstraint)

metadata = MetaData()
users = Table("users", metadata,
    Column("id", Integer, primary_key=True),
    Column("username", String(64), nullable=False, unique=True),
    Column("password_hash", String(255), nullable=False),
    Column("account_type", String(16), nullable=False),
    Column("active", Boolean, nullable=False, default=True),
)
competitions = Table("competitions", metadata,
    Column("id", Integer, primary_key=True),
    Column("code", String(64), nullable=False, unique=True),
    Column("name", String(150), nullable=False),
    Column("mode", String(8), nullable=False),
    Column("status", String(32), nullable=False, default="DRAFT"),
    Column("max_teams", Integer, nullable=False),
    Column("registration_open", Boolean, nullable=False, default=False),
    Column("submission_open", Boolean, nullable=False, default=False),
    Column("registration_opens_at", DateTime),
    Column("registration_closes_at", DateTime),
    Column("submission_opens_at", DateTime),
    Column("submission_closes_at", DateTime),
    Column("format_config", JSON, nullable=False),
)
teams = Table("teams", metadata,
    Column("id", Integer, primary_key=True),
    Column("competition_id", Integer, ForeignKey("competitions.id"), nullable=False),
    Column("name", String(100), nullable=False),
    Column("owner_user_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("status", String(32), nullable=False, default="REGISTERED"),
    UniqueConstraint("competition_id", "name"),
    UniqueConstraint("competition_id", "owner_user_id"),
)
audit_logs = Table("audit_logs", metadata,
    Column("id", Integer, primary_key=True),
    Column("competition_id", Integer, ForeignKey("competitions.id")),
    Column("actor_user_id", Integer, ForeignKey("users.id")),
    Column("action", String(100), nullable=False),
    Column("details", JSON),
)
schema_migrations = Table("schema_migrations", metadata,
    Column("version", String(64), primary_key=True),
)
