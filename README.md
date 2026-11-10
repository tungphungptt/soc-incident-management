
# SOC Incident Management System

Ứng dụng full-stack quản lý vận hành SOC, xây dựng dựa trên 14 bảng hiện có của `soc_incident_management`.

## Có gì trong project?

- **Backend:** FastAPI + SQLAlchemy 2 + MySQL 8 + JWT.
- **Frontend:** React + TypeScript + Vite, giao diện dark SOC bằng tiếng Việt.
- **Dashboard:** số lượng sự cố, cảnh báo, nhân viên SOC, tài sản, IOC, tổ chức — truy vấn trực tiếp MySQL.
- **14 module dữ liệu:** sự cố, cảnh báo, nhân viên, tổ chức, tài sản, IOC, MITRE ATT&CK và các bảng liên kết/lịch sử.
- **API:** CRUD dựa trên schema được reflect trực tiếp từ database; Swagger tại `/docs`.
- **An toàn dữ liệu:** không tự chạy seed, không DROP/ALTER bảng khi khởi động, không có lệnh import dữ liệu tự động.

> **Quan trọng:** `database-data.zip` có seed SQL, verification SQL, 18 business queries, README và script sinh dữ liệu; không có file CREATE TABLE/schema đầy đủ. Vì vậy backend đọc schema thật từ MySQL lúc chạy. Hãy đảm bảo database `soc_incident_management` đã được tạo và có đủ 14 bảng trước khi chạy app.

## 1. Cấu hình backend (Windows PowerShell)

**Bản nâng cấp bảy giao diện:** xem [hướng dẫn khu vực làm việc và API](docs/role-workspaces.md).
Trước khi chạy bản mới, từ `backend` thực hiện:

```powershell
.\.venv\Scripts\python.exe -m scripts.migrate_workspaces
```

Tạo đủ tài khoản và dữ liệu nghiệp vụ demo bằng lệnh seed ở mục 6 với tùy chọn
`--with-data`. Nếu đã có tài khoản, có thể chạy riêng
`.\.venv\Scripts\python.exe -m scripts.seed_demo_data` để giữ nguyên mật khẩu.

Mở PowerShell trong thư mục `backend`:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
```

Sửa `DATABASE_URL` trong `backend/.env`. Ví dụ nếu dùng tài khoản `root`:

```env
DATABASE_URL=mysql+pymysql://root:YOUR_URL_ENCODED_PASSWORD@127.0.0.1:3306/soc_incident_management?charset=utf8mb4
JWT_SECRET=replace-with-a-long-random-secret
ADMIN_USERNAME=admin
ADMIN_PASSWORD=Set-A-Strong-Local-Password
CORS_ORIGINS=http://localhost:5173
```

Nếu mật khẩu chứa ký tự đặc biệt (`@`, `:`, `/`, `#`...), URL-encode mật khẩu hoặc tạo một MySQL user riêng cho ứng dụng. Không commit file `.env`.

Chạy backend:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Kiểm tra:
- Health: http://127.0.0.1:8000/health
- Swagger: http://127.0.0.1:8000/docs

`/health` phải trả `{"status":"ok","database":"connected"}`.

## 2. Cấu hình frontend

Mở cửa sổ PowerShell thứ hai trong thư mục `frontend`:

```powershell
Copy-Item .env.example .env
npm install
npm run dev
```

Mở http://localhost:5173. Đăng nhập bằng username/password đã đặt trong `backend/.env`.

## 3. Deploy lên Render

Blueprint nằm ở `render.yaml` tại thư mục gốc repo, tạo một Docker web service cho backend và một static site cho frontend. Khi tạo Blueprint, nhập các biến được Render yêu cầu:

- `DATABASE_URL`: URL MySQL bên ngoài theo dạng `mysql+pymysql://USER:PASSWORD@HOST:PORT/soc_incident_management?charset=utf8mb4`. Render Blueprint không tạo MySQL managed tương thích với backend này; MySQL phải cho phép kết nối từ Render.
- `ADMIN_PASSWORD`: mật khẩu mạnh cho tài khoản SOC Manager.
- `CORS_ORIGINS`: origin của frontend sau khi deploy, ví dụ `https://soc-incident-frontend.onrender.com`.
- `VITE_API_BASE_URL`: URL backend, ví dụ `https://soc-incident-api.onrender.com/api/v1`.

Trước khi deploy, database phải được tạo sẵn và có đủ 14 bảng theo schema của ứng dụng. Backend health check cần database kết nối được. Không đưa mật khẩu hoặc thông tin kết nối vào Git.

## 4. Database và dữ liệu mẫu

1. Sao lưu database trước mọi thay đổi.
2. Tạo database/schema theo DDL hiện có nếu chưa có.
3. Nếu cần dữ liệu mẫu, đọc `database-data/seed_soc_incident_management.sql` trong ZIP nguồn và chạy có chủ đích trên database phù hợp.
4. Seed file ghi rõ chỉ INSERT và giả định schema đã tồn tại; nó không tạo bảng.
5. Không chạy seed lặp lại nếu dữ liệu đã có, vì có thể trùng khóa chính.
6. App không chạy seed hoặc migration khi khởi động.

## 5. Các endpoint chính

- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `GET /api/v1/meta/tables`
- `GET /api/v1/dashboard`
- `GET /api/v1/tables/{table_name}?page=1&page_size=20&search=...`
- `GET /api/v1/tables/{table_name}/{key}`
- `POST /api/v1/tables/{table_name}`
- `PUT /api/v1/tables/{table_name}/{key}`
- `DELETE /api/v1/tables/{table_name}/{key}`
- `GET /api/v1/reports/incident-summary`

All data endpoints require a Bearer token. The table API only permits the 14 allowlisted tables. SQLAlchemy parameterizes values and validates field names against reflected columns.

## 6. Important limitations / next implementation steps

The application now has seven role workspaces, persistent accounts, employee
identity links, transactional incident workflows, SLA clocks, reporting and
monthly compensation. See [role-workspaces.md](docs/role-workspaces.md) for the
complete permission matrix, migration, endpoints and verification evidence.

- Shared CRUD is for directories; incident mutations use dedicated workflow endpoints.
- Composite relationships are managed through assignment and link services.
- IOC identity is the composite pair `(LoaiIOC, GiaTriIOC)`, including incident foreign keys.
- Reports aggregate on the server; large deployments need query optimization.
- Alert ingestion, Wazuh/Elastic integration and real-time streaming remain outside this implementation.

## 7. Tests

### Bản sửa ràng buộc MySQL và 18 truy vấn

Từ `backend`, sau migration workspace, chạy:

```powershell
.\.venv\Scripts\python.exe -m scripts.migrate_business_rules
.\.venv\Scripts\python.exe -m scripts.verify_queries
$env:SOC_TEST_MYSQL = '1'
try {
    .\.venv\Scripts\python.exe -m pytest -q --disable-warnings -p no:cacheprovider
} finally {
    Remove-Item Env:SOC_TEST_MYSQL
}
```

Migration sao lưu dữ liệu/schema trước thay đổi vào `backend/migration_backups/`,
cập nhật thưởng, đổi khóa IOC và cài [sql/triggers.sql](sql/triggers.sql).
Dừng backend trong khi chạy DDL, sau đó khởi động lại để làm mới reflected schema.
Không DROP/TRUNCATE/reset dữ liệu. Các test MySQL dùng transaction rollback.
SQL thuần: [sql/queries.sql](sql/queries.sql). Kết quả và giải thích ràng buộc:
[docs/mysql-business-rules.md](docs/mysql-business-rules.md).

### Seed tài khoản demo cho 7 vai trò

Chạy thủ công từ thư mục `backend` (PowerShell):

```powershell
$env:DEMO_ACCOUNT_PASSWORD = 'Demo@12345'
try {
    .\.venv\Scripts\python.exe -m scripts.seed_demo_accounts
} finally {
    Remove-Item Env:DEMO_ACCOUNT_PASSWORD
}
```

Nếu không đặt biến môi trường, script hỏi mật khẩu và ẩn nội dung nhập.
Mật khẩu chỉ được lưu dưới dạng hash scrypt có salt bằng chính hàm dùng cho
Admin; không ghi mật khẩu vào file hay in ra log.

Script tạo đúng một tài khoản demo cho mỗi vai trò hiện có:
`admin_demo`, `soc_manager`, `analyst_l1`, `analyst_l2`, `analyst_l3`,
`incident_responder`, `threat_hunter`. Tất cả ở trạng thái active.
Chạy lại sẽ đặt lại vai trò, mật khẩu và active cho đúng bảy username trên,
không tạo trùng hoặc thay đổi tài khoản `admin` và tài khoản khác.
Kho tài khoản là `backend/accounts.sqlite3`; script không thay đổi dữ liệu MySQL.
Script in bảng `username | role | status` sau khi hoàn tất.

Thêm `--with-data` vào lệnh seed để tạo cả 40 Incident, quan hệ nghiệp vụ,
profile và lương/chính sách thưởng demo. Lựa chọn này cũng chạy migration cần thiết.

Mở http://127.0.0.1:5173/, đăng xuất rồi đăng nhập bằng từng username với
mật khẩu đã chọn. `admin_demo` mở quản lý tài khoản; các vai trò nghiệp vụ
mở dashboard và menu tương ứng. Chi tiết quyền: [docs/roles.md](docs/roles.md).

From `backend`:

```powershell
pytest
```

## Directory structure

```text
backend/    FastAPI application
frontend/   React + TypeScript web application
docs/       architecture and data mapping notes
database-data/  source SQL and seed documentation from the supplied ZIP
```
=======
# soc-incident-management
