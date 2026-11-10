# Báo cáo kiểm tra end-to-end — 10/11/2026

Kết luận: ứng dụng chạy được với MySQL soc_schema_test; 7/7 vai trò đăng nhập thành công. Luồng API và luồng form trên trình duyệt đều hoàn tất. Cần xử lý phạm vi đọc sự cố và chuẩn bị dữ liệu/liên kết tài khoản trước demo.

## Môi trường và phạm vi
- Backend FastAPI: http://127.0.0.1:8000; frontend Vite: http://127.0.0.1:5173. MySQL cài trên máy, database soc_schema_test.
- DATABASE_URL được thay trong môi trường tiến trình, lấy host/user/password từ backend/.env rồi chỉ đổi tên database. Không sửa .env, code ứng dụng hoặc database dự án; không commit.
- accounts.ACCOUNT_DB được trỏ tạm trong tiến trình đến D:/Database/soc-e2e-20261110/accounts.sqlite3. Không sửa accounts.py và không mở kho tài khoản dự án. Đây là điều chỉnh đường dẫn phục vụ cô lập kiểm thử, không thay đổi kiểm tra quyền.
- Gọi đúng hàm seed_demo_accounts trong backend/scripts/seed_demo_accounts.py để tạo 7 tài khoản, không dùng --with-data; không chạy lại migration/seed nghiệp vụ.
- Vì seed tài khoản không tạo profile, đã ghi nhận lỗi ban đầu, sau đó dùng PUT /workspace/profiles/{username} bằng Admin để liên kết 6 tài khoản nghiệp vụ với nhân viên có sẵn trong database thử.
- Liên kết: Manager NV001, L1 NV022, L2 NV006, L3 NV003, Responder NV015, Hunter NV019.
- Có thêm dữ liệu kiểm thử trong soc_schema_test: sự cố gắn [E2E], hành động/phân công/audit, IOC e2e-20261110.example, tổ chức E2ETC01, lương thử NV022 tháng 11. Không xóa seed gốc hoặc DROP database.

## Build và khởi động
- Backend khởi động thành công, Uvicorn báo Application startup complete; API thực tế phản hồi.
- TypeScript kiểm tra thành công với tsc --project tsconfig.json --noEmit --incremental --tsBuildInfoFile trỏ ngoài repo; Vite production build thành công, 1584 modules. Bundle JS khoảng 199.36 kB (gzip 61.77 kB). Output ở D:/Database/soc-e2e-20261110/frontend-dist.
- Không chạy nguyên npm run build để tránh ghi đè tsconfig.tsbuildinfo sẵn có; đã chạy các bước typecheck/build tương đương. Lần gọi ban đầu dùng --build cùng --tsBuildInfoFile bị TS5094 (sai tùy chọn của bộ kiểm thử), sau đó sửa lệnh và kiểm tra thành công; không phải lỗi mã TypeScript.
- Vite dev server khởi động thành công, strictPort 5173; VITE_API_BASE_URL=/api/v1 tạm thời, proxy tới backend 8000.
- Chrome headless chạy với profile riêng; môi trường Windows ban đầu lỗi GPU/sandbox, đã đổi cờ khởi động cho phiên headless thử. Sau đó không có lỗi JavaScript của ứng dụng.

## Độ bao phủ và giới hạn
- Bộ API chính: 309 yêu cầu, không có 5xx. Các 4xx bao gồm chặn quyền và kiểm tra dữ liệu có chủ đích; chi tiết trong api_results.json.
- Browser: 36 lượt mở trang, 30 tổ hợp route/vai trò cơ bản, 205 phản hồi API, 0 ngoại lệ JavaScript, không có phản hồi API 4xx/5xx trong các hành trình UI thành công.
- Thử form thật tạo sự cố, chuyển cấp qua bốn vai trò, thêm hành động, phân tích và đóng; không chỉ kiểm tra giao diện tĩnh.
- Các kiểm tra API là HTTP đến Uvicorn thật; không dùng TestClient hoặc mock backend. Không thử tải lớn, đồng thời, hay mọi tổ hợp nhập liệu sai.

## Màn hình và chức năng
| Màn hình/chức năng | Trạng thái | API và ghi chú |
|---|---|---|
| Đăng nhập `/` | chạy tốt | 7 vai trò qua form thật và POST /auth/login; GET /auth/me xác nhận danh tính |
| `/#/ADMIN/home` | chạy tốt | /accounts, /roles, /workspace/staff, /tables/nhan_vien_soc; không có số liệu tài khoản giả |
| `/#/ADMIN/to_chuc` | chạy tốt | /meta/tables + /tables/to_chuc, đã thử tạo/sửa tổ chức qua API |
| `/#/ADMIN/tai_san` | chạy tốt | API thật; màn danh mục và form hiển thị. Chưa thử hết create/update/delete tài sản |
| `/#/ADMIN/nhan_vien_soc` | chạy tốt | API thật; màn danh mục và form hiển thị. Chưa thử hết create/update/delete nhân viên |
| `/#/ADMIN/audit` | chạy tốt | /workspace/audit trả nhật ký MySQL + SQLite, có hoạt động thực từ phiên thử |
| `/#/SOC_MANAGER/home` | chạy tốt | /workspace/reports, incidents, staff; KPI, rủi ro, hiệu suất, cấu hình lương thật |
| `/#/SOC_L1/home` | chạy tốt | /tables/canh_bao có phân trang tải đủ; hàng đợi NEW, bộ lọc, form tạo/chuyển cấp |
| `/#/SOC_L2/home` | chạy tốt | Danh sách INVESTIGATING được giao; bảng top tài sản tháng hiện tại rỗng do seed tháng khác |
| `/#/SOC_L3/home` | chạy tốt | Critical/High, MITRE/IOC và tài sản đều lấy từ báo cáo backend |
| `/#/INCIDENT_RESPONDER/home` | chạy tốt | Board CONTAINED/REMEDIATING và danh sách đóng từ API thật |
| `/#/THREAT_HUNTER/home` và `/intelligence` | chạy tốt | /workspace/intelligence, /workspace/iocs, /workspace/incidents; hai route hiện dùng cùng HunterLayout |
| `/#/{role}/incidents`, 6 vai trò nghiệp vụ | chạy tốt | Dùng danh sách /workspace/incidents đã tải ở App; đổi route không nhất thiết phát request mới |
| `/#/{role}/incidents/{id}` | chạy tốt | /workspace/incidents/{id} + /workspace/intelligence, cảnh báo/tài sản/IOC/MITRE/phân công/timeline từ DB |
| `/#/{role}/personal`, 6 vai trò nghiệp vụ | chạy tốt sau liên kết | /workspace/personal; trước khi liên kết profile trả 409. Lương chưa có hiển thị Chưa cấu hình |
| Luồng tạo → chuyển cấp → CLOSED | chạy tốt | Đã đi qua form L1/L2/L3/Responder, từng mutation 200/201; timeline ghi đủ trạng thái |
| Critical thiếu hoặc sai chuyên gia | chạy tốt | API trả 409; L2 hợp lệ tạo 201, được trigger phân công tự động |
| Quyền đọc sự cố chưa được giao | lỗi về phạm vi cần chốt | L2/Responder danh sách workspace có lọc, nhưng generic API và detail nhận ID bất kỳ không kiểm tra cùng IOC |
| Màn CRUD riêng cho danh mục MITRE/IOC, cảnh báo ngoài khu vực L1 | chưa làm ở UI | MITRE hiện tra cứu/gắn liên kết; IOC có form tạo. Không có route độc lập sửa/xóa các danh mục này; không coi đó là lỗi API |
| Dữ liệu mock/hard-code trong UI | không phát hiện | Dữ liệu nghiệp vụ đến từ API thật; nội dung database là seed mô phỏng, không phải dữ liệu sản xuất |

Không tìm thấy TODO/mock/fake/dummy hoặc Math.random trong frontend/src đang chạy. Placeholder ở ô tìm IOC là gợi ý nhập liệu; thông báo Chưa có dữ liệu/Chưa cấu hình là trạng thái rỗng thật. Mã vai trò, tên hành động và quy tắc SLA cố định là cấu hình nghiệp vụ, không phải dữ liệu mock. Checklist Responder lấy từ các hành động đã ghi.

## Lỗi trước khi liên kết nhân viên
Seed tài khoản đơn thuần tạo accounts trong SQLite, không tạo soc_account_profiles. GET /workspace/staff trả mảng rỗng ban đầu. Các request 409 đã ghi nhận:

| Vai trò | Endpoint | HTTP |
|---|---|---|
| SOC_MANAGER | /workspace/personal | 409 |
| SOC_L1 | /workspace/personal | 409 |
| SOC_L2 | /workspace/incidents | 409 |
| SOC_L2 | /workspace/personal | 409 |
| SOC_L3 | /workspace/personal | 409 |
| INCIDENT_RESPONDER | /workspace/incidents | 409 |
| INCIDENT_RESPONDER | /workspace/personal | 409 |
| THREAT_HUNTER | /workspace/personal | 409 |

Sau khi Admin liên kết qua API, các endpoint trên trả 200 cho 6 vai trò nghiệp vụ. Frontend L2/Responder tải incidents trong Promise.all ở App.tsx, nên thiếu profile có thể làm toàn bộ trang chủ báo lỗi thay vì chỉ trang Của tôi.

## Endpoint matrix thực tế
Tiền tố tất cả đường dẫn: /api/v1. Ma trận sau chạy sau liên kết profile. HTTP 403 đúng chính sách không được tính là lỗi khởi động/chức năng. Việc gọi trực tiếp một bảng bị cấm có thể khác quyền của endpoint workspace tổng hợp; xem phần quyền bên dưới.

| Endpoint GET | Admin | Manager | L1 | L2 | L3 | Responder | Hunter |
|---|---:|---:|---:|---:|---:|---:|---:|
| /auth/me | 200 | 200 | 200 | 200 | 200 | 200 | 200 |
| /roles | 200 (7) | 200 (7) | 200 (7) | 200 (7) | 200 (7) | 200 (7) | 200 (7) |
| /accounts | 200 (8) | 403 | 403 | 403 | 403 | 403 | 403 |
| /meta/tables | 200 (3) | 200 (14) | 200 (6) | 200 (11) | 200 (11) | 200 (8) | 200 (9) |
| /workspace/staff | 200 (6) | 200 (6) | 200 (6) | 200 (6) | 200 (6) | 200 (6) | 200 (6) |
| /workspace/incidents | 403 | 200 (150) | 200 (150) | 200 (19) | 200 (150) | 200 (17) | 200 (150) |
| /workspace/incidents/INC004 | 403 | 200 | 200 | 200 | 200 | 200 | 200 |
| /workspace/intelligence | 403 | 200 | 200 | 200 | 200 | 200 | 200 |
| /workspace/personal | 403 | 200 | 200 | 200 | 200 | 200 | 200 |
| /workspace/personal?month=2026-10 | 403 | 200 | 200 | 200 | 200 | 200 | 200 |
| /workspace/reports | 403 | 200 | 200 | 200 | 200 | 200 | 200 |
| /workspace/reports?month=2026-10 | 403 | 200 | 200 | 200 | 200 | 200 | 200 |
| /workspace/audit | 200 (6) | 403 | 403 | 403 | 403 | 403 | 403 |
| /dashboard | 200 | 200 | 200 | 200 | 200 | 200 | 200 |
| /reports/incident-summary | 403 | 200 | 200 | 200 | 200 | 200 | 200 |
| /tables/to_chuc?page_size=100 | 200 (20) | 200 (20) | 403 | 403 | 403 | 403 | 403 |
| /tables/nhan_vien_soc?page_size=100 | 200 (30) | 200 (30) | 403 | 403 | 403 | 403 | 403 |
| /tables/tai_san?page_size=100 | 200 (120) | 200 (120) | 200 (120) | 200 (120) | 200 (120) | 200 (120) | 200 (120) |
| /tables/su_co?page_size=100 | 403 | 200 (150) | 200 (150) | 200 (150) | 200 (150) | 200 (150) | 200 (150) |
| /tables/canh_bao?page_size=100 | 403 | 200 (450) | 200 (450) | 200 (450) | 200 (450) | 200 (450) | 200 (450) |
| /tables/ioc?page_size=100 | 403 | 200 (100) | 200 (100) | 200 (100) | 200 (100) | 200 (100) | 200 (100) |
| /tables/ky_thuat_mitre?page_size=100 | 403 | 200 (25) | 403 | 200 (25) | 200 (25) | 403 | 200 (25) |
| /tables/canh_bao_tai_san?page_size=100 | 403 | 200 (500) | 200 (500) | 200 (500) | 200 (500) | 403 | 200 (500) |
| /tables/tai_san_incident?page_size=100 | 403 | 200 (250) | 403 | 200 (250) | 200 (250) | 200 (250) | 200 (250) |
| /tables/incident_ioc?page_size=100 | 403 | 200 (305) | 403 | 200 (305) | 200 (305) | 200 (305) | 200 (305) |
| /tables/su_co_ky_thuat_mitre?page_size=100 | 403 | 200 (250) | 403 | 200 (250) | 200 (250) | 403 | 200 (250) |
| /tables/su_co_nhan_vien_soc?page_size=100 | 403 | 200 (363) | 403 | 403 | 403 | 403 | 403 |
| /tables/hanh_dong_xu_ly?page_size=100 | 403 | 200 (364) | 403 | 200 (364) | 200 (364) | 200 (364) | 403 |
| /tables/lich_su_trang_thai?page_size=100 | 403 | 200 (414) | 200 (414) | 200 (414) | 200 (414) | 200 (414) | 403 |

Số trong ngoặc là số bản ghi/mảng ở lượt ma trận, trước các mutation tiếp theo; cột total của lương là số tiền, không được diễn giải thành số dòng.

## Phân quyền: hành vi đọc/ghi đã xác nhận
| Vai trò | Đọc | Ghi/chặn đã thử hoặc xác nhận từ code |
|---|---|---|
| ADMIN | Tài khoản, 3 danh mục, staff, nhật ký | Tạo/đổi vai trò/khóa tài khoản, tạo/sửa tổ chức và liên kết profile thành công; nghiệp vụ incidents trả 403 |
| SOC_MANAGER | Toàn bộ nghiệp vụ, báo cáo nhân sự/lương; không đọc quản lý tài khoản hoặc nhật ký Admin | Phân công, mọi bước hợp lệ của workflow, cấu hình lương thành công |
| SOC_L1 | Tất cả sự cố ở workspace, cảnh báo/tài sản/IOC/lịch sử; MITRE tổng hợp bị ẩn | Tạo/triage NEW, nhận xử lý, chuyển L2; không thêm hành động và không cấu hình lương |
| SOC_L2 | Danh sách workspace lọc theo phân công; generic và detail vẫn đọc ngoài phân công | Collect Evidence/Scan Malware, gắn IOC/Technique, khoanh vùng, chuyển L3; Block IP 403; mutation ngoài phân công 403 |
| SOC_L3 | Mọi sự cố, không bắt buộc được giao | Cập nhật phân tích/risk score, khoanh vùng, chuyển Responder thành công bằng form thật |
| INCIDENT_RESPONDER | Danh sách workspace lọc theo phân công; generic/detail vẫn đọc ngoài phân công; MITRE tổng hợp bị ẩn | Thêm hành động ứng phó, REMEDIATING/CLOSED khi được giao; mutation ngoài phân công 403 |
| THREAT_HUNTER | Mọi sự cố, IOC/MITRE; generic action/history 403 nhưng detail vẫn chứa chúng | Tạo IOC, chặn IOC trùng, gắn IOC và tạo incident thành công; có thể gắn IOC vào vụ chưa được giao theo code hiện tại |

Các vai trò ngoài Manager bị PUT /workspace/compensation trả 403. /workspace/personal lấy employee_id từ tài khoản, bỏ qua employee_id truyền vào query; đã thử không đọc lương người khác. Đường PUT /tables/su_co/{id} bị 409 đối với người có quyền ghi nghiệp vụ và 403 đối với người không có quyền, không vượt workflow.

### Phạm vi đọc ngoài phân công
docs/role-workspaces.md cho phép tham khảo hồ sơ liên quan cùng IOC. Đọc hồ sơ liên quan không tự nó là lỗi. Tuy nhiên code hiện không kiểm tra quan hệ cùng IOC và API generic không lọc theo phân công:
- L2 và Responder đọc được sự cố E2E do L1 tạo khi chưa được giao và sự cố đó không có IOC; can_work=false nhưng HTTP 200, không phải 403.
- Sau seed và các luồng thử, GET /tables/su_co cho cả hai role báo total=154; workspace list lần lượt chỉ 22 và 19 ở lượt kiểm tra bổ sung (số liệu trước khi Hunter tạo thêm một vụ).
- Cả L2 và Responder đọc INC001 chưa được giao: trả 3 hành động, 7 sự kiện timeline, 2 người tham gia, can_work=false.
- POST actions và transition khi chưa được giao đều trả 403: chặn ghi đang hoạt động.
- L1/Hunter generic action hoặc history bị 403 trong ma trận nhưng endpoint detail trả action/timeline. Cần thống nhất quyền đọc dữ liệu tổng hợp với các bảng nền; không coi riêng sự khác biệt này là bypass ghi.
- L2 gắn Technique trả 200. Đây phù hợp tài liệu workspace hiện tại, dù bảng quyền nền trong roles.md chưa thể hiện đầy đủ; không ghi nhận thành lỗi nâng quyền L2.

## Luồng nghiệp vụ
| Bước/kiểm tra | HTTP hoặc kết quả |
|---|---|
| Create HIGH by L1 | 201 — đúng kỳ vọng |
| Unassigned action SOC_L2 | 403 — đúng kỳ vọng |
| Unassigned action INCIDENT_RESPONDER | 403 — đúng kỳ vọng |
| NEW -> INVESTIGATING by L1 | 200 — đúng kỳ vọng |
| Assign SOC_L2 | 200 — đúng kỳ vọng |
| Assign SOC_L3 | 200 — đúng kỳ vọng |
| Assign INCIDENT_RESPONDER | 200 — đúng kỳ vọng |
| Assign THREAT_HUNTER | 200 — đúng kỳ vọng |
| Duplicate assignment blocked | 409 — đúng kỳ vọng |
| L2 forbidden action blocked | 403 — đúng kỳ vọng |
| L2 adds action | 200 — đúng kỳ vọng |
| L2 technique write vs permissions matrix | 200 — đúng kỳ vọng |
| INVESTIGATING -> CONTAINED by L2 | 200 — đúng kỳ vọng |
| Responder adds action | 200 — đúng kỳ vọng |
| CONTAINED -> REMEDIATING by responder | 200 — đúng kỳ vọng |
| REMEDIATING -> CLOSED by responder | 200 — đúng kỳ vọng |
| CLOSED cannot reopen | 409 — đúng kỳ vọng |
| Critical without expert blocked | 409 — đúng kỳ vọng |
| Critical L1 expert blocked | 409 — đúng kỳ vọng |
| Critical L2 expert accepted | 201 — đúng kỳ vọng |
| Create no-action case | 201 — đúng kỳ vọng |
| No-action case -> INVESTIGATING | 200 — đúng kỳ vọng |
| No-action case -> CONTAINED | 200 — đúng kỳ vọng |
| No-action case -> REMEDIATING | 200 — đúng kỳ vọng |
| Close without action blocked | 409 — đúng kỳ vọng |
| Configure isolated demo salary | 200 — đúng kỳ vọng |
| Admin creates account | 201 — đúng kỳ vọng |
| Admin changes role and disables account | 200 — đúng kỳ vọng |
| Disabled account cannot login | 401 — đúng kỳ vọng |
| Admin creates org | 201 — đúng kỳ vọng |
| Admin edits org | 200 — đúng kỳ vọng |
| Hunter creates IOC | 201 — đúng kỳ vọng |
| Duplicate IOC rejected | 409 — đúng kỳ vọng |
| Hunter links IOC to unassigned Critical case | 200 — đúng kỳ vọng |
| Hunter creates incident | 201 — đúng kỳ vọng |

### Luồng form trình duyệt
| Bước | Vai trò | HTTP |
|---|---|---|
| UI create HIGH | SOC_L1 | 201 |
| UI NEW -> INVESTIGATING | SOC_L1 | 200 |
| UI L1 -> L2 handoff | SOC_L1 | 200 |
| UI L2 collect evidence | SOC_L2 | 200 |
| UI L2 -> L3 handoff | SOC_L2 | 200 |
| UI L3 analysis | SOC_L3 | 200 |
| UI INVESTIGATING -> CONTAINED | SOC_L3 | 200 |
| UI L3 -> responder handoff | SOC_L3 | 200 |
| UI responder action | INCIDENT_RESPONDER | 200 |
| UI CONTAINED -> REMEDIATING | INCIDENT_RESPONDER | 200 |
| UI REMEDIATING -> CLOSED | INCIDENT_RESPONDER | 200 |

Sự cố luồng API: INC-fa20c2141cf7; trạng thái CLOSED; 2 hành động, 4 lần chuyển trạng thái. Sự cố luồng UI: INC-b0485c762f79; đã nhìn thấy CLOSED trên trang sau lần tải lại chi tiết.
Lương thử NV022 tháng 11: 12.345.000; thưởng sau luồng API HIGH đóng đúng SLA: 500.000; tổng 12.845.000 (kết quả chụp trước luồng browser đóng thêm một vụ). Đây là dữ liệu thử ghi thật trong database thử.

## Route đã duyệt và API thật quan sát được
Chỉ liệt kê lần đầu cho mỗi tổ hợp role/route. Các route dùng dữ liệu tải sẵn có thể không phát request riêng khi đổi hash.

| Vai trò | Route | API quan sát trong lượt mở | Lỗi giao diện |
|---|---|---|---|
| ADMIN | /#/ADMIN/home | /accounts, /tables/nhan_vien_soc?page_size=100&page=1 | Không |
| ADMIN | /#/ADMIN/to_chuc | /meta/tables, /tables/to_chuc?page=1&page_size=20 | Không |
| ADMIN | /#/ADMIN/tai_san | /meta/tables, /tables/tai_san?page=1&page_size=20 | Không |
| ADMIN | /#/ADMIN/nhan_vien_soc | /meta/tables, /tables/nhan_vien_soc?page=1&page_size=20 | Không |
| ADMIN | /#/ADMIN/audit | /workspace/audit | Không |
| SOC_MANAGER | /#/SOC_MANAGER/home | Dữ liệu App đã tải / xem mô tả API ở trên | Không |
| SOC_MANAGER | /#/SOC_MANAGER/incidents | Dữ liệu App đã tải / xem mô tả API ở trên | Không |
| SOC_MANAGER | /#/SOC_MANAGER/incidents/INC004 | /workspace/incidents/INC004, /workspace/intelligence | Không |
| SOC_MANAGER | /#/SOC_MANAGER/personal | /workspace/personal?month=2026-11 | Không |
| SOC_L1 | /#/SOC_L1/home | /tables/canh_bao?page_size=100&page=1, /tables/canh_bao?page_size=100&page=2, /tables/canh_bao?page_size=100&page=3, /tables/canh_bao?page_size=100&page=4, /tables/canh_bao?page_size=100&page=5 | Không |
| SOC_L1 | /#/SOC_L1/incidents | Dữ liệu App đã tải / xem mô tả API ở trên | Không |
| SOC_L1 | /#/SOC_L1/incidents/INC004 | /workspace/incidents/INC004, /workspace/intelligence | Không |
| SOC_L1 | /#/SOC_L1/personal | /workspace/personal?month=2026-11 | Không |
| SOC_L2 | /#/SOC_L2/home | Dữ liệu App đã tải / xem mô tả API ở trên | Không |
| SOC_L2 | /#/SOC_L2/incidents | Dữ liệu App đã tải / xem mô tả API ở trên | Không |
| SOC_L2 | /#/SOC_L2/incidents/INC004 | /workspace/incidents/INC004, /workspace/intelligence | Không |
| SOC_L2 | /#/SOC_L2/personal | /workspace/personal?month=2026-11 | Không |
| SOC_L3 | /#/SOC_L3/home | Dữ liệu App đã tải / xem mô tả API ở trên | Không |
| SOC_L3 | /#/SOC_L3/incidents | Dữ liệu App đã tải / xem mô tả API ở trên | Không |
| SOC_L3 | /#/SOC_L3/incidents/INC004 | /workspace/incidents/INC004, /workspace/intelligence | Không |
| SOC_L3 | /#/SOC_L3/personal | /workspace/personal?month=2026-11 | Không |
| INCIDENT_RESPONDER | /#/INCIDENT_RESPONDER/home | Dữ liệu App đã tải / xem mô tả API ở trên | Không |
| INCIDENT_RESPONDER | /#/INCIDENT_RESPONDER/incidents | Dữ liệu App đã tải / xem mô tả API ở trên | Không |
| INCIDENT_RESPONDER | /#/INCIDENT_RESPONDER/incidents/INC004 | /workspace/incidents/INC004, /workspace/intelligence | Không |
| INCIDENT_RESPONDER | /#/INCIDENT_RESPONDER/personal | /workspace/personal?month=2026-11 | Không |
| THREAT_HUNTER | /#/THREAT_HUNTER/home | Dữ liệu App đã tải / xem mô tả API ở trên | Không |
| THREAT_HUNTER | /#/THREAT_HUNTER/incidents | Dữ liệu App đã tải / xem mô tả API ở trên | Không |
| THREAT_HUNTER | /#/THREAT_HUNTER/incidents/INC004 | /workspace/incidents/INC004, /workspace/intelligence | Không |
| THREAT_HUNTER | /#/THREAT_HUNTER/personal | /workspace/personal?month=2026-11 | Không |
| THREAT_HUNTER | /#/THREAT_HUNTER/intelligence | /workspace/intelligence? | Không |
| SOC_L1 | /#/SOC_L1/incidents/INC-b0485c762f79 | /tables/canh_bao?page_size=100&page=2, /tables/canh_bao?page_size=100&page=3, /tables/canh_bao?page_size=100&page=4, /tables/canh_bao?page_size=100&page=5, /workspace/incidents/INC-b0485c762f79, /workspace/intelligence | Không |
| SOC_L2 | /#/SOC_L2/incidents/INC-b0485c762f79 | /workspace/incidents/INC-b0485c762f79, /workspace/intelligence | Không |
| SOC_L3 | /#/SOC_L3/incidents/INC-b0485c762f79 | /workspace/incidents/INC-b0485c762f79, /workspace/intelligence | Không |
| INCIDENT_RESPONDER | /#/INCIDENT_RESPONDER/incidents/INC-b0485c762f79 | /workspace/incidents/INC-b0485c762f79, /workspace/intelligence | Không |

## Việc cần làm trước demo theo ưu tiên
1. **P0 — chốt và thực thi phạm vi đọc:** nếu chỉ được xem hồ sơ được giao hoặc liên quan cùng IOC như mô tả, cần kiểm tra ở detail, generic incidents/actions/history và các endpoint tổng hợp. Hiện ID bất kỳ cũng đọc được. Giữ chặn ghi ngoài phân công đã chạy đúng.
2. **P1 — hoàn tất dữ liệu demo:** seed 7 tài khoản phải kèm bước liên kết profile rõ ràng; nếu thiếu, L2/Responder lỗi ngay trang chủ và 6 vai trò lỗi Của tôi. Giữ kho SQLite đi cùng dữ liệu MySQL đúng môi trường.
3. **P1 — chọn tháng/case trình diễn:** dữ liệu seed kết thúc tháng 10/2026; tháng 11 mặc định top_assets rỗng cho cả 6 vai trò. Đổi sang tháng 10 trả 10 tài sản. Chọn sẵn vụ đang ở giai đoạn phù hợp từng vai trò hoặc dùng vụ E2E mới.
4. **P1 — cấu hình lương nếu demo thu nhập:** chỉ NV022 được cấu hình mức thử trong lần này; các nhân viên khác giữ NULL, hiển thị Chưa cấu hình đúng thiết kế. Không giới thiệu ô rỗng thành tính năng đã có dữ liệu.
5. **P2 — đồng bộ tài liệu quyền và UI:** quyền nền roles.md khác một số quyền tổng hợp/workflow; ghi rõ quyền xem tham khảo, quyền gắn Technique của L2 và quyền đọc action/timeline của L1/Hunter.
6. **P2 — chốt phạm vi màn hình:** nếu bài nộp yêu cầu màn CRUD riêng cho cảnh báo/IOC/MITRE, hiện chưa có đủ route/form sửa/xóa. Không cần bổ sung nếu yêu cầu chỉ là tra cứu, tạo IOC và liên kết Technique hiện có.
7. **P2 — sửa nhãn chữ:** SharedIOC có nhãn Lo?i tại frontend/src/workspace/layouts.tsx:67; cần sửa trước khi chụp màn hình báo cáo.

## Bằng chứng
- D:/Database/soc-e2e-20261110/api_results.json: từng request, vai trò, HTTP, lỗi, số lượng và kỳ vọng.
- D:/Database/soc-e2e-20261110/browser_results.json: route, request mạng, form mutation, runtime errors.
- D:/Database/soc-e2e-20261110/supplementary_results.json và extra_flow_results.json: phạm vi đọc, dữ liệu rỗng, kiểm tra Admin/Hunter.
- D:/Database/soc-e2e-20261110/screenshots/: ảnh các trang được duyệt.
- Không đưa token hoặc mật khẩu vào báo cáo này. Các script bộ kiểm thử nằm ngoài repo tại D:/Database/soc-e2e-20261110.

Backend và frontend được giữ chạy để xem lại với môi trường thử tạm thời. Database soc_schema_test được giữ nguyên; không xóa database.
