import hashlib
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import func, insert, select

from backend.models.tables import audit_logs, submissions, teams
from backend.services.registration import get_competition, utc_now
from backend.services.windows import is_open


def own_team(connection, competition_id, user, *, lock=False):
    if user["account_type"] != "TEAM":
        raise HTTPException(403, "Chỉ tài khoản đội được nộp Bot và xem bài của đội.")
    query = select(teams).where(teams.c.competition_id == competition_id,
        teams.c.owner_user_id == user["id"], teams.c.status.in_(["REGISTERED", "APPROVED"]))
    if lock:
        query = query.with_for_update()
    team = connection.execute(query).mappings().first()
    if team is None:
        raise HTTPException(403, "Không có đội đủ điều kiện trong giải hiện tại.")
    return team


def public_submission(row):
    # Never expose filesystem paths or other teams' source files.
    from datetime import timezone
    def stamp(value):
        return value.replace(tzinfo=timezone.utc).isoformat() if value else None
    return {"id": row["id"], "version": row["version"], "filename": "student_bot.py",
            "size_bytes": row["source_size_bytes"], "received_at": stamp(row["received_at"]),
            "validation_status": row["validation_status"],
            "validation_message": row["validation_message"], "validated_at": stamp(row["validated_at"])}


def list_own_submissions(engine, code, user):
    with engine.connect() as connection:
        competition = get_competition(connection, code)
        team = own_team(connection, competition["id"], user)
        rows = connection.execute(select(submissions).where(submissions.c.team_id == team["id"])
            .order_by(submissions.c.version.desc())).mappings().all()
        return [public_submission(row) for row in rows]


def accept_submission(engine, settings, user, data, received_at=None):
    received_at = received_at or utc_now()
    try:
        source = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise HTTPException(422, "File phải là văn bản Python mã hóa UTF-8.") from None
    if not source.strip() or "\x00" in source:
        raise HTTPException(422, "File rỗng hoặc không phải văn bản hợp lệ.")
    destination = None
    committed = False
    try:
        with engine.begin() as connection:
            competition = get_competition(connection, settings.competition_code, lock=True)
            # Check the server timestamp captured after the entire file was read.
            if not is_open(competition, "submission", received_at):
                raise HTTPException(409, "Nộp bài đang đóng hoặc ngoài thời gian đã hẹn.")
            team = own_team(connection, competition["id"], user, lock=True)
            version = (connection.scalar(select(func.max(submissions.c.version)).where(
                submissions.c.team_id == team["id"])) or 0) + 1
            folder = settings.submission_dir.resolve()
            try:
                folder.mkdir(parents=True, exist_ok=True, mode=0o700)
            except OSError:
                raise HTTPException(503, "Không tạo được thư mục lưu file; báo ban tổ chức.") from None
            filename = f"{uuid4().hex}.py"
            destination = folder / filename
            try:
                with destination.open("xb") as handle:
                    handle.write(data)
                destination.chmod(0o600)
            except OSError:
                raise HTTPException(503, "Không lưu được file. Hãy thử lại hoặc báo ban tổ chức.") from None
            values = {"team_id": team["id"], "submitted_by": user["id"], "version": version,
                      "source_file_path": filename, "source_sha256": hashlib.sha256(data).hexdigest(),
                      "source_size_bytes": len(data), "received_at": received_at,
                      "validation_status": "PENDING",
                      "validation_message": "Đã nhận file, chờ Validator/Judge kiểm tra."}
            result = connection.execute(insert(submissions).values(**values))
            submission_id = result.inserted_primary_key[0]
            connection.execute(insert(audit_logs).values(competition_id=competition["id"],
                actor_user_id=user["id"], action="SUBMISSION_RECEIVED",
                details={"team_id": team["id"], "submission_id": submission_id, "version": version}))
        committed = True
        return public_submission({"id": submission_id, "validated_at": None, **values})
    finally:
        if not committed and destination is not None:
            destination.unlink(missing_ok=True)
