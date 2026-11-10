# Khảo sát trước khi nâng cấp

## API hiện có

- POST `/auth/login`, GET `/auth/me`, GET `/roles`: dùng chung.
- GET/POST `/accounts`, PUT `/accounts/{username}`: Admin.
- GET `/meta/tables`; GET/POST `/tables/{table}`; GET/PUT/DELETE `/tables/{table}/{key}`: CRUD phản chiếu schema.
- GET `/dashboard`: chỉ đếm bảng và nhóm trạng thái.
- GET `/reports/incident-summary`: tối đa 500 bản ghi, chưa có tổng hợp nghiệp vụ.

Các đường dẫn trên có tiền tố `/api/v1`.

## Phần thiếu theo vai trò

| Vai trò | Thiếu | Cách bổ sung |
|---|---|---|
| Admin | Danh mục, ràng buộc xóa nhân viên, nhật ký, liên kết tài khoản | Giữ CRUD danh mục; bổ sung profile và audit |
| Manager | SLA, Risk Score tổ chức, tải công việc, thống kê tháng, lương thưởng, phân công | API workspace/report, workflow assignment, compensation |
| L1 | Hàng đợi, lọc thời gian, gom cảnh báo, nhận xử lý, chuyển cấp, top tài sản | API incident list/create, transition/escalate, report |
| L2 | Sự cố của tôi, chi tiết liên kết, hành động có thời lượng, IOC/Technique | API detail/action/link, workspace |
| L3 | Ưu tiên Critical/High, báo cáo IOC/MITRE/tài sản, cập nhật phân tích | API workspace/report, analysis/escalate |
| Responder | Board của tôi, checklist, đóng có điều kiện, timeline | API workspace/detail/action/transition |
| Hunter | Bộ lọc IOC/Technique, incident chung IOC, tạo phát hiện | API intelligence, link, incident create |
| Nhân viên | Trang của tôi chỉ đúng người đăng nhập | API personal dựa trên liên kết tài khoản–MaNV |

## Khác biệt schema thực tế và yêu cầu

- `ThoiGianXuLy`, `ThoiGianDong` hiện NOT NULL: migration chuyển nullable để NEW không có thời gian xử lý/đóng giả.
- Bảng phân công có PK `(MaIncident, MaNV)`: đã chặn cùng nhân viên hai lần; yêu cầu cho phép vai trò khác được triển khai bằng PK ba cột `(MaIncident, MaNV, VaiTro)` và thêm thời điểm tham gia.
- Hành động và lịch sử lấy thời gian làm khóa chính: giữ schema, service chọn timestamp duy nhất và dùng giao dịch; thêm cột thời lượng cho hành động.
- Chưa có lương và liên kết tài khoản: thêm bảng profile, lương theo tháng, chính sách thưởng; không suy đoán dữ liệu lương.
- Chưa có nhật ký hệ thống: thêm bảng audit, ghi người dùng và hành động.
- IOC trước nâng cấp lấy giá trị làm PK. Bản sửa tiếp theo đã chuyển sang PK `(LoaiIOC, GiaTriIOC)` cùng FK liên quan; xem [mysql-business-rules.md](mysql-business-rules.md).

## Quy tắc cần thay thế

CRUD cũ cho phép sửa `TrangThai`, tạo phân công và lịch sử trực tiếp, chưa có
kiểm tra Critical hay điều kiện đóng. Các đường ghi đó phải chuyển qua service
workflow có khóa dòng, kiểm tra vai trò, lịch sử cùng giao dịch. Admin được quản
lý danh mục theo yêu cầu mới nhưng không được đọc/xử lý sự cố.
