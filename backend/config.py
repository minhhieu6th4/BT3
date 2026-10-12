from pathlib import Path

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")
    db_host: str = "localhost"
    db_port: int = Field(default=3306, ge=1, le=65535)
    db_name: str = "BT3_Schema1"
    db_user: str = "bt3_app"
    db_password: SecretStr = SecretStr("")
    jwt_secret: SecretStr
    access_token_minutes: int = Field(default=30, ge=1, le=1440)
    competition_code: str = "demo"
    cors_origins: list[str] = []

    @field_validator("jwt_secret")
    @classmethod
    def valid_secret(cls, value: SecretStr) -> SecretStr:
        secret = value.get_secret_value()
        if len(secret) < 32 or secret.startswith("replace-"):
            raise ValueError("JWT_SECRET phải là chuỗi ngẫu nhiên riêng, ít nhất 32 ký tự.")
        return value
