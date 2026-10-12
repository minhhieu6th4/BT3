import re

from pydantic import BaseModel, ConfigDict, Field, field_validator


def normalize_username(value: str) -> str:
    value = value.strip().lower()
    if not re.fullmatch(r"[a-z0-9_-]{3,64}", value):
        raise ValueError("Tên đăng nhập: 3–64 ký tự, dùng a-z, 0-9, _ hoặc -.")
    return value


class Credentials(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(max_length=64)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("username")
    @classmethod
    def username_format(cls, value: str) -> str:
        return normalize_username(value)


class UserView(BaseModel):
    id: int
    username: str
    account_type: str


class TokenView(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserView


class TeamView(BaseModel):
    id: int
    name: str
    competition_id: int
    status: str


class RegistrationView(BaseModel):
    user: UserView
    team: TeamView


class RegistrationControl(BaseModel):
    model_config = ConfigDict(extra="forbid")
    open: bool
