# Cập nhật nộp Bot và hẹn giờ

Backend hiện yêu cầu schema `0002_submission_windows`. Database đã tạo trước đó:
trong DBeaver, dùng kết nối root/quản trị, chọn BT3_Schema1 rồi chạy một lần
`database/migrations/0002_submission_windows.sql`. Không chạy lại schema/seed.
Tài khoản ứng dụng hiện có không cần quyền ALTER; quyền này chỉ dùng khi nâng schema.
Nếu chạy migration lỗi, dừng và kiểm tra, không chạy lại toàn bộ vì DDL tự commit.

Cài `python -m pip install -r requirements.txt` trong .venv, khởi động lại backend.
/api/health trả schema 0002_submission_windows khi sẵn sàng. Thiếu migration sẽ
báo lỗi cập nhật dữ liệu; backend không tự sửa database khi khởi động.

## API mới

- POST /api/submissions: multipart/form-data, đúng một trường file với tên file
  student_bot.py; chỉ TEAM là chủ đội REGISTERED/APPROVED trong giải được chọn.
- GET /api/submissions/me: lịch sử riêng của đội theo phiên bản mới nhất trước.
- PUT /api/admin/submission: điều khiển cửa nộp Bot.
- PUT /api/admin/registration: vẫn giữ đường dẫn, dùng cùng định dạng điều khiển.

Thủ công: `{"mode":"MANUAL","open":true}` hoặc false (mode có thể bỏ qua).
Hẹn giờ: `{"mode":"SCHEDULED","opens_at":"2026-10-12T09:00:00+07:00",
"closes_at":"2026-10-12T14:00:00+07:00"}`. Đây là ví dụ, cần chọn lịch thực tế.
Mốc thời gian API bắt buộc có múi giờ. Chỉ một cửa được mở tại một thời điểm.
Admin có thể mở lại khi cửa kia đóng. Hai lịch không được chồng nhau; lịch nối
liền (đóng đăng ký đúng lúc mở nộp bài) được phép. Thao tác thủ công xóa lịch của
đúng cửa đó. Giữ nguyên ck_open_phases trong MySQL. Cửa mở thủ công được coi là
chưa có thời điểm đóng, nên phải đóng hoặc hẹn giờ đóng trước khi đặt lịch cửa kia.

Lịch lưu MySQL, trạng thái hiệu lực được tính bằng đồng hồ UTC máy chủ ở mỗi
request: opens_at <= now < closes_at. Không cần cron hoặc browser luôn mở.
Hai cột *_open lưu lựa chọn thủ công, không tự thay đổi theo giờ ở chế độ SCHEDULED;
đọc API để biết trạng thái hiệu lực thay vì chỉ đọc hai cột đó trong DBeaver.
UI cập nhật khoảng 15 giây; backend kiểm tra hạn ở lúc nhận đủ file và có khóa
transaction, nên UI chưa kịp cập nhật cũng không thể nộp quá hạn.

Mặc định file tối đa 1 MiB, đúng tên student_bot.py, văn bản UTF-8 không rỗng và
không chứa NUL. Chưa kiểm tra cú pháp/API Bot/import ở đây; bài luôn PENDING và
chưa chọn phiên bản thi đấu. Không import/exec hoặc chạy file đã nộp trên host.

File lưu dưới storage/submissions với tên UUID .py, SHA-256 và dung lượng ghi vào
MySQL. source_file_path là tên tương đối so với SUBMISSION_DIR. Thư mục riêng,
không phục vụ qua /assets; API không trả đường dẫn hoặc mã nguồn đội khác.
MAX_SUBMISSION_BYTES và SUBMISSION_DIR có thể đặt trong .env nếu cần thay mặc định.
Storage cần giữ cùng bản sao database; các file này được Git bỏ qua.

Nếu nhận file thất bại thì không ghi phiên bản; nếu SQL thất bại thì rollback và
xóa file vừa tạo. Xử lý sự cố đột ngột giữa filesystem/DB vẫn cần kiểm tra file mồ
côi khi vận hành; filesystem không có transaction chung với MySQL.

Admin chỉ xóa đội demo chưa có bài nộp và chưa thi đấu, giữ lịch sử đã nộp.
Các mô tả bên dưới về khóa đăng ký theo giai đoạn/lịch cũ được thay bằng quy tắc
chỉ mở một cửa ở phần cập nhật này. Chưa triển khai Judge/chọn Bot cuối/Tournament.

---

# Backend BT3 giai đoạn 1

Đã thực hiện hai bước đầu: FastAPI kết nối MySQL; đăng nhập/phân quyền và đăng ký
đội với quản trị viên mở/đóng đăng ký. Dùng schema đã có, không tạo/xóa bảng lúc
khởi động. Chưa có frontend; thử API bằng trang /docs hoặc Postman.

## 1. Tạo tài khoản MySQL cho ứng dụng

Trong DBeaver, dùng kết nối có quyền quản trị MySQL hiện tại. Mở bản mẫu
`database/create_backend_user.sql.example`, thay mật khẩu mẫu bằng mật khẩu riêng
rồi chạy. Không lưu/commit bản có mật khẩu thật. Nếu CREATE USER báo thiếu quyền,
nhờ người quản lý MySQL tạo tài khoản hoặc kiểm tra tài khoản kết nối DBeaver.
Nếu tài khoản đã tồn tại, không chạy lại CREATE USER; kiểm tra quyền của nó.

Tài khoản `bt3_app` kết nối database, không phải admin website. Chỉ cần quyền
SELECT/INSERT/UPDATE trên BT3_Schema1; quyền tạo bảng dành cho người triển khai SQL.

## 2. Chuẩn bị cấu hình và thư viện

Chạy từ thư mục gốc BT3 trong terminal:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
cp .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Nếu .venv đã có, chỉ cần kích hoạt rồi cài thư viện. requirements.txt dành cho
chạy ứng dụng, requirements-dev.txt thêm thư viện kiểm thử.

Điền trong `.env`:

- DB_NAME=BT3_Schema1, DB_HOST=localhost, DB_PORT=3306.
- DB_USER=bt3_app và DB_PASSWORD là mật khẩu vừa đặt. Với ký tự # hoặc khoảng
  trắng, đặt giá trị mật khẩu trong dấu nháy kép theo định dạng dotenv.
- JWT_SECRET là chuỗi ngẫu nhiên từ lệnh trên, không dùng giá trị mẫu.
- COMPETITION_CODE=demo, tương ứng dữ liệu seed đã nạp.

.env và .venv đã được bỏ qua bởi Git. Không đưa mật khẩu vào câu lệnh terminal.

## 3. Tạo admin website và chạy backend

```bash
python -m backend.create_admin
python -m uvicorn backend.main:create_app --factory --reload --host 127.0.0.1 --port 8000
```

Lệnh tạo admin hỏi tên và mật khẩu (mật khẩu không hiển thị khi nhập), băm Argon2id
trước khi lưu; không ghi đè hoặc nâng quyền tài khoản đã có. Tạo admin là thao tác
cục bộ, không có API công khai cho phép đăng ký ADMIN.

Mở http://127.0.0.1:8000/docs trong trình duyệt. /api/health kiểm tra kết nối và
baseline 0001_initial; /api/competition xác nhận giải demo tồn tại.

## 4. Thử luồng chính qua /docs

1. POST /api/auth/login → Try it out, nhập username/password của admin rồi Execute.
2. Copy access_token. Bấm Authorize ở đầu trang, dán token (không thêm chữ Bearer).
3. PUT /api/admin/registration với `{"open": true}`. Chỉ admin được gọi.
4. POST /api/teams với `{"username": "team01", "password": "a-private-password"}`.
   Đây chỉ là ví dụ; dùng mật khẩu riêng. Thành công trả HTTP 201, tạo một user
   TEAM và một team cùng tên, không trả mật khẩu/hash. Không tự đăng nhập.
5. POST /api/auth/login bằng tài khoản đội. Trong Authorize thay token admin bằng
   token đội; GET /api/auth/me và /api/teams/me phải trả đúng tài khoản/đội.
6. Với token đội, thử PUT /api/admin/registration phải nhận 403.
7. Đăng nhập admin lại và thay token; PUT với `{"open": false}`. Đăng ký đội mới
   phải nhận 409. GET /api/competition hiển thị trạng thái đóng.

Sau đó có thể mở lại đăng ký trong cùng giai đoạn để thử đủ 6 đội. Đội thứ 7 bị
409; tên trùng (không phân biệt hoa/thường) bị 409. Các thử này ghi dữ liệu thật
vào database demo: không cần reset để chứng minh, và chưa có chức năng reset.

## API đã có

| API | Quyền | Mục đích |
|---|---|---|
| GET /api/health | Công khai | Kiểm tra MySQL và baseline |
| GET /api/competition | Công khai | Trạng thái giải, số đội, khả năng đăng ký |
| POST /api/teams | Công khai khi mở đăng ký | Tạo tài khoản và đội demo |
| GET /api/teams | Công khai | Danh sách đội, không có mật khẩu/hồ sơ |
| POST /api/auth/login | Công khai | Nhận Bearer JWT, mặc định 30 phút |
| GET /api/auth/me | Đã đăng nhập | Thông tin tài khoản |
| GET /api/teams/me | Chủ đội | Đội của tài khoản trong giải đang chọn |
| PUT /api/admin/registration | ADMIN | Mở/đóng đăng ký |

Quy ước hiện tại: username 3–64 ký tự a-z/0-9/_/-, được chuyển chữ thường; tên đội
bằng username. Password 8–128 ký tự. Đây là lựa chọn triển khai MVP có thể thay đổi.
Không cho người đăng ký chọn role/owner/status. Đếm đội chưa WITHDRAWN để giữ
suất; admin có API xóa đội demo trước giai đoạn nộp bài. Chưa triển khai đăng ký sinh viên của bản đầy đủ.
Cấu hình DB và giới hạn đội vẫn dùng chung; API TEAM đăng ký hiện dành cho demo.

Nếu lịch registration_opens_at/closes_at có giá trị, phải thỏa lịch UTC bên cạnh
cờ mở/đóng. Seed demo để lịch trống nên admin thao tác bất cứ lúc nào trong giai
đoạn DRAFT/REGISTRATION. Chưa có API đặt lịch. Sau CODING không được mở lại đăng ký.
Không tự chuyển sang CODING khi đóng, để admin có thể mở lại trước bước nộp bài.

## Kiến trúc và bảo vệ dữ liệu

routers nhận request và trả response → services kiểm tra quy tắc/giao dịch →
models/tables mô tả cột → database/connection truy cập MySQL.

Registration và admin control cùng khóa hàng competition (SELECT FOR UPDATE)
trong transaction. Hai đăng ký đồng thời không thể cùng chiếm suất cuối; user,
team và audit log cùng commit/rollback. SQL dùng tham số, không nối chuỗi từ input.

Mỗi request có token kiểm tra tài khoản còn active và quyền hiện tại trong DB.
JWT được ký, không mã hóa; không chứa mật khẩu. Chưa có logout thu hồi token hoặc
refresh token: frontend bỏ token khi thoát, token cũ tự hết hạn. Chưa có rate limit
đăng nhập; bản hiện tại dùng cho demo cục bộ. Trước khi công khai cần bổ sung giới
hạn thử đăng nhập và HTTPS. Không chạy Bot, không nhập/xuất kết quả thi đấu.

Lỗi dữ liệu trả HTTP 503 không lộ credential; lỗi input 422 không phản chiếu password.
Đăng ký đóng/đủ đội/trùng tên là 409; sai đăng nhập là 401; sai quyền là 403.

## Kiểm thử

```bash
python -m pytest -q
```

Test API dùng SQLite riêng trong bộ nhớ để kiểm tra luồng và rollback, không
kết nối hoặc xóa BT3_Schema1. SQLite chỉ dành cho test; backend thực tế dùng MySQL.
SQLite không chứng minh khóa hàng/đăng ký đồng thời của MySQL. Xem
`tests/backend/README.md` để biết giới hạn và kiểm thử MySQL tùy chọn.

Không cần chạy lại schema.sql hoặc seed_demo.sql để sử dụng backend này.

## Xóa đội để thử lại demo

ADMIN gọi `DELETE /api/admin/teams/{team_id}` trong /docs, lấy ID từ GET /api/teams.
Chỉ áp dụng cho giải DEMO ở DRAFT/REGISTRATION và chưa mở nộp bài. Đội bị loại khỏi
list/count, tài khoản cũ bị vô hiệu hóa (token cũ cũng bị từ chối), tên được giải
phóng để đăng ký lại với ID mới. Không tự mở lại đăng ký.

Đây là xóa khỏi demo bằng lưu trữ mềm: giữ bản ghi và audit log để không phá khóa
ngoại, đổi tên lưu trữ và đánh dấu WITHDRAWN. Không cần quyền DELETE của MySQL hay
đổi schema; SELECT/INSERT/UPDATE hiện có là đủ. Chưa reset cả giải/kết quả thi đấu.

## Giao diện demo

Mở http://127.0.0.1:8000/demo, đăng nhập trực tiếp bằng tài khoản website.
Không cần Authorize/copy token; xem frontend/README.md. /docs vẫn dùng để thử API.
