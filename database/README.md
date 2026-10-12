# Cập nhật schema 0002

Schema.sql vẫn là baseline 0001. Với database đang dùng: chạy
migrations/0002_submission_windows.sql bằng tài khoản MySQL quản trị, một lần.
Với database mới: schema.sql → migration 0002 → seed_demo.sql nếu là demo.
Không reset dữ liệu hoặc nạp lại seed khi cập nhật.

0002 GIỮ ck_open_phases, thêm registration_mode/submission_mode và
submissions.source_size_bytes. Backend chỉ cho một cửa mở tại một thời điểm và
từ chối lịch chồng nhau. Backend tính cửa đang mở từ mode và lịch theo giờ UTC, không dùng
status giải làm điều kiện khóa hai cửa. Các quy tắc cũ nói phải đóng đăng ký
trước khi nộp bài/mở lại bị cấm không còn áp dụng ở phiên bản này.

---

# Database BT3

Thiết kế dùng chung MySQL 8.0.16 trở lên (khuyến nghị MySQL 8.4), InnoDB.
Hai database `bt3_main` và `bt3_demo` tách dữ liệu nhưng có cùng cấu trúc.
Mốc thời gian lưu UTC; frontend chuyển sang giờ Việt Nam khi hiển thị.
Tên đăng nhập và tên đội dùng collation của database: không phân biệt hoa/thường
và dấu. Backend cần chuẩn hóa tên trước khi lưu; nếu muốn phân biệt dấu phải đổi
collation trước khi triển khai.

## File và cách khởi tạo

- `create_databases.sql`: tạo hai database rỗng nếu chưa tồn tại, không xóa dữ liệu.
- `schema.sql`: baseline 0001_initial, chạy một lần cho mỗi database trống.
- `seed_demo.sql`: tạo giải demo 6 đội, vòng bảng và hai bảng A/B; không tạo đội
  để giao diện đăng ký còn chỗ khi trình bày. Không chứa mật khẩu hay kết quả mẫu.
- `migrations/`: nơi lưu các thay đổi cấu trúc sau baseline.
- `erd.md`: sơ đồ và giải thích các quan hệ.
- `verify.sql`: truy vấn kiểm tra cấu trúc và seed, chỉ đọc dữ liệu.

Trong MySQL Workbench, mở kết nối rồi thực hiện:

1. Chạy create_databases.sql bằng tài khoản có quyền tạo database.
2. Chọn bt3_demo làm schema mặc định, chạy schema.sql.
3. Chạy seed_demo.sql. Không chạy seed lặp lại; trùng code sẽ báo lỗi.
4. Chọn bt3_main, chạy schema.sql. Không nạp seed_demo vào bản chính.
5. Chọn database muốn kiểm tra rồi chạy verify.sql.

Có thể dùng MySQL CLI từ thư mục gốc BT3:

```bash
mysql -u YOUR_DB_USER -p < database/create_databases.sql
mysql -u YOUR_DB_USER -p bt3_demo < database/schema.sql
mysql -u YOUR_DB_USER -p bt3_demo < database/seed_demo.sql
mysql -u YOUR_DB_USER -p bt3_main < database/schema.sql
mysql -u YOUR_DB_USER -p bt3_demo < database/verify.sql
```

Không có tài khoản đăng nhập website sẵn. Backend sẽ tạo admin với mật khẩu được
băm bằng thuật toán chuyên dụng. Tài khoản MySQL và tài khoản website khác nhau.
Tài khoản đội demo có account_type TEAM; tên đăng nhập đồng thời có thể được dùng
làm tên đội. Bản đầy đủ dùng STUDENT và team_members; thông tin sinh viên cho phép
NULL để demo không bắt buộc email/mã sinh viên. ADMIN không cần hồ sơ sinh viên.

## Dữ liệu chính

- users: tài khoản và hồ sơ; email_verifications: mã xác nhận đã băm, hạn dùng.
- competitions: giới hạn đội, trạng thái, cửa mở/đóng và lịch nếu có; format_config
  chứa cấu hình thể thức, chưa thay thế việc kiểm tra hoặc điều hành của backend.
- teams/team_members: đội và thành viên theo giải. Một tài khoản sở hữu tối đa
  một đội/giải; một sinh viên thuộc tối đa một đội/giải. Backend kiểm tra đội trưởng.
- submissions: mỗi lần nộp một phiên bản; chỉ lưu đường dẫn tương đối do backend
  quản lý và SHA-256 của file, không nhận đường dẫn tùy ý do người dùng cung cấp.
- selected_submissions: một bài được khóa cho mỗi đội, phải thuộc chính đội đó.
- rounds/tournament_groups/group_teams: vòng, bảng và danh sách đội trong bảng.
  Dùng tournament_groups để tránh tên GROUPS có thể xung đột từ khóa SQL.
- rule_sets: cấu hình luật có phiên bản; luật đã dùng phải bất biến.
- matches: các cặp đấu/các ô knockout, cho phép chưa xác định đủ đội; group_id
  NULL cho knockout. BYE biểu diễn việc đi tiếp khi không có đối thủ, không tạo
  Game giả cho BYE. BYE không tự quyết định quy tắc thiếu đội của demo.
- games: các ván và lần chạy lại; liên kết đúng hai đội của Match và bài của mỗi
  đội. red_team_id xác định màu; đội kia là BLUE. Một Game chính thức mỗi số ván.
- moves: nước đi JSON theo định dạng from/to hiện có, kèm thứ tự, lượt và màu.
  initial_state trong games dùng định dạng turn/team/board của GameState hiện có.
- rankings: snapshot Tournament tính, có thể tái tạo; không phải nguồn kết quả gốc.
- audit_logs: thay đổi trạng thái/công bố/chạy lại, không lưu mật khẩu hoặc token.

Database là nguồn chính cho kết quả và replay trong thiết kế này; match.json sẽ
được xuất từ đó. Chưa có chương trình nhập/xuất hoặc kết nối với engine hiện tại.
Tỷ số Match được tính từ các Game chính thức, không lưu thêm hai cột điểm có thể
mâu thuẫn. Backend/Tournament cập nhật kết quả Match và ranking cùng quy trình.

## Những ràng buộc cần backend thực hiện

Khóa ngoại và CHECK chỉ bảo vệ dữ liệu cục bộ, không thay cho quy tắc nghiệp vụ:

- Khi đăng ký, khóa bản ghi competition trong transaction, kiểm tra cửa/thời hạn
  và đếm đội trước khi thêm để hai yêu cầu đồng thời không vượt giới hạn 6.
- Chỉ ADMIN được mở/đóng và công bố; phải đóng đăng ký trước khi mở nộp bài.
  Các cờ mở/đóng là quyền cho phép; nếu có mốc thời gian, phải đồng thời thỏa lịch.
- Người nộp thuộc đội hoặc là chủ tài khoản đội, kiểm tra thời hạn nhận đủ file.
  Cấp số phiên bản trong transaction; xử lý unique conflict khi nộp đồng thời.
- Chọn bài phải VALID và đáp ứng quy tắc lựa chọn đã thống nhất. Khóa lựa chọn
  trước khi chạy, không sửa file Bot đã chọn. Không chạy Bot trên host.
- Lời mời thành viên và các trạng thái tạm phải có quy trình xác nhận; team_members
  dành cho chỗ đã được ghi danh, không phải danh sách lời mời chưa được xử lý.
- Match vòng bảng: hai đội thuộc cùng group; bảng thuộc vòng ROUND_ROBIN.
  Match knockout không có group. Người thắng phải có kết quả nhất quán.
- Game dùng Bot VALID đã được chọn, RuleSet phù hợp; ván hoàn tất cần có thời gian
  và trạng thái đầu đủ để replay. Không chỉ tin dữ liệu do frontend gửi.
- Một vòng COMPLETED khi đủ kết quả chính thức. published_at chỉ được ghi khi
  thực sự công bố, không dùng như lịch hẹn tương lai. API khán giả lọc theo nó.
- Sau khi công bố/chốt: hạn chế sửa; nếu chạy lại giữ attempt cũ và thay lựa chọn
  chính thức trong transaction. Không xóa lịch sử âm thầm.
- Cấu hình main (100 đội/10 bảng/Top32) sẽ được nạp khi chốt lịch, luật và tie-break.
  Chưa seed final BO/luật game hoặc quy tắc dưới 6 đội vì chúng chưa được xác nhận.

## Trạng thái kiểm tra

Xem VALIDATION.md để biết kiểm tra nào thực sự đã chạy. Script không tự khởi tạo
hay sửa database đang dùng trên máy. Chưa có reset demo hoặc tài khoản DB tự động;
những thao tác đó cần triển khai riêng với phạm vi rõ ràng.
