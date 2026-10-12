"""Run from repository root: python -m backend.create_admin"""
import getpass

from pydantic import ValidationError
from sqlalchemy import insert
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from backend.config import Settings
from backend.database.connection import create_mysql_engine
from backend.models.tables import users
from backend.schemas.accounts import Credentials
from backend.security import hash_password


def main():
    username = input("Tên đăng nhập quản trị viên: ")
    password = getpass.getpass("Mật khẩu (8–128 ký tự): ")
    if password != getpass.getpass("Nhập lại mật khẩu: "):
        raise SystemExit("Hai mật khẩu không khớp; chưa tạo tài khoản.")
    try:
        credentials = Credentials(username=username, password=password)
    except ValidationError as exc:
        raise SystemExit("; ".join(error["msg"] for error in exc.errors())) from None
    engine = create_mysql_engine(Settings())
    try:
        with engine.begin() as connection:
            connection.execute(insert(users).values(username=credentials.username,
                password_hash=hash_password(credentials.password), account_type="ADMIN", active=True))
    except IntegrityError:
        raise SystemExit("Tên đăng nhập đã tồn tại; không thay đổi tài khoản cũ.") from None
    except SQLAlchemyError:
        raise SystemExit("Không tạo được admin. Kiểm tra .env và quyền MySQL.") from None
    finally:
        engine.dispose()
    print("Đã tạo tài khoản quản trị viên.")


if __name__ == "__main__":
    main()
