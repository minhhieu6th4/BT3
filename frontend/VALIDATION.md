# Kiểm chứng giao diện demo

Ngày 12/10/2026.

- Kiểm thử trình duyệt trên FastAPI riêng tại cổng 8001 với SQLite trong bộ nhớ:
  admin đăng nhập đúng trang; mở đăng ký; đăng ký đội; thông báo thành công;
  đội đăng nhập đúng trang; admin thấy đội mới; hộp xác nhận xóa; xóa đội giải
  phóng suất; đóng đăng ký; nút đăng ký bị vô hiệu hóa khi đóng.
- Kiểm tra hiển thị trang đăng nhập trên backend đang chạy của người dùng ở
  cổng 8000, chỉ đọc trạng thái, không thêm/xóa đội ở database thực.
- Kiểm tra màn hình nhỏ 390px: không tràn chiều ngang; reset viewport sau thử.
- 16 kiểm thử backend/static route thành công; 2 MySQL tùy chọn chưa cấu hình.
- Node kiểm tra cú pháp hai module JS thành công; Python compile và diff check tốt.

Dữ liệu QA cổng 8001 bị bỏ khi tắt máy chủ. Không chạy lại schema/seed, không đổi
.env, không thêm tài khoản thực, không commit/push. /main là thông báo chưa mở,
chưa kết nối database main. Frontend chưa có trang guest/submission/thi đấu.

## Trang nộp bài và hẹn giờ

Đã thử trên trình duyệt tại server tạm 8001: admin mở hai cửa độc lập và lưu
lịch nộp, đăng ký đội mới, đăng nhập đội, chọn student_bot.py, nộp v1 thành công,
hiển thị giờ VN/dung lượng/PENDING trong lịch sử. Khi thử đã sửa lỗi tự refresh
đóng form hẹn giờ trước khi người dùng nhập. Dữ liệu test riêng, không dùng MySQL.

## Điều chỉnh ngày 13/10/2026

Người dùng xác nhận database mới có 0001_initial, nên đã sửa migration 0002
chưa áp dụng để GIỮ ck_open_phases. Mã hiện tại chỉ cho một cửa mở mỗi thời điểm,
chặn lịch chồng nhau và cho lịch nối tiếp. Các mô tả kiểm thử hai cửa cùng mở
ở phần trước là lịch sử phiên bản cũ, không còn là hành vi hiện tại.
29 test thành công, 2 test MySQL tùy chọn chưa chạy; chưa thực thi migration lên
database người dùng. Không xóa dữ liệu, không đổi .env, không commit/push.
