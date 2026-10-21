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

## 3. Database và dữ liệu mẫu

1. Sao lưu database trước mọi thay đổi.
2. Tạo database/schema theo DDL hiện có nếu chưa có.
3. Nếu cần dữ liệu mẫu, đọc `database-data/seed_soc_incident_management.sql` trong ZIP nguồn và chạy có chủ đích trên database phù hợp.
4. Seed file ghi rõ chỉ INSERT và giả định schema đã tồn tại; nó không tạo bảng.
5. Không chạy seed lặp lại nếu dữ liệu đã có, vì có thể trùng khóa chính.
6. App không chạy seed hoặc migration khi khởi động.

## 4. Các endpoint chính

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

## 5. Important limitations / next implementation steps

This first runnable version supplies real authentication, schema-aware CRUD, and live dashboard counts. It is a foundation, not a fully validated production SOC platform yet.

- The ZIP supplied for this build does not include complete DDL, so exact status/severity columns and foreign key details could not be statically validated here.
- Current authentication is a single environment-configured SOC Manager account. Employee login accounts, persistent roles, password reset, and per-role permission management require separate auth tables/migration.
- Generic CRUD does not yet implement a dedicated, transaction-safe incident lifecycle service that automatically writes `lich_su_trang_thai` and `hanh_dong_xu_ly`. Use these audit tables carefully until that workflow is implemented against the exact schema.
- Composite-primary-key tables are listable; generic edit/delete is disabled because a safe composite-key UI is not implemented.
- SLA targets, alert ingestion, Wazuh/Elastic integration, notifications, and real-time streaming are not represented as completed features.
- Before production, add dedicated integration tests against a disposable MySQL database, configure TLS/network restrictions, rotate secrets, use a least-privilege MySQL user, and implement authorization policies per action.

## 6. Tests

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
