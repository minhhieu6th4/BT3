# BT3 — UET Algorithm Battle

Nền tảng thi đấu Bot Python. Kiến trúc: FastAPI, MySQL, Docker và HTML/CSS/JS.

- `database/README.md`: cấu trúc database và hướng dẫn khởi tạo.
- `backend/README.md`: cấu hình MySQL, tạo admin, chạy API và thử đăng ký đội demo.
- `game/`, `bots/`, `tournament/`: các thành phần hiện có, chưa tích hợp backend.

Backend hiện hỗ trợ kết nối dữ liệu, đăng nhập, phân quyền và mở/đóng đăng ký.
Giao diện người chơi/admin demo: mở http://127.0.0.1:8000/demo sau khi chạy backend.
Nộp Bot, Judge/Sandbox và điều phối giải chưa tích hợp backend ở giai đoạn này.
Xem frontend/README.md để biết các trang và cách thử.

Nộp Bot và lịch mở/đóng riêng đã có. Database cũ cần migration 0002 trước khi
sử dụng. Xem backend/README.md và frontend/README.md để cập nhật và thử.
