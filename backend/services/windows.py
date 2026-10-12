from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy import insert, update
from backend.models.tables import audit_logs, competitions
from backend.services.registration import get_competition, utc_now


def is_open(competition, kind, now=None):
    now = now or utc_now()
    if competition[f"{kind}_mode"] == "MANUAL":
        return bool(competition[f"{kind}_open"])
    start = competition[f"{kind}_opens_at"]
    end = competition[f"{kind}_closes_at"]
    return start is not None and end is not None and start <= now < end


def window_view(competition, kind, now=None):
    def stamp(value):
        return value.replace(tzinfo=timezone.utc).isoformat() if value else None
    return {"mode": competition[f"{kind}_mode"], "open": is_open(competition, kind, now),
            "opens_at": stamp(competition[f"{kind}_opens_at"]),
            "closes_at": stamp(competition[f"{kind}_closes_at"])}


def remaining_interval(competition, kind, now):
    if competition[f"{kind}_mode"] == "MANUAL":
        return (now, datetime.max) if competition[f"{kind}_open"] else None
    start = competition[f"{kind}_opens_at"]
    end = competition[f"{kind}_closes_at"]
    if start is None or end is None or end <= now:
        return None
    return max(start, now), end


def ensure_no_overlap(competition, now):
    registration = remaining_interval(competition, "registration", now)
    submission = remaining_interval(competition, "submission", now)
    if registration and submission and max(registration[0], submission[0]) < min(registration[1], submission[1]):
        raise HTTPException(409, "Đăng ký và nộp bài không được mở cùng lúc hoặc có lịch chồng nhau. "
            "Hãy đóng cửa kia hoặc đặt hai lịch nối tiếp. Cửa mở thủ công chưa có giờ đóng, "
            "nên không thể hẹn cửa kia trong tương lai.")


def set_window(engine, code, kind, body, actor_id):
    if kind not in ("registration", "submission"):
        raise ValueError("Unknown window")
    with engine.begin() as connection:
        competition = get_competition(connection, code, lock=True)
        def utc(value):
            return value.astimezone(timezone.utc).replace(tzinfo=None) if value else None
        changes = {f"{kind}_mode": body.mode, f"{kind}_open": bool(body.open),
                   f"{kind}_opens_at": utc(body.opens_at), f"{kind}_closes_at": utc(body.closes_at)}
        candidate = {**competition, **changes}
        ensure_no_overlap(candidate, utc_now())
        # Both controls share the competition lock, including concurrent requests.
        connection.execute(update(competitions).where(competitions.c.id == competition["id"]).values(**changes))
        connection.execute(insert(audit_logs).values(competition_id=competition["id"],
            actor_user_id=actor_id, action=f"{kind.upper()}_CONTROL_CHANGED",
            details={"mode": body.mode, "open": body.open,
                     "opens_at": body.opens_at.isoformat() if body.opens_at else None,
                     "closes_at": body.closes_at.isoformat() if body.closes_at else None}))
        competition.update(changes)
        return window_view(competition, kind)
