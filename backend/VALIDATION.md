# Kết quả kiểm thử backend

Ngày 12/10/2026, Python 3.12, thư viện theo requirements.txt và requirements-dev.txt.

- 13 kiểm thử API/hành vi thành công; 2 kiểm thử MySQL tùy chọn được bỏ qua vì
  chưa có tài khoản/database kiểm thử MySQL được cấu hình.
- Kiểm tra cú pháp Python và git diff --check thành công.
- Kiểm thử chạy ngoài sandbox vì TestClient bị treo trong môi trường hạn chế;
  các test đã chạy dùng SQLite trong bộ nhớ, không chạm BT3_Schema1.
- Có một cảnh báo deprecation từ Starlette về httpx trong TestClient; không làm
  thất bại kiểm thử. Phiên bản đã kiểm tra được ghi cố định trong requirements.

Chưa kiểm chứng kết nối thực tới BT3_Schema1 hoặc khóa hàng dưới MySQL. Người dùng
chưa có tài khoản MySQL dành cho backend. Đã cung cấp mẫu tạo bt3_app và hướng dẫn
.env, tạo admin, chạy /api/health và luồng /docs. Không thay đổi schema.sql, không
chạy lại seed, không chạy Bot, không commit/push.

## Nộp Bot và lịch tự động (12/10/2026)

27 test backend thành công, 2 test MySQL tùy chọn chưa cấu hình; chưa thực thi
migration 0002 lên MySQL của người dùng. Kiểm thử giao diện trên dữ liệu SQLite
riêng: hai cửa cùng mở, lưu lịch VN, đội đăng ký/login/nộp file, lịch sử v1 PENDING.
Không thực thi Bot, không đổi .env hay dữ liệu thật. User cần áp dụng migration
bằng kết nối quản trị MySQL trước khi dùng bản này trên BT3_Schema1.

## Điều chỉnh ngày 13/10/2026

Người dùng xác nhận database mới có 0001_initial, nên đã sửa migration 0002
chưa áp dụng để GIỮ ck_open_phases. Mã hiện tại chỉ cho một cửa mở mỗi thời điểm,
chặn lịch chồng nhau và cho lịch nối tiếp. Các mô tả kiểm thử hai cửa cùng mở
ở phần trước là lịch sử phiên bản cũ, không còn là hành vi hiện tại.
29 test thành công, 2 test MySQL tùy chọn chưa chạy; chưa thực thi migration lên
database người dùng. Không xóa dữ liệu, không đổi .env, không commit/push.
