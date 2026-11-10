# Bảy khu vực làm việc SOC

Ngày kiểm tra: 10/11/2026. Frontend: http://127.0.0.1:5173/.
Giữ nguyên bảy mã vai trò và tài khoản `admin` hiện có.

Bản sửa MySQL tiếp theo: [mysql-business-rules.md](mysql-business-rules.md).
Ràng buộc đã được kiểm tra cả ở backend lẫn trigger/CHECK/FK; lịch sử MySQL
do trigger ghi để tránh ghi hai lần.

## Giao diện và hành động

| Vai trò | Trang chủ | Thành phần riêng | Màu nhấn | Hành động được phép |
|---|---|---|---|---|
| ADMIN | Quản trị hệ thống | Tài khoản, liên kết nhân viên, danh mục, nhật ký | Tím `#8b5cf6` | Tạo/khóa/đổi vai trò, liên kết hồ sơ, CRUD tổ chức/tài sản/nhân viên có ràng buộc |
| SOC_MANAGER | Trung tâm điều hành | KPI, biểu đồ trạng thái/mức độ, Risk Score tổ chức, SLA, quá tải, hiệu suất và lương thưởng | Xanh dương `#3b82f6` | Phân công kèm vai trò, chuyển trạng thái hợp lệ, ghi hành động, phân tích, cấu hình lương tháng |
| SOC_L1 | Hàng đợi phân loại | Danh sách NEW dày dòng, SLA, cảnh báo chọn nhiều, tra cứu thời gian, top tài sản | Cyan `#06b6d4` | Gom cảnh báo từ NEW, tạo Incident, đặt mức độ, nhận xử lý, chuyển L2 |
| SOC_L2 | Bàn điều tra | Rail quy trình, thẻ Incident của tôi, bằng chứng, tương quan IOC | Vàng `#f59e0b` | Collect Evidence / Scan Malware, thêm IOC, gắn IOC/Technique, khoanh vùng, chuyển L3 |
| SOC_L3 | Phân tích chuyên sâu | Critical/High, biểu đồ MITRE, IOC phổ biến, tài sản chưa có Incident đóng | Hồng `#ec4899` | Cập nhật phân tích/Risk Score, khoanh vùng, giao Responder, bổ sung bằng chứng/IOC/Technique |
| INCIDENT_RESPONDER | Trung tâm ứng phó | Board CONTAINED / REMEDIATING, checklist theo hành động thực, timeline | Cam `#f97316` | Bảy hành động ứng phó, CONTAINED → REMEDIATING → CLOSED |
| THREAT_HUNTER | Không gian săn mối đe dọa | Bộ lọc IOC bốn tiêu chí, tìm MITRE, liên kết Incident, bảng phổ biến | Xanh lá `#10b981` | Thêm IOC, gắn IOC/Technique, tạo Incident từ phát hiện |

Các layout được khai báo riêng trong `frontend/src/workspace/layouts.tsx`.
Component nền ở `components.tsx`: bảng, badge, đồng hồ SLA, biểu đồ thanh,
timeline, thẻ thống kê. Chi tiết Incident và biểu mẫu dùng chung.

URL dùng hash: `/#/SOC_L1/home`, `/#/SOC_L2/incidents/{id}`, v.v.
Đăng nhập đưa người dùng về đúng trang chủ. URL khác vai trò hiển thị
“Không có quyền”. Backend kiểm tra lại mọi thao tác; không dựa vào URL hay
nút frontend. Sáng/tối được lưu trong localStorage.

## API thêm

Tất cả có tiền tố `/api/v1`, yêu cầu Bearer token:

| Method | Endpoint | Chức năng |
|---|---|---|
| GET | `/workspace/staff` | Nhân viên đã liên kết và vai trò active |
| PUT | `/workspace/profiles/{username}` | Admin liên kết tài khoản–MaNV |
| GET | `/workspace/incidents` | Lọc trạng thái, mức độ, ngày, của tôi; ưu tiên Critical |
| POST | `/workspace/incidents` | Tạo Incident NEW, gom cảnh báo, kiểm tra chuyên gia Critical |
| GET | `/workspace/incidents/{id}` | Cảnh báo, tài sản, IOC, Technique, người tham gia, timeline |
| PUT | `/workspace/incidents/{id}/triage` | L1/Manager phân loại mức độ khi NEW |
| POST | `/workspace/incidents/{id}/transition` | Chuyển trạng thái và ghi lịch sử trong giao dịch |
| POST | `/workspace/incidents/{id}/assign` | Manager chọn nhân viên và vai trò |
| POST | `/workspace/incidents/{id}/escalate` | L1 → L2, L2 → L3, L3 → Responder |
| POST | `/workspace/incidents/{id}/actions` | Hành động có kết quả và thời lượng |
| PUT | `/workspace/incidents/{id}/analysis` | Manager/L3 cập nhật mô tả và Risk Score |
| POST | `/workspace/incidents/{id}/links` | Gắn IOC hoặc Technique có sẵn |
| POST | `/workspace/iocs` | Thêm IOC, chống trùng |
| GET | `/workspace/intelligence` | Lọc loại/giá trị/nguồn/tin cậy và Technique |
| GET | `/workspace/personal` | Chỉ dữ liệu nhân viên liên kết với người đăng nhập |
| PUT | `/workspace/compensation` | Manager lưu lương cơ bản của nhân viên theo tháng |
| GET | `/workspace/audit` | Admin đọc 300 hoạt động gần nhất, gồm tài khoản |
| GET | `/workspace/reports` | Tổng hợp nghiệp vụ thật; chỉ Manager nhận dữ liệu nhân sự/lương |

CRUD cũ được giữ cho danh mục. Các đường ghi chung vào Incident, phân công,
lịch sử, hành động, IOC và liên kết IOC/Technique bị chặn để tránh vượt qua
workflow. Admin có quyền danh mục theo yêu cầu mới, không có quyền nghiệp vụ.

L2 và Responder chỉ đọc Incident có phân công cho nhân viên liên kết với tài
khoản. Hồ sơ khác, kể cả cùng IOC, trả 403 ở endpoint chi tiết/CRUD một bản ghi.
Danh sách, dữ liệu con, intelligence, báo cáo và dashboard đều lọc theo cùng
phạm vi; không trả ID Incident ngoài phân công qua liên kết IOC dùng chung.
Xóa phân công thu hồi quyền đọc ở yêu cầu kế tiếp. Frontend không quyết định
phạm vi này. Quyền các vai trò khác giữ nguyên; xem [roles.md](roles.md).

## Quy tắc cũ và cách sửa

| Trước đây | Hiện tại |
|---|---|
| Sửa `TrangThai` bằng CRUD tự do | Chặn đường ghi chung; service kiểm tra đúng chuỗi NEW → INVESTIGATING → CONTAINED → REMEDIATING → CLOSED |
| Không kiểm tra vai trò khi chuyển | L1 chỉ NEW; L2/L3 chỉ INVESTIGATING; Responder chỉ CONTAINED/REMEDIATING; Manager mọi bước hợp lệ |
| Có thể đổi CLOSED về NEW | Backend từ chối; frontend không đưa ra trạng thái tiếp theo |
| Không ghi lịch sử tự động | Mỗi lần chuyển ghi actor qua MaNV, trạng thái cũ/mới, thời điểm; audit ghi username; cùng giao dịch với cập nhật Incident |
| Critical không cần chuyên gia | Tạo/nâng mức độ/chuyển trạng thái kiểm tra có L2/L3; frontend yêu cầu chuyên gia khi tạo Critical |
| Đóng không cần hành động | Backend yêu cầu ít nhất một hành động; frontend vô hiệu nút đóng khi chưa có |
| Phân công chỉ PK nhân viên+Incident | PK ba cột thêm vai trò; chặn trùng cùng nhân viên/cùng vai trò; ghi thời điểm tham gia |
| Xóa nhân viên có thể cascade lịch sử | Backend từ chối nhân viên đã tham gia Incident hoặc đang liên kết tài khoản |
| Thời điểm xử lý/đóng bắt buộc ngay khi NEW | Hai cột nullable, được ghi đúng thời điểm chuyển trạng thái |
| Hành động không có thời lượng | Thêm `ThoiLuongPhut`, kiểm tra số phút dương |

Service khóa dòng Incident trong giao dịch khi thay đổi trạng thái/phân công/
hành động, và trả thông báo tiếng Việt khi ràng buộc bị vi phạm.

## SLA và thu nhập

SLA tính từ `ThoiGianPhatHien`: Critical 60, High 240, Medium 720, Low 1440 phút.
Đồng hồ dừng tại `ThoiGianDong` khi CLOSED, giữ thông tin đã vi phạm hay chưa.
Thời gian lưu trong MySQL theo UTC; giao diện chuyển sang giờ địa phương.

Risk Score tổ chức = Critical×10 + High×5 + Medium×2 + Low. Cặp tổ chức–Incident
được khử trùng trước khi tính. Tổ chức không có sự cố có điểm 0.

Ngưỡng quá tải: `OVERLOAD_THRESHOLD` trong `backend/.env`, mặc định 5 Incident
đang xử lý. Đếm Incident riêng biệt ở INVESTIGATING/CONTAINED/REMEDIATING.

“Của tôi” không nhận mã nhân viên do client chỉ định; server tra theo username.
Đếm sự cố CLOSED theo tháng đóng, thời gian xử lý từ phát hiện tới đóng. Mỗi
nhân viên tham gia được tính một lần/Incident dù có nhiều vai trò.

Lương cơ bản lấy từ `soc_monthly_salary`. Chính sách thưởng lấy từ
`soc_bonus_policy`; chỉ thưởng sự cố CLOSED đúng SLA, mỗi nhân viên tham gia
nhận đầy đủ mức theo severity. Chưa cấu hình thì trả null và hiển thị “Chưa cấu
hình”, không tự suy đoán lương. Seed demo lưu mức thưởng 1.000.000 / 500.000 /
200.000 / 100.000 VND và lương cơ bản demo theo từng nhân viên, từng tháng.
Các mức này là dữ liệu mô phỏng được lưu thật, không phải bảng lương thực tế.

## Migration và seed

Chạy từ `backend`:

```powershell
.\.venv\Scripts\python.exe -m scripts.migrate_workspaces
$env:DEMO_ACCOUNT_PASSWORD = 'Demo@12345'
try {
    .\.venv\Scripts\python.exe -m scripts.seed_demo_accounts --with-data
} finally {
    Remove-Item Env:DEMO_ACCOUNT_PASSWORD
}
```

Migration chỉ chạy thủ công, không tự chạy khi khởi động. Tạo bốn bảng bổ sung
profile, lương tháng, chính sách thưởng, audit; thêm thời điểm phân công và
thời lượng hành động, sửa PK phân công và độ chính xác timestamp, cho phép
NULL thời gian xử lý/đóng. Không xóa dữ liệu nghiệp vụ hay thay tài khoản admin.

`seed_demo_data` cũng có thể chạy riêng để không đặt lại mật khẩu demo.
Seed tạo 40 Incident `DMINC000..039`, 80 cảnh báo, 8 tài sản, 3 tổ chức,
8 IOC, 4 Technique, 6 nhân viên liên kết sáu tài khoản nghiệp vụ, phân công,
hành động và lịch sử. Các ID demo được dành riêng; bản ghi đã có được bỏ qua,
giữ các thay đổi khi demo. Đã chạy hai lần: lần đầu 40 Incident, lần sau 0.
Không có thao tác DROP, TRUNCATE hoặc reset dữ liệu khi khởi động.

## Kiểm chứng

- Backend: **34 test đạt**, gồm kiểm tra luồng đầy đủ, đóng không có hành động,
  rollback Critical thiếu chuyên gia, không vượt workflow qua CRUD, gom cảnh
  báo, phân công trùng, dữ liệu cá nhân, IOC trùng, bảo vệ nhân viên và SLA.
- Frontend: `npm run build` thành công.
- Chrome: đăng nhập bằng biểu mẫu lần lượt 7 tài khoản, kiểm tra trang chủ,
  menu, header, biểu mẫu hành động, trang cá nhân của sáu vai trò nghiệp vụ,
  URL sai vai trò, sáng/tối lưu lựa chọn. Không có lỗi runtime.
- Mobile 390px: không tràn ngang. [Ảnh mobile](screenshots/hunter-mobile-light.png).
- MySQL thật: chạy một Incident kiểm chứng từ NEW tới CLOSED qua L1/L2/L3/
  Responder, xác nhận 4 lần đổi trạng thái và 2 hành động trong timeline, chuyển
  cấp, cập nhật phân tích, chặn mở lại và xóa nhân viên. Đã xóa đúng Incident
  kiểm chứng cùng các dòng con, giữ 40 Incident seed và nhật ký kiểm chứng.

Kết quả trình duyệt có cấu trúc: [workspace-browser-results.json](workspace-browser-results.json).
Ảnh trang chủ: [Admin](screenshots/admin.png), [Manager](screenshots/soc_manager.png),
[L1](screenshots/soc_l1.png), [L2](screenshots/soc_l2.png), [L3](screenshots/soc_l3.png),
[Responder](screenshots/incident_responder.png), [Hunter](screenshots/threat_hunter.png).

## Giới hạn còn lại

- Đã sửa giới hạn IOC: PK/FK là cặp loại+giá trị, không ghép nhầm hai loại khác nhau.
- Phân tích tổng hợp hiện đọc dữ liệu bằng SQLAlchemy rồi tổng hợp trên server;
  phù hợp bộ demo nhưng cần tối ưu/pagination phía server khi lượng dữ liệu lớn.
- Chưa có màn hình chỉnh chính sách thưởng; chính sách được lưu trong database
  và seed rõ ràng, Manager có màn hình chỉnh lương cơ bản theo tháng.
- Gom cảnh báo chuyển liên kết sang Incident mới; giữ Incident nguồn NEW và
  lịch sử của nó. Không tự xóa Incident nguồn khi hết cảnh báo.
- Không có chức năng trong yêu cầu giao diện bị thay bằng số liệu cứng; các
  thống kê, checklist, SLA, thu nhập đều tính từ bản ghi thật trong database.
