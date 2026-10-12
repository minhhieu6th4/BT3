import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select

from backend.models.tables import users
from backend.security import read_token

bearer = HTTPBearer(auto_error=False)


def current_user(request: Request,
                 credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
    denied = HTTPException(401, "Phiên đăng nhập không hợp lệ hoặc đã hết hạn.",
                          headers={"WWW-Authenticate": "Bearer"})
    if credentials is None:
        raise denied
    try:
        user_id = read_token(credentials.credentials, request.app.state.settings)
    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise denied from None
    with request.app.state.engine.connect() as connection:
        user = connection.execute(select(users).where(users.c.id == user_id)).mappings().first()
    if user is None or not user["active"]:
        raise denied
    return dict(user)


def require_admin(user=Depends(current_user)):
    if user["account_type"] != "ADMIN":
        raise HTTPException(403, "Chỉ quản trị viên được thực hiện thao tác này.")
    return user
