from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select

from backend.dependencies import current_user
from backend.models.tables import competitions, teams
from backend.schemas.accounts import Credentials, RegistrationView, TeamView
from backend.security import hash_password
from backend.services.registration import register_team

router = APIRouter(prefix="/api/teams", tags=["Đội"])


@router.post("", response_model=RegistrationView, status_code=201)
def register(body: Credentials, request: Request):
    return register_team(request.app.state.engine, request.app.state.settings.competition_code,
                         body.username, hash_password(body.password))


@router.get("/me", response_model=TeamView)
def my_team(request: Request, user=Depends(current_user)):
    with request.app.state.engine.connect() as connection:
        row = connection.execute(select(teams).join(
            competitions, teams.c.competition_id == competitions.c.id).where(
            teams.c.owner_user_id == user["id"],
            competitions.c.code == request.app.state.settings.competition_code,
            teams.c.status != "WITHDRAWN"
        )).mappings().first()
    if row is None:
        raise HTTPException(404, "Tài khoản không có đội trong giải hiện tại.")
    return row


@router.get("", response_model=list[TeamView])
def list_teams(request: Request):
    with request.app.state.engine.connect() as connection:
        return connection.execute(select(teams).join(
            competitions, teams.c.competition_id == competitions.c.id).where(
            competitions.c.code == request.app.state.settings.competition_code,
            teams.c.status != "WITHDRAWN"
        ).order_by(teams.c.id)).mappings().all()
