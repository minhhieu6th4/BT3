# Quan hệ dữ liệu BT3

```mermaid
erDiagram
    users ||--o{ teams : owns
    users ||--o{ team_members : joins
    users ||--o{ email_verifications : verifies
    competitions ||--o{ teams : registers
    teams ||--o{ team_members : includes
    teams ||--o{ submissions : submits
    users ||--o{ submissions : uploads
    teams ||--o| selected_submissions : locks
    submissions ||--o| selected_submissions : selected
    competitions ||--o{ rounds : contains
    rule_sets o|--o{ rounds : default_rule
    rounds ||--o{ tournament_groups : contains
    tournament_groups ||--o{ group_teams : includes
    teams ||--o{ group_teams : assigned
    rounds ||--o{ matches : contains
    tournament_groups o|--o{ matches : groups
    matches ||--o{ games : contains
    submissions ||--o{ games : bot_A
    submissions ||--o{ games : bot_B
    rule_sets ||--o{ games : governs
    games ||--o{ moves : records
    group_teams ||--o| rankings : snapshot
    competitions o|--o{ audit_logs : records
    users o|--o{ audit_logs : acts
```

Sơ đồ lược bớt các khóa ngoại đội A/B và winner để dễ đọc; schema.sql là đặc tả
chính xác của các cột và ràng buộc. Một đầu có thể chưa có bản ghi ở đầu nhiều,
ví dụ một Match PENDING chưa có Game. Knockout không cần Group.

Các khóa ghép bảo vệ quan hệ cùng giải, cùng vòng, cùng đội: không gắn một đội
của giải khác vào bảng/trận và không gắn Bot của đội khác vào Game. Hai màu có
thể đổi giữa các ván, còn team_a/team_b của Match cố định.

Tên đăng nhập duy nhất toàn database; tên đội duy nhất theo giải. student_code
và school_email duy nhất nếu có, nhưng việc xác minh danh tính là trách nhiệm
backend cùng quy trình của ban tổ chức. Thông tin xác nhận email chưa chứng minh
sinh viên đã đồng ý tham gia đội.
