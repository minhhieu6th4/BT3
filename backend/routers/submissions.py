from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from starlette.concurrency import run_in_threadpool
from backend.dependencies import current_user
from backend.services.registration import utc_now
from backend.services.submissions import accept_submission, list_own_submissions

router = APIRouter(prefix="/api/submissions", tags=["Nộp Bot"])


@router.get("/me")
def my_submissions(request: Request, user=Depends(current_user)):
    return list_own_submissions(request.app.state.engine,
                               request.app.state.settings.competition_code, user)


@router.post("", status_code=201)
async def upload_submission(request: Request, file: UploadFile = File(...), user=Depends(current_user)):
    try:
        if user["account_type"] != "TEAM":
            raise HTTPException(403, "Chỉ tài khoản đội được nộp Bot.")
        # Reject extra files/fields instead of silently accepting the first file.
        form = await request.form()
        if len(form.multi_items()) != 1 or form.multi_items()[0][0] != "file":
            raise HTTPException(422, "Chỉ nộp một file student_bot.py trong trường file.")
        if file.filename != "student_bot.py":
            raise HTTPException(422, "File phải có tên chính xác student_bot.py.")
        data = bytearray()
        while chunk := await file.read(65536):
            data.extend(chunk)
            if len(data) > request.app.state.settings.max_submission_bytes:
                raise HTTPException(413, "File vượt giới hạn dung lượng cho phép.")
        if not data:
            raise HTTPException(422, "File nộp không được rỗng.")
        return await run_in_threadpool(accept_submission, request.app.state.engine,
                                      request.app.state.settings, user, bytes(data), utc_now())
    finally:
        await file.close()
