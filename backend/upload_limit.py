from fastapi import HTTPException
from starlette.responses import JSONResponse


class UploadLimit:
    """Cap multipart bytes before unbounded data can spool to disk."""
    def __init__(self, app, max_bytes):
        self.app = app
        self.max_bytes = max_bytes + 65536  # multipart boundary/header allowance

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] != "POST" or scope["path"] != "/api/submissions":
            return await self.app(scope, receive, send)
        length = dict(scope["headers"]).get(b"content-length")
        try:
            oversized = length is not None and int(length) > self.max_bytes
        except ValueError:
            oversized = True
        if oversized:
            return await JSONResponse({"detail": "Yêu cầu nộp bài vượt giới hạn dung lượng."},
                                      status_code=413)(scope, receive, send)
        received = 0
        async def limited_receive():
            nonlocal received
            message = await receive()
            received += len(message.get("body", b""))
            if received > self.max_bytes:
                raise HTTPException(413, "Yêu cầu nộp bài vượt giới hạn dung lượng.")
            return message
        await self.app(scope, limited_receive, send)
