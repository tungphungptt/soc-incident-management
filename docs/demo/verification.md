# Kiểm chứng 6 mục sửa demo — 10/11/2026

Nhánh `draft/demo-hardening-20261110`, không push. Một commit snapshot nền giữ
các thay đổi sẵn có; sáu commit WIP sau đó tách riêng từng mục. Không sửa `.env`.
Toàn bộ MySQL kiểm chứng chỉ dùng `soc_schema_test`.

## Thay đổi và kiểm thử

| Mục | File chính | Kết quả |
|---|---|---|
| 1 | `backend/app/read_scope.py`, `main.py`, `workspaces.py`, `backend/tests/test_read_scope.py` | 39 test quyền/workflow đạt; kiểm tra trong/ngoài phân công, dữ liệu con, IOC dùng chung và thu hồi quyền |
| 2 | `backend/scripts/seed_demo_accounts.py`, `demo_safety.py`, `backend/app/accounts.py`, test seed | 20 test seed/quyền đạt; tự liên kết 7 tài khoản, giữ liên kết hợp lệ; seed chạy hai lần mỗi vòng E2E |
| 3 | `backend/scripts/seed_demo_salaries.py`, `backend/tests/test_seed_demo_salaries.py` | 6 test seed đạt; 7 mức lương 10/2026; không thêm trùng/ghi đè lương đã cấu hình |
| 4 | `frontend/src/workspace/layouts.tsx` | Sửa `Lo?i` thành `Loại`; TS/TSX/CSS đọc strict UTF-8; TypeScript và Vite build đạt |
| 5 | `docs/roles.md`, `docs/role-workspaces.md` | Bỏ chính sách đọc vụ ngoài phân công chỉ vì cùng IOC, mô tả đúng quyền CRUD/workflow/thu nhập |
| 6 | `docs/demo/reset_demo.py`, README, test guard | 13 test guard đạt; dựng lại MySQL thực tế hai lần theo đúng thứ tự |

## E2E thực tế sau từng mục

| Mục | Yêu cầu API | Lượt trang Chrome | Bước workflow bằng form | Kết quả |
|---|---:|---:|---:|---|
| 1 | 309 | 36 | 11 | PASS |
| 2 | 309 | 36 | 11 | PASS |
| 3 | 310 | 36 | 11 | PASS |
| 4 | 310 | 36 | 11 | PASS |
| 5 | 310 | 36 | 11 | PASS |
| 6 | 310 | 36 | 11 | PASS |

Tổng **1.858 yêu cầu API, 216 lượt trang**. Mỗi vòng có 7 vai trò đăng nhập,
không có 5xx, trạng thái khác kỳ vọng hoặc ngoại lệ JavaScript của ứng dụng.
Các 4xx có chủ đích được đối chiếu: ngoài quyền/phân công, thiếu chuyên gia,
đóng khi chưa có hành động, phân công trùng.

HTTP thật tới Uvicorn cổng 8011; Chrome vào Vite cổng 5181. Mỗi vòng khởi động
backend mới để nạp code mới rồi dừng sau kiểm thử. Kho tài khoản tách biệt;
vòng cuối dùng đúng SQLite do reset tạo. Browser chọn case được giao từ API
cho L2/Responder, còn API kiểm tra 403 ngoài phân công.

Luồng form: L1 tạo HIGH → INVESTIGATING → chuyển L2 → Collect Evidence → chuyển
L3 → cập nhật phân tích → CONTAINED → chuyển Responder → Isolate Host →
REMEDIATING → CLOSED. Ngoài ra kiểm tra Critical thiếu/sai/đúng chuyên gia,
lương cá nhân, quyền cấu hình lương và chặn sửa trạng thái qua CRUD chung.

Có một lần automation vòng 5 bị race lúc tải lại trang đăng nhập. Bộ chạy
ngoài repo đã được sửa để chờ `Page.loadEventFired`; chạy lại toàn vòng đạt.
Không sửa logic đăng nhập của ứng dụng để vượt test.

## Kiểm tra cuối

- Toàn bộ backend: **59 passed, 13 skipped**. Các test MySQL opt-in được bỏ
  qua ở lượt unit SQLite, không kết nối database dự án.
- MySQL opt-in riêng trên `soc_schema_test`: **13 passed**; fixture rollback
  các dữ liệu thử.
- TypeScript noEmit và Vite build đạt. Output đặt ngoài repo để không thay
  artifact build sẵn có.
- `soc_incident_management` bị từ chối trước kết nối. Database thử đã tồn tại
  nhưng thiếu `--reset-existing` cũng bị từ chối.
- Reset có cờ dựng lại `soc_schema_test` hai lần thành công; ngay sau mỗi reset:
  **150 sự cố, 7 profile, 7 dòng lương 10/2026**. E2E sau đó thêm các vụ `[E2E]`.
- Chỉ DROP/CREATE `soc_schema_test` trong lượt reset được yêu cầu. Không DROP
  hoặc kết nối database dự án; không push.

## Liên kết sau reset

| Tài khoản | Vai trò | Nhân viên | Lương demo 10/2026 |
|---|---|---|---:|
| admin_demo | ADMIN | NV002 | 12.000.000 |
| soc_manager | SOC_MANAGER | NV001 | 25.000.000 |
| analyst_l1 | SOC_L1 | NV025 | 12.000.000 |
| analyst_l2 | SOC_L2 | NV007 | 18.000.000 |
| analyst_l3 | SOC_L3 | NV004 | 23.000.000 |
| incident_responder | INCIDENT_RESPONDER | NV015 | 17.000.000 |
| threat_hunter | THREAT_HUNTER | NV021 | 19.000.000 |

Mã được chọn từ bằng chứng phân công trong seed và giữ ổn định khi chạy lại.
Với dữ liệu khác, mã có thể khác. Admin không có quyền nghiệp vụ chỉ vì có profile.
Các mức lương là dữ liệu mô phỏng công khai, không phải lương thực tế.

## Bằng chứng và tái chạy

- `D:/Database/soc-hardening-test/item1_api_results.json` đến
  `item6_api_results.json`: từng request và HTTP.
- `item1_browser_results.json` đến `item6_browser_results.json` cùng thư mục:
  route, mạng, các mutation bằng form và runtime errors.
- Các log `itemN_api.log`, `itemN_browser.log`, `itemN_server.log`;
  `item6_reset.log` ghi trình tự reset.
- Bộ chạy local: `D:/Database/soc-hardening-test/run_round.py <1..6>`.
  Script và token thử nằm ngoài Git; không dùng mật khẩu MySQL làm mật khẩu demo.
- Ảnh tại `D:/Database/soc-hardening-test/screenshots/`.
- Hướng dẫn reset được commit: [README.md](README.md).

Database thử được giữ lại. Phân quyền theo nhân viên nằm ở lớp API, không phải
MySQL GRANT. CLOSED vẫn đọc được nếu hàng phân công còn tồn tại; schema chưa
có cột kết thúc phân công.
