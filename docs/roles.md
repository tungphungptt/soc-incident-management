# Tài khoản và phân quyền

Chính sách hiện tại sau bản sửa 10/11/2026. Quyền được kiểm tra tại backend,
kể cả khi gọi API trực tiếp; ẩn menu không thay thế kiểm tra quyền.

Tài khoản nằm trong SQLite: mặc định `backend/accounts.sqlite3`, hoặc đường
dẫn `SOC_ACCOUNT_DB` nếu đặt trước khi khởi động. Vai trò ở `accounts.role`.
`soc_account_profiles` trong MySQL nối `username` với `nhan_vien_soc.MaNV`.
Không có FK giữa hai database. Không xóa kho SQLite dự án để seed lại.

`seed_demo_accounts` chỉ chạy trên database có tên chứa `test` hoặc `demo` và
từ chối `soc_incident_management`. Script tạo/cập nhật 7 tài khoản và tự liên
kết 7 nhân viên khác nhau. Nhân viên nghiệp vụ mới được chọn theo bằng chứng
`su_co_nhan_vien_soc.VaiTro`; liên kết hợp lệ đang có được giữ lại. Admin dùng
một nhân viên riêng còn trống vì schema nhân viên không có vai trò ADMIN.
Thiếu bằng chứng/nhân viên thì báo lỗi, không tự tạo nhân viên giả.

| Vai trò | Đọc dữ liệu | Tạo / sửa | Xóa |
|---|---|---|---|
| Admin | Tài khoản, tổ chức, tài sản, nhân viên, nhật ký | Tài khoản, danh mục, liên kết hồ sơ | Danh mục; chặn nhân viên đã tham gia Incident |
| SOC Manager | Toàn bộ nghiệp vụ và báo cáo nhân sự/lương | Tạo/phân công/chuyển trạng thái/hành động/phân tích/IOC qua workflow; cấu hình lương | Danh mục được cho phép; không xóa trực tiếp Incident qua CRUD |
| L1 | Sự cố, cảnh báo, tài sản, IOC, liên kết cảnh báo–tài sản, lịch sử trạng thái | Sự cố, cảnh báo | Không |
| L2 | Chỉ sự cố được phân công và dữ liệu liên quan; không CRUD trực tiếp tổ chức/nhân viên/phân công | Collect Evidence/Scan Malware, tạo/gắn IOC, gắn Technique, INVESTIGATING → CONTAINED, chuyển L3 | Không |
| L3 | Mọi sự cố và dữ liệu nghiệp vụ được phép, không bắt buộc được phân công | Phân tích/Risk Score, bằng chứng, IOC/Technique, khoanh vùng và chuyển Responder | Không |
| Incident Responder | Chỉ sự cố được phân công và cảnh báo/tài sản/IOC/hành động/lịch sử liên quan; không đọc MITRE | Bảy hành động ứng phó, CONTAINED → REMEDIATING → CLOSED | Không |
| Threat Hunter | Mọi sự cố, cảnh báo, tài sản, IOC/MITRE và liên kết được phép | Tạo IOC, gắn IOC/Technique và tạo Incident từ phát hiện | Không |

CRUD chung không được ghi trực tiếp Incident, phân công, lịch sử, hành động,
IOC và liên kết IOC/Technique: trả 409 nếu có quyền nền, hoặc 403 nếu không có
quyền. Phải dùng endpoint workflow. Lịch sử MySQL do trigger ghi khi chuyển
trạng thái; Manager không có quyền ghi lịch sử thủ công. Các bảng PK ghép chưa
có CRUD đọc một hàng theo khóa ghép; sử dụng danh sách đã lọc theo phạm vi.

## Phạm vi đọc L2/Responder

- Server tra nhân viên từ profile của tài khoản, rồi tra các hàng phân công có
  cùng `MaNV`. Không tin `employee_id`, `mine=false` hoặc vai trò do client gửi.
- CLOSED vẫn đọc được nếu hàng phân công còn tồn tại. Schema chưa có thời điểm
  kết thúc phân công; xóa hàng đó thu hồi quyền ở yêu cầu tiếp theo.
- Chi tiết Incident và CRUD đọc một bản ghi ngoài phạm vi trả **403**. Cùng IOC
  với vụ được giao không đủ quyền xem vụ khác.
- Danh sách lọc trước khi đếm/phân trang/tìm kiếm: không có hàng phù hợp trả 200
  với danh sách rỗng. Không có profile thì đọc phạm vi trả 403.
- Cảnh báo, hành động, lịch sử, liên kết phải thuộc Incident được giao. Tài sản
  có thể liên quan qua Incident hoặc cảnh báo; IOC dùng đúng cặp loại và giá trị.
- Tài sản/IOC dùng chung vẫn thấy nếu có liên quan vụ được giao, nhưng không trả
  liên kết, ID hoặc lịch sử của vụ khác. Áp dụng cả intelligence, same-IOC,
  reports, dashboard và incident-summary, không chỉ danh sách frontend.
- Quyền nền giữ nguyên: Responder không đọc MITRE; cả hai không CRUD trực tiếp
  phân công. Hồ sơ được giao vẫn trả người tham gia phục vụ xử lý.

Manager, L1, L3, Hunter, Admin giữ nguyên phạm vi trước bản sửa. L1/Hunter được
xem action/timeline trong hồ sơ tổng hợp dù không được CRUD đọc bảng hành động.
Đây là phân quyền của ứng dụng, không phải MySQL GRANT cho từng nhân viên.

## Thu nhập và phiên đăng nhập

Chỉ Manager cấu hình lương qua `/workspace/compensation`. Sáu vai trò nghiệp
vụ đọc `/workspace/personal` của chính nhân viên liên kết; query `employee_id`
không đổi chủ thể. Admin không có trang thu nhập. Seed lương tạo 7 mức **demo**
tháng 10/2026 và giữ mức đã cấu hình khi chạy lại. Chỉ Admin đọc nhật ký và
quản lý tài khoản; không tự khóa/hạ quyền của chính mình.

Mật khẩu được băm bằng scrypt với salt riêng. JWT chỉ mang tên tài khoản, quyền được đọc lại từ kho tài khoản cho mỗi yêu cầu. Đổi mật khẩu không thu hồi JWT đã cấp; khóa tài khoản sẽ ngăn truy cập ngay.

Unit test từ `backend`: đặt tạm `DATABASE_URL=sqlite://`, rồi chạy
`.\.venv\Scripts\python.exe -B -m pytest tests/test_read_scope.py tests/test_roles.py tests/test_workspaces.py -q -p no:cacheprovider`.
MySQL/end-to-end chỉ dùng `soc_schema_test`, kho tài khoản demo riêng và biến
môi trường tạm. Xem [role-workspaces.md](role-workspaces.md); báo cáo cũ giữ lại
làm bằng chứng lịch sử, không thay thế chính sách mới này.
