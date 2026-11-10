# Dựng lại demo MySQL 8.0

Dùng MySQL cài trên máy và Python trong virtualenv backend. Không dùng Docker.
Script không sửa `.env`, code hay database dự án. Trong đợt kiểm chứng này chỉ
chạy trên `soc_schema_test`.

## Kiểm tra trước khi chạy

```powershell
backend\.venv\Scripts\python.exe -B docs/demo/reset_demo.py --database soc_schema_test --dry-run
```

Tên phải chỉ gồm chữ/số/gạch dưới và chứa `test` hoặc `demo` (không phân biệt
hoa thường). `soc_incident_management` luôn bị từ chối trước khi kết nối.

## Tạo mới

```powershell
backend\.venv\Scripts\python.exe -B docs/demo/reset_demo.py --database soc_schema_test
```

Host/port/user/mật khẩu lấy từ `DATABASE_URL` của môi trường hoặc
`backend/.env`; chỉ tên database được thay bằng đối số đã kiểm tra. Nếu không
có URL thì báo lỗi, không đoán thông tin đăng nhập. Mật khẩu 7 tài khoản demo
được hỏi bằng getpass hoặc lấy từ biến tạm `DEMO_ACCOUNT_PASSWORD`.

Nếu database hoặc kho tài khoản demo đã tồn tại, script dừng. Muốn dựng lại từ
đầu, dừng backend đang dùng **database thử**, rồi chạy rõ cờ:

```powershell
backend\.venv\Scripts\python.exe -B docs/demo/reset_demo.py --database soc_schema_test --reset-existing
```

**Cờ này xóa database được chỉ định và kho SQLite demo riêng rồi dựng lại.**
Không có lệnh xóa database nào khác, không xóa thư mục đệ quy. Nếu một bước
thất bại, script dừng; dữ liệu demo có thể mới dựng một phần, chạy lại với cờ
trên sau khi xử lý lỗi. MySQL DDL không rollback toàn bộ quy trình.

## Thứ tự cố định

1. `docs/sql/02_schema_proposed.sql`: 18 bảng, chuyển USE sang target đã kiểm tra.
2. `docs/sql/03_seed_proposed.sql`: seed lịch sử, trước khi cài trigger workflow.
3. `scripts.migrate_workspaces`.
4. `scripts.migrate_business_rules` (trigger, view, chính sách thưởng).
5. `scripts.seed_demo_accounts`: in 7 tài khoản ↔ nhân viên, tự liên kết.
6. `scripts.seed_demo_salaries`: lương mô phỏng 7 nhân viên tháng 10/2026.

Hai script seed cũng tự từ chối database dự án. Chạy lại seed không thêm
profile/lương trùng; lương đã cấu hình được giữ nguyên. Seed tài khoản cập nhật
mật khẩu của đúng 7 tài khoản demo theo mật khẩu được cung cấp.

Nhân viên nghiệp vụ được chọn theo vai trò phân công có thật trong seed;
không hard-code một nhân viên chưa tồn tại. Admin được liên kết nhân viên riêng,
không được thêm quyền nghiệp vụ. Các mức lương là dữ liệu demo công khai trong
`seed_demo_salaries.py`, không phải lương thực tế.

## Chạy ứng dụng trên dữ liệu vừa dựng

Đặt tạm `DATABASE_URL` trỏ đúng target và `SOC_ACCOUNT_DB` theo đường dẫn script
in ra: mặc định `backend/migration_backups/demo_accounts/<target>/accounts.sqlite3`.
Không dùng kho `backend/accounts.sqlite3` của dự án. Thư mục migration_backups
đã được bỏ qua trong Git; mật khẩu và SQLite không được commit.

Khởi động backend từ `backend` với Uvicorn, frontend từ `frontend` với Vite.
Frontend dùng `/api/v1` qua proxy cổng 8000, hoặc `VITE_API_BASE_URL` tạm trỏ
backend kiểm thử. Chọn tháng **10/2026** để xem đủ dữ liệu seed/lương.

Unit test bảo vệ reset không kết nối MySQL:

```powershell
$env:DATABASE_URL = 'sqlite://'
backend\.venv\Scripts\python.exe -B -m pytest backend/tests/test_demo_reset_safety.py -q -p no:cacheprovider
```

Xem [phân quyền](../roles.md) và [khu vực làm việc](../role-workspaces.md).
