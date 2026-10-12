from fastapi import APIRouter, Depends, Request

from backend.dependencies import require_admin
from backend.schemas.windows import WindowControl
from backend.services.registration import get_competition, team_count, utc_now
from backend.services.windows import is_open, window_view, set_window
from datetime import timezone

router = APIRouter(tags=["Giải và quản trị"])


@router.get("/api/competition")
def competition_status(request: Request):
    with request.app.state.engine.connect() as connection:
        competition = get_competition(connection, request.app.state.settings.competition_code)
        count = team_count(connection, competition["id"])
    now = utc_now()
    return {"id": competition["id"], "code": competition["code"],
            "name": competition["name"], "mode": competition["mode"],
            "status": competition["status"],
            "registration_open": is_open(competition, "registration", now),
            "registration_available": is_open(competition, "registration", now) and count < competition["max_teams"],
            "team_count": count, "max_teams": competition["max_teams"],
            "submission_open": is_open(competition, "submission", now),
            "registration_window": window_view(competition, "registration", now),
            "submission_window": window_view(competition, "submission", now),
            "server_time": now.replace(tzinfo=timezone.utc).isoformat(),
            "submission_max_bytes": request.app.state.settings.max_submission_bytes,
            "submission_filename": "student_bot.py"}


@router.put("/api/admin/registration")
def registration_control(body: WindowControl, request: Request,
                         admin=Depends(require_admin)):
    return set_window(request.app.state.engine, request.app.state.settings.competition_code,
                      "registration", body, admin["id"])


@router.delete("/api/admin/teams/{team_id}")
def delete_demo_team(team_id: int, request: Request, admin=Depends(require_admin)):
    from backend.services.registration import remove_demo_team
    return remove_demo_team(request.app.state.engine,
                            request.app.state.settings.competition_code,
                            team_id, admin["id"])


@router.put("/api/admin/submission")
def submission_control(body: WindowControl, request: Request, admin=Depends(require_admin)):
    return set_window(request.app.state.engine, request.app.state.settings.competition_code,
                      "submission", body, admin["id"])
