from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import func, insert, select, update
from sqlalchemy.exc import IntegrityError

from backend.models.tables import audit_logs, competitions, submissions, teams, users


def utc_now():
    # MySQL DATETIME stores UTC without a timezone marker.
    return datetime.now(timezone.utc).replace(tzinfo=None)


def in_registration_window(competition, now):
    start, end = competition["registration_opens_at"], competition["registration_closes_at"]
    return (start is None or now >= start) and (end is None or now < end)


def get_competition(connection, code, *, lock=False):
    query = select(competitions).where(competitions.c.code == code)
    if lock:
        query = query.with_for_update()
    row = connection.execute(query).mappings().first()
    if row is None:
        raise HTTPException(404, "Chưa có giải được cấu hình. Kiểm tra dữ liệu seed.")
    return dict(row)


def team_count(connection, competition_id):
    return connection.scalar(select(func.count()).select_from(teams).where(
        teams.c.competition_id == competition_id, teams.c.status != "WITHDRAWN"))


def register_team(engine, code, username, password_hash):
    try:
        with engine.begin() as connection:
            competition = get_competition(connection, code, lock=True)
            if competition["mode"] != "DEMO":
                raise HTTPException(409, "Đăng ký tài khoản đội đơn giản hiện chỉ hỗ trợ demo.")
            now = utc_now()
            from backend.services.windows import is_open
            if not is_open(competition, "registration", now):
                raise HTTPException(409, "Đăng ký hiện đang đóng hoặc ngoài thời hạn.")
            if team_count(connection, competition["id"]) >= competition["max_teams"]:
                raise HTTPException(409, "Đã đủ đội tham gia.")
            user_id = connection.execute(insert(users).values(
                username=username, password_hash=password_hash, account_type="TEAM",
                active=True)).inserted_primary_key[0]
            team_id = connection.execute(insert(teams).values(
                competition_id=competition["id"], name=username,
                owner_user_id=user_id, status="REGISTERED")).inserted_primary_key[0]
            connection.execute(insert(audit_logs).values(
                competition_id=competition["id"], actor_user_id=user_id,
                action="TEAM_REGISTERED", details={"team_id": team_id}))
            return {"user": {"id": user_id, "username": username, "account_type": "TEAM"},
                    "team": {"id": team_id, "name": username,
                             "competition_id": competition["id"], "status": "REGISTERED"}}
    except IntegrityError as exc:
        # MySQL duplicate key; SQLite is only used in isolated unit tests.
        errno = exc.orig.args[0] if exc.orig.args else None
        if errno == 1062 or "UNIQUE constraint failed" in str(exc.orig):
            raise HTTPException(409, "Tên đăng nhập hoặc tên đội đã tồn tại.") from None
        raise


def control_registration(engine, code, opened, actor_id):
    from backend.services.windows import set_window
    from backend.schemas.windows import WindowControl
    return set_window(engine, code, "registration", WindowControl(open=opened), actor_id)


def remove_demo_team(engine, code, team_id, actor_id):
    """Archive a demo team and retire its account; preserve historical foreign keys."""
    with engine.begin() as connection:
        competition = get_competition(connection, code, lock=True)
        if competition["mode"] != "DEMO":
            raise HTTPException(409, "Chỉ được xóa đội bằng chức năng này trong demo.")
        if competition["status"] not in ("DRAFT", "REGISTRATION", "CODING"):
            raise HTTPException(409, "Không xóa đội khi đã bắt đầu xử lý thi đấu.")
        team = connection.execute(select(teams).where(
            teams.c.id == team_id, teams.c.competition_id == competition["id"],
            teams.c.status != "WITHDRAWN").with_for_update()).mappings().first()
        if team is None:
            raise HTTPException(404, "Không tìm thấy đội đang tham gia giải demo này.")
        has_submissions = connection.scalar(select(func.count()).select_from(submissions).where(
            submissions.c.team_id == team_id))
        if has_submissions:
            raise HTTPException(409, "Đội đã có bài nộp; không xóa để tránh mất lịch sử thi đấu.")
        owner = connection.execute(select(users).where(
            users.c.id == team["owner_user_id"]).with_for_update()).mappings().one()
        other_teams = connection.scalar(select(func.count()).select_from(teams).where(
            teams.c.owner_user_id == owner["id"], teams.c.id != team_id,
            teams.c.status != "WITHDRAWN"))
        if owner["account_type"] != "TEAM" or other_teams:
            raise HTTPException(409, "Không thể xóa đội có chủ tài khoản đặc biệt hoặc dùng chung.")
        old_name = team["name"]
        # '~' cannot occur in a registered username; IDs make archive names unique.
        connection.execute(update(teams).where(teams.c.id == team_id).values(
            status="WITHDRAWN", name=f"~removed-team-{team_id}"))
        connection.execute(update(users).where(users.c.id == owner["id"]).values(
            active=False, username=f"~removed-user-{owner['id']}"))
        connection.execute(insert(audit_logs).values(
            competition_id=competition["id"], actor_user_id=actor_id,
            action="DEMO_TEAM_REMOVED", details={"team_id": team_id,
                "original_name": old_name, "retired_user_id": owner["id"]}))
        return {"removed_team_id": team_id, "name": old_name,
                "detail": "Đã xóa đội khỏi demo, vô hiệu hóa tài khoản và giải phóng suất/tên."}
