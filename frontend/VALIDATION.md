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
