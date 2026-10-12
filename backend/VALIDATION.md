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
