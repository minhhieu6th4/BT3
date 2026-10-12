# Trang nộp Bot và lịch tự động

Sau khi nâng database lên 0002 theo backend/README.md và chạy backend:

- Đội đăng nhập → Đến trang nộp bài → chọn student_bot.py → Nộp bài.
- /demo/nop-bai hiển thị lịch, quyền nộp và lịch sử phiên bản.
- Admin có hai thẻ Đăng ký đội/Nộp Bot riêng. Mở ngay/Đóng ngay là thủ công.
- Hẹn giờ tự động: nhập hai mốc theo giờ Việt Nam, Lưu lịch. Chỉ một cửa mở tại một thời điểm; lịch không được chồng nhau.
- Chọn thời điểm đóng sau mở. Mở/đóng ngay thay lịch cũ, cho phép mở lại.
- PENDING là đã nhận file, chưa được xác nhận hợp lệ; không có kết quả giả từ Judge.
- Giao diện tự cập nhật trạng thái; không xóa file đang chọn hay form lịch đang nhập.

Các mô tả cũ bên dưới nói nộp Bot chưa có hoặc hai cửa phụ thuộc đã được thay bằng
phần cập nhật này. Không chạy lại schema.sql; chỉ dùng migration 0002 cho DB cũ.

---

# Giao diện demo BT3

HTML/CSS/JavaScript thuần, không cần npm/build hoặc máy chủ frontend riêng.
FastAPI phục vụ giao diện và API trên cùng origin, nên không cần sửa CORS.

## Mở giao diện

Giữ backend chạy theo hướng dẫn backend/README.md, rồi mở:
http://127.0.0.1:8000/demo

Nếu backend không bật --reload, cần khởi động lại sau khi thêm route frontend.
Cấu hình .env vẫn chọn BT3_Schema1 và COMPETITION_CODE=demo. Không chạy lại SQL.
Không mở index.html trực tiếp bằng file:// vì các đường dẫn API cần FastAPI.

## Đường dẫn

- /demo: đưa về đăng nhập hoặc trang phù hợp tài khoản.
- /demo/dang-nhap: dùng chung form cho đội và admin; nhận diện vai trò từ backend.
- /demo/dang-ky: đăng ký tên đội/tài khoản, mật khẩu và xác nhận mật khẩu.
- /demo/doi: thông tin đội của tài khoản đã đăng nhập.
- /demo/quan-tri: admin mở/đóng đăng ký, xem số đội và xác nhận xóa đội demo.
- /main: trang thông báo giải chính chưa mở, không đọc dữ liệu demo để giả lập main.
- /docs: giao diện thử API vẫn giữ nguyên.

Không có trang khán giả ở giai đoạn này. Nộp Bot/thi đấu chưa có nút hành động;
chỉ có thông báo bước tiếp theo. Đăng ký đơn giản vẫn giới hạn mode DEMO.

## Đăng nhập và dữ liệu

Giao diện tự nhận token từ API rồi gửi Bearer trong các yêu cầu cần xác thực.
Không cần copy token vào Authorize như /docs. Token lưu sessionStorage của tab,
không lưu mật khẩu; đăng xuất xóa token ở tab hiện tại. Backend chưa hỗ trợ thu hồi
JWT khi logout; token đã sao chép vẫn có hiệu lực đến hạn nếu user còn active.
401 trên API bảo vệ đưa về đăng nhập. Token của /docs và frontend quản lý độc lập.

Dữ liệu trạng thái lấy thật từ backend, không hard-code số đội hoặc trạng thái.
Tự làm mới mỗi 15 giây khi tab hiện; các form không bị xóa dữ liệu đang nhập.
Lỗi tên trùng/đủ đội/đóng đăng ký và lỗi kết nối được hiển thị. Các thao tác ghi
có khóa nút khi xử lý; API vẫn là nơi kiểm soát quyền, thời hạn và giới hạn đội.
Tên đội trong HTML được escape; không dùng dữ liệu user làm mã HTML thực thi.

Xóa đội có hộp xác nhận, dựa trên API lưu trữ mềm hiện có. Chỉ xóa trước nộp bài.
Không có reset toàn bộ giải. Admin không tạo bằng form đăng ký, dùng create_admin.

## Kiểm thử giao diện riêng

`python -m tests.frontend.preview_server` mở http://127.0.0.1:8001/demo với dữ liệu
SQLite trong bộ nhớ riêng và tài khoản giả preview-admin / preview-password-only.
Không đọc .env, không kết nối MySQL, không ghi dữ liệu vào giải của bạn.
Tắt server là mất dữ liệu thử; đây không phải chế độ backend dùng khi trình bày.

Tình huống nên thử trên demo thật: đăng nhập đúng/sai, đăng ký khi đóng/mở,
xác nhận mật khẩu không khớp, trùng tên/đủ đội, đúng vai trò, xóa đội và đăng ký
lại, logout, reload đường dẫn con. Giữ database demo riêng vì các thao tác ghi
trên cổng 8000 dùng database thật được cấu hình.
