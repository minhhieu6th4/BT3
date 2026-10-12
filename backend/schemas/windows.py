from typing import Literal
from pydantic import AwareDatetime, BaseModel, ConfigDict, model_validator


class WindowControl(BaseModel):
    model_config = ConfigDict(extra="forbid", json_schema_extra={"examples": [
        {"mode": "MANUAL", "open": True},
        {"mode": "SCHEDULED", "opens_at": "2026-10-13T09:00:00+07:00",
         "closes_at": "2026-10-13T14:00:00+07:00"},
    ]})
    mode: Literal["MANUAL", "SCHEDULED"] = "MANUAL"
    open: bool | None = None
    opens_at: AwareDatetime | None = None
    closes_at: AwareDatetime | None = None

    @model_validator(mode="after")
    def valid_window(self):
        if self.mode == "MANUAL":
            if self.open is None or self.opens_at is not None or self.closes_at is not None:
                raise ValueError("Chế độ thủ công cần open=true/false và không có lịch.")
        elif (self.open is not None or self.opens_at is None or self.closes_at is None
              or self.closes_at <= self.opens_at):
            raise ValueError("Lịch cần thời điểm mở/đóng có múi giờ và đóng sau mở.")
        return self
