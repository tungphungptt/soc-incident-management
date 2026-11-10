# Kết quả kiểm tra tài khoản demo

Đây là kết quả trước nâng cấp workspace. Kết quả hiện tại và ảnh giao diện:
[role-workspaces.md](role-workspaces.md).

Ngày kiểm tra: 10/11/2026.

Script: `backend/scripts/seed_demo_accounts.py`.
Mật khẩu demo dùng khi chạy: `Demo@12345` (giá trị hướng dẫn đăng nhập;
trong SQLite chỉ có hash scrypt có salt, dùng cùng hàm `password_hash` với Admin).

Đã chạy seed hai lần trên kho tài khoản hiện tại. Mỗi username demo có đúng
một dòng, tất cả active, mỗi vai trò có đúng một tài khoản **demo**. Admin thật
vẫn tồn tại ngoài bảy tài khoản demo; toàn bộ bản ghi `admin`, bao gồm hash
mật khẩu, được so sánh trước/sau và giữ nguyên. Bộ test còn kiểm tra chạy lại
với mật khẩu mới, sửa vai trò sai và mở khóa tài khoản demo.

## Kết quả từng vai trò

Tất cả các dòng bên dưới: đăng nhập API 200, `/auth/me` đúng vai trò và active,
metadata đúng bảng và quyền, dashboard 200, đọc được mọi bảng được cấp quyền.
Đã kiểm tra DOM trong Chrome headless qua giao diện Vite tại
`http://127.0.0.1:5173/`, không có error banner/error box.

| Username | Vai trò | Trạng thái | Menu thực tế (gồm Tổng quan) | Dashboard | Bảng đọc được | API từ chối đúng quyền |
|---|---|---|---:|---|---:|---:|
| admin_demo | ADMIN | active | 1 | Quản lý tài khoản, danh sách 8 tài khoản | 0 | 56 |
| soc_manager | SOC_MANAGER | active | 11 | 6 thẻ số liệu | 14 | 0 (toàn quyền nghiệp vụ) |
| analyst_l1 | SOC_L1 | active | 6 | 4 thẻ số liệu | 6 | 46 |
| analyst_l2 | SOC_L2 | active | 8 | 4 thẻ số liệu | 11 | 37 |
| analyst_l3 | SOC_L3 | active | 8 | 4 thẻ số liệu | 11 | 33 |
| incident_responder | INCIDENT_RESPONDER | active | 7 | 4 thẻ số liệu | 8 | 44 |
| threat_hunter | THREAT_HUNTER | active | 6 | 4 thẻ số liệu | 9 | 39 |

API kiểm tra qua proxy frontend `/api/v1`, không chỉ gọi trực tiếp backend.
Tổng cộng 255 yêu cầu không được cấp quyền đều trả 403. Chỉ Admin được đọc
danh sách tài khoản; sáu vai trò nghiệp vụ đều bị từ chối API tài khoản.

Các API tạo/sửa được cấp quyền được thử bằng trường không tồn tại: trả lỗi
validation 422 (hoặc 400 khi bảng có khóa ghép), xác nhận đi qua lớp kiểm tra
quyền mà không ghi dữ liệu nghiệp vụ. Không thực hiện thao tác tạo/sửa/xóa
dữ liệu MySQL thật. Quyền chi tiết xem [roles.md](roles.md).

Trình tự menu ưu tiên đã được kiểm tra:

- L1: Cảnh báo → Quản lý sự cố.
- L2: Quản lý sự cố → IOC → Hành động xử lý.
- L3: Quản lý sự cố → MITRE ATT&CK → IOC.
- Incident Responder: Hành động xử lý → Quản lý sự cố → Tài sản.
- Threat Hunter: IOC → MITRE ATT&CK → Quản lý sự cố.
- Manager: đủ các mục quản lý nghiệp vụ, nhân viên, tổ chức và phân công.
- Admin: màn hình quản lý tài khoản, không có menu nghiệp vụ.

Chạy từ `backend`: `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider`:
**12 passed**. Có cảnh báo deprecation sẵn có từ FastAPI/Starlette.

Giới hạn hiện tại: phân quyền theo bảng/chức năng, chưa lọc dòng theo người
được giao sự cố; bảng khóa ghép chưa hỗ trợ sửa/xóa trên giao diện. Không có
dữ liệu nghiệp vụ nên không kiểm tra trực quan nút sửa/xóa trên dòng dữ liệu;
quyền tương ứng được xác nhận qua metadata và các yêu cầu API bị từ chối.
