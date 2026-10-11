# Kiểm chứng

Ngày kiểm tra: 11/10/2026.

- Kiểm tra tĩnh 17 bảng và 28 khóa ngoại: thứ tự tạo bảng,
  tên bảng/cột tham chiếu; schema không có lệnh DROP.
- Đối chiếu định dạng GameState và Move với mã game hiện có.
- Kiểm tra file và khoảng trắng; chỉ thêm thư mục database.
- Chưa chạy schema/seed trên MySQL Server. Có MySQL CLI 8.0.46 và mysqld,
  nhưng khởi tạo server tạm ở thư mục riêng bị từ chối quyền truy cập,
  kể cả sau khi thử với quyền bổ sung. Không truy cập database hiện có.

Chưa xác nhận thực thi DDL/seed hoặc hành vi ràng buộc trên server.
Khi có MySQL thử nghiệm, chạy schema/seed và kiểm tra:

1. Có 17 bảng, baseline 0001_initial; demo có A/B, chưa có đội.
2. Tên đăng nhập/tên đội trùng bị từ chối; giới hạn 6 cần backend khóa transaction.
3. Một sinh viên không thuộc hai đội trong cùng giải.
4. Đội khác giải không gắn được vào bảng/Match.
5. Bài chọn thuộc đúng đội; Game không dùng bài của đội khác.
6. Winner ngoài Match/Game bị từ chối; DRAW không có winner.
7. Một số ván chỉ có một lần chạy chính thức; vẫn giữ lần chạy lại.
8. Không công bố vòng chưa COMPLETED; API phải ngăn dữ liệu kín.

Kiểm tra backend chưa thể chạy vì backend chưa được xây dựng.
