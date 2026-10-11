# Thay đổi cấu trúc database

`schema.sql` là baseline `0001_initial`, dùng cho database trống.
Không chạy lại schema để cập nhật database đang có dữ liệu.

Các thay đổi sau này được đặt tên `0002_<noi_dung>.sql`, `0003_<noi_dung>.sql`.
Mỗi migration chạy theo thứ tự trên cả bt3_demo và bt3_main, chọn đúng database
trước khi chạy, và chỉ ghi phiên bản vào schema_migrations sau khi thành công.
Không có migration giả hoặc migration lặp lại baseline ở đây.

Trước khi đổi schema: sao lưu, thử trên bản sao, kiểm tra dữ liệu, rồi mới áp dụng.
MySQL DDL có thể tự commit; không giả định ROLLBACK hoàn tác ALTER TABLE.
Chưa có trình chạy migration tự động; sẽ bổ sung cùng backend khi cần.
