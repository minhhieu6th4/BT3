# Kiểm thử backend

Chạy từ gốc BT3: `python -m pytest -q`.

Test mặc định dùng SQLite trong bộ nhớ riêng: kết nối/health, admin mở/đóng,
đăng ký/login/xem đội, quyền 401/403, tên trùng và rollback, giới hạn 6 đội,
ngoài lịch, giai đoạn CODING, token hết hạn, tài khoản inactive/thay quyền,
không cho đăng ký ADMIN, không trả password hoặc lỗi database nội bộ.
Không truy cập database demo/main. SQLite không kiểm chứng SELECT FOR UPDATE.

Hai test MySQL chỉ chạy khi đã cấu hình rõ một database kiểm thử có tên bắt đầu
`bt3_test_`, có schema.sql và quyền SELECT/INSERT/UPDATE/DELETE cho tài khoản test.
Chúng tạo dữ liệu có mã ngẫu nhiên, kiểm tra hai đăng ký cùng tranh suất cuối và
trùng tên/rollback; sau đó xóa riêng dữ liệu đã tạo, không reset database.

Các biến môi trường cho test MySQL (không đưa mật khẩu lên Git/chat):
BT3_TEST_MYSQL_DATABASE, BT3_TEST_MYSQL_USER, BT3_TEST_MYSQL_PASSWORD;
BT3_TEST_MYSQL_HOST mặc định localhost; BT3_TEST_MYSQL_PORT mặc định 3306.
Không tự đọc .env chứa kết nối app để tránh vô tình kiểm thử vào BT3_Schema1.
Nếu chưa cấu hình, hai test này báo skipped. Backend thực tế luôn dùng MySQL.

Nộp bài: kiểm tra quyền/riêng tư, phiên bản, file UTF-8/rỗng/tên sai, cap upload
kể cả không Content-Length, rollback file khi SQL lỗi, không thực thi code đã nộp.
Lịch: chỉ một cửa mở, chặn lịch chồng nhau, cho lịch nối tiếp, lịch đã hết không chặn cửa mới, override thủ công, UTC và biên mở-inclusive/đóng-exclusive.
Test MySQL tùy chọn cần chạy migration 0002 ở database thử trước.
