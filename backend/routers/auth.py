from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select

from backend.dependencies import current_user
from backend.models.tables import users
from backend.schemas.accounts import Credentials, TokenView, UserView
from backend.security import make_token, verify_password

router = APIRouter(prefix="/api/auth", tags=["Đăng nhập"])


@router.post("/login", response_model=TokenView)
def login(body: Credentials, request: Request):
    with request.app.state.engine.connect() as connection:
        user = connection.execute(select(users).where(
            users.c.username == body.username)).mappings().first()
    valid = verify_password(body.password, user["password_hash"] if user else None)
    if not valid or user is None or not user["active"]:
        raise HTTPException(401, "Tên đăng nhập hoặc mật khẩu không đúng.")
    settings = request.app.state.settings
    return {"access_token": make_token(user["id"], settings),
            "expires_in": settings.access_token_minutes * 60, "user": user}


@router.get("/me", response_model=UserView)
def me(user=Depends(current_user)):
    return user
