from sqlalchemy import URL, create_engine, event
from sqlalchemy.engine import Engine

from backend.config import Settings


def create_mysql_engine(settings: Settings) -> Engine:
    url = URL.create(
        "mysql+pymysql", username=settings.db_user,
        password=settings.db_password.get_secret_value(), host=settings.db_host,
        port=settings.db_port, database=settings.db_name,
        query={"charset": "utf8mb4"},
    )
    engine = create_engine(url, pool_pre_ping=True, pool_recycle=1800,
                           connect_args={"connect_timeout": 5}, hide_parameters=True)

    @event.listens_for(engine, "connect")
    def set_utc(connection, _record):
        with connection.cursor() as cursor:
            cursor.execute("SET time_zone = '+00:00'")

    return engine
