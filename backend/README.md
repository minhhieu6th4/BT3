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
