from fastapi import APIRouter, Depends, Request

from backend.dependencies import require_admin
from backend.schemas.accounts import RegistrationControl
from backend.services.registration import (control_registration, get_competition,
                                           in_registration_window, team_count, utc_now)

router = APIRouter(tags=["Giải và quản trị"])


@router.get("/api/competition")
def competition_status(request: Request):
    with request.app.state.engine.connect() as connection:
        competition = get_competition(connection, request.app.state.settings.competition_code)
        count = team_count(connection, competition["id"])
    return {"id": competition["id"], "code": competition["code"],
            "name": competition["name"], "mode": competition["mode"],
            "status": competition["status"], "registration_open": bool(competition["registration_open"]),
            "registration_available": bool(competition["registration_open"]
                and competition["status"] == "REGISTRATION"
                and in_registration_window(competition, utc_now())
                and count < competition["max_teams"]),
            "team_count": count, "max_teams": competition["max_teams"],
            "submission_open": bool(competition["submission_open"])}


@router.put("/api/admin/registration")
def registration_control(body: RegistrationControl, request: Request,
                         admin=Depends(require_admin)):
    return control_registration(request.app.state.engine,
                                request.app.state.settings.competition_code,
                                body.open, admin["id"])


@router.delete("/api/admin/teams/{team_id}")
def delete_demo_team(team_id: int, request: Request, admin=Depends(require_admin)):
    from backend.services.registration import remove_demo_team
    return remove_demo_team(request.app.state.engine,
                            request.app.state.settings.competition_code,
                            team_id, admin["id"])
