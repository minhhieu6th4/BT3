import logging
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError

from backend.config import Settings
from backend.database.connection import create_mysql_engine
from backend.models.tables import schema_migrations
from backend.routers import auth, competition, teams, submissions
from backend.upload_limit import UploadLimit

logger = logging.getLogger(__name__)


def create_app(settings=None, engine=None):
    settings = settings or Settings()
    owned_engine = engine is None
    engine = engine or create_mysql_engine(settings)

    @asynccontextmanager
    async def lifespan(_app):
        yield
        if owned_engine:
            engine.dispose()

    app = FastAPI(title="BT3 Backend", version="0.1.0", lifespan=lifespan)
    app.state.settings = settings
    app.state.engine = engine
    app.add_middleware(UploadLimit, max_bytes=settings.max_submission_bytes)
    if settings.cors_origins:
        app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins,
                           allow_methods=["GET", "POST", "PUT", "DELETE"],
                           allow_headers=["Authorization", "Content-Type"])

    @app.exception_handler(RequestValidationError)
    async def invalid_request(_request: Request, exc: RequestValidationError):
        # Pydantic's default input field can echo a submitted password.
        errors = [{"loc": error["loc"], "msg": error["msg"], "type": error["type"]}
                  for error in exc.errors()]
        return JSONResponse(status_code=422, content={"detail": errors})

    @app.exception_handler(SQLAlchemyError)
    async def database_error(_request: Request, _exc: SQLAlchemyError):
        # Avoid printing connection credentials or bound data.
        logger.error("Database operation failed (%s)", type(_exc).__name__)
        if getattr(_exc, "orig", None) and getattr(_exc.orig, "args", [None])[0] == 1054:
            return JSONResponse(status_code=503, content={"detail":
                "Database cần cập nhật: chạy migration 0002_submission_windows.sql bằng tài khoản MySQL quản trị."})
        return JSONResponse(status_code=503, content={"detail":
            "Không truy cập được dữ liệu. Kiểm tra kết nối và schema MySQL."})

    @app.get("/api/health", tags=["Kết nối"])
    def health():
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            baseline = connection.scalar(select(schema_migrations.c.version).where(
                schema_migrations.c.version == "0001_initial"))
        if baseline is None:
            return JSONResponse(status_code=503, content={"detail": "Thiếu schema 0001_initial."})
        with engine.connect() as connection:
            latest = connection.scalar(select(schema_migrations.c.version).where(
                schema_migrations.c.version == "0002_submission_windows"))
        if latest is None:
            return JSONResponse(status_code=503, content={"detail":
                "Chạy database/migrations/0002_submission_windows.sql trên database đang dùng trước khi tiếp tục."})
        return {"status": "ok", "database": "connected", "schema": latest}

    app.include_router(auth.router)
    app.include_router(teams.router)
    app.include_router(competition.router)
    app.include_router(submissions.router)
    frontend = Path(__file__).resolve().parents[1] / "frontend"
    app.mount("/assets", StaticFiles(directory=frontend), name="frontend-assets")

    @app.get("/", include_in_schema=False)
    def frontend_home():
        return RedirectResponse("/demo", status_code=302)

    @app.get("/demo", include_in_schema=False)
    @app.get("/demo/", include_in_schema=False)
    @app.get("/demo/dang-nhap", include_in_schema=False)
    @app.get("/demo/dang-ky", include_in_schema=False)
    @app.get("/demo/nop-bai", include_in_schema=False)
    @app.get("/demo/doi", include_in_schema=False)
    @app.get("/demo/quan-tri", include_in_schema=False)
    @app.get("/main", include_in_schema=False)
    def frontend_page():
        return FileResponse(frontend / "index.html", headers={"Cache-Control": "no-store"})

    return app
