# Sửa mức thưởng, IOC và ràng buộc MySQL

Kiểm tra trên MySQL 8.0.46, ngày 10/11/2026. Không reset database; giữ nguyên
40 Incident demo, tài khoản `admin` và dữ liệu liên kết hiện có.

## 1. Mức thưởng

| Severity | VND |
|---|---:|
| CRITICAL | 1.000.000 |
| HIGH | 500.000 |
| MEDIUM | 200.000 |
| LOW | 100.000 |

Migration upsert đúng bốn dòng trong `soc_bonus_policy`. Seed dùng cùng mức
mới và gọi migration để cập nhật cả dữ liệu đã tồn tại. Không sửa lương cơ bản
hay reset Incident. API vẫn tính thưởng từ chính sách đã lưu, chỉ cho CLOSED
đúng SLA và không đếm trùng một nhân viên nhiều vai trò.

## 2. Khóa IOC

- `ioc`: PRIMARY KEY `(LoaiIOC, GiaTriIOC)`.
- `incident_ioc`: PRIMARY KEY `(MaIncident, LoaiIOC, GiaTriIOC)`.
- FK `(LoaiIOC, GiaTriIOC)` tham chiếu đúng cặp của `ioc`, giữ CASCADE cho
  cập nhật/xóa chính IOC; xóa Domain không xóa liên kết URL cùng giá trị.
- Migration backfill LoaiIOC từ parent cũ trước khi bỏ FK cũ; xác nhận số
  dòng và toàn bộ tập liên kết trước/sau, không chỉ so sánh số lượng.
- Backend kiểm tra trùng theo cặp; detail, intelligence, top IOC và Incident
  chung IOC đều dùng cả hai trường. Frontend gửi `ioc_type` khi gắn IOC và
  hiển thị loại bên cạnh giá trị trong danh sách chọn.
- Collation hiện tại được giữ nguyên: so sánh không phân biệt hoa/thường như
  schema trước đây. Cùng giá trị ở hai loại khác nhau được phép.

## 3. Ràng buộc ở MySQL

File thực thi: [sql/triggers.sql](../sql/triggers.sql). Có 17 trigger, một
procedure cập nhật Risk Score và một VIEW vi phạm thời gian. CHECK/PK/FK được
cài trong [migration](../backend/scripts/migrate_business_rules.py).

| Yêu cầu | Cách MySQL thực thi |
|---|---|
| Critical có ít nhất một L2/L3 | BEFORE INSERT yêu cầu `MaChuyenGia`, `VaiTroChuyenGia`; AFTER INSERT tạo phân công ngay; BEFORE UPDATE kiểm tra phân công bằng locking read |
| Không làm mất chuyên gia Critical | Một phân công L2/L3 được chỉ định làm điểm bảo đảm; trigger chặn xóa/đổi khóa của phân công đó. Có thể chuyển chỉ định sang phân công L2/L3 khác đã tồn tại trước khi xóa người cũ |
| CLOSED cần hành động | BEFORE UPDATE chặn đóng khi không có hành động; thêm guard chống xóa/chuyển đi hành động cuối của CLOSED |
| Không CLOSED → NEW | BEFORE UPDATE chặn mọi mở lại CLOSED; đồng thời chỉ cho đúng chuỗi trạng thái hợp lệ |
| Không trùng phân công | PRIMARY KEY `(MaIncident, MaNV, VaiTro)` |
| Không xóa nhân viên phụ trách | BEFORE DELETE báo lỗi; FK của phân công/hành động/lịch sử dùng RESTRICT thay CASCADE để không xóa lịch sử qua cascade |
| Lịch sử trạng thái tự động | AFTER UPDATE ghi đúng một dòng với trạng thái cũ/mới, thời điểm và người thực hiện |
| Risk Score tổ chức tự cập nhật | Procedure khử trùng Incident/tổ chức; trigger trên Incident, liên kết tài sản–Incident, thay đổi/xóa tài sản; trigger tổ chức giữ giá trị dẫn xuất |
| Critical NEW không quá 1 giờ | VIEW `soc_critical_new_violations` đánh dấu ngay khi đọc nếu đã quá hạn; Manager report trả danh sách này, đồng hồ SLA vẫn hiển thị quá hạn |
| Giá trị severity/status hợp lệ | CHECK cho bốn mức độ và năm trạng thái |

### Critical và tính nguyên tử

MySQL không có deferred cross-table CHECK. Nếu bắt buộc parent Critical phải
có child trước INSERT thì không thể tạo parent do FK ngược. Vì vậy câu INSERT
Critical truyền chuyên gia và vai trò L2/L3; trigger tạo child trong chính câu
lệnh đó. Nếu tạo child thất bại, cả INSERT rollback. Backend xác thực tài khoản
active và vai trò của chuyên gia trước khi thực hiện.

MySQL kiểm tra L2/L3 theo `VaiTro` tham gia Incident, đúng trường sẵn có của
schema. Quyền đăng nhập vẫn do backend kiểm tra; SQL trực tiếp sử dụng quyền
của tài khoản database. Không đưa dữ liệu/mật khẩu đăng nhập SQLite vào MySQL.

Phân công bảo đảm được bảo vệ bằng khóa dòng parent, tránh tình huống hai
giao dịch cùng xóa hai chuyên gia. Nếu đổi chuyên gia bằng SQL, thêm phân công
mới trước, rồi cập nhật `su_co.MaChuyenGia/VaiTroChuyenGia` sang phân công đó.
Backend hiện không có thao tác xóa phân công nên không thay đổi giao diện đang chạy.

### Actor và lịch sử

Backend đặt `@soc_actor_employee` và `@soc_actor_username` trên connection,
thực hiện UPDATE, rồi xóa các biến trong `finally`. Trigger ghi lịch sử trong
cùng transaction. Backend không ghi thêm lịch sử MySQL nên không có dòng trùng.
SQLite test giữ fallback ghi lịch sử để kiểm thử service độc lập.

SQL trực tiếp không đặt actor vẫn ghi `USER()` vào `NguoiThucHien`; MaNV để
NULL thay vì gán nhầm một nhân viên. Timestamp dùng microsecond và tránh trùng
khóa thời gian. `@soc_change_time` chỉ dùng khi seed lịch sử với mốc thời gian demo.

### Critical NEW quá một giờ

Thời gian trôi qua không phát sinh INSERT/UPDATE để trigger chạy, và CHECK
không dùng được UTC_TIMESTAMP() thay đổi theo thời gian. VIEW tính trực tiếp:

```sql
SELECT * FROM soc_critical_new_violations;
```

Trả deadline, số giây quá hạn và `ViPham=1`; không cần bật global
`event_scheduler`, không tự đổi trạng thái hoặc xóa Incident vi phạm. Đây là
cơ chế đánh dấu/truy vấn kiểm tra được yêu cầu, không phải từ chối dữ liệu cũ
đã quá một giờ khi khởi động. Test backdate Critical NEW hai giờ, thấy vi phạm;
chuyển INVESTIGATING thì dòng đó biến mất khỏi VIEW.

## 4. Lệnh chạy

Dừng API trong lúc chạy DDL, từ `backend`:

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

Migration đọc và chạy `sql/triggers.sql`; không cần cài MySQL CLI. Có thể chạy
lại file trigger sau migration bằng MySQL client, từ thư mục gốc dự án:

```powershell
mysql -u root -p soc_incident_management --execute="source sql/triggers.sql"
mysql -u root -p soc_incident_management --execute="source sql/queries.sql"
```

Trước DDL, migration lưu JSON dữ liệu và SHOW CREATE TABLE vào
`backend/migration_backups/` (bỏ qua trong Git). MySQL DDL tự commit; migration
có kiểm tra schema từng bước để chạy tiếp nếu gián đoạn, không tự phục hồi
bằng reset DB. Nếu dữ liệu cũ có Critical thiếu chuyên gia hoặc CLOSED thiếu
hành động, migration dừng ở preflight để xử lý rõ ràng, không bịa phân công.
Đã chạy migration nhiều lần và seed lần nữa: thêm 0 Incident, giữ nguyên số
dòng nghiệp vụ, toàn bộ IOC edges và bản ghi admin.

## 5. Kết quả kiểm chứng

**48 test backend đạt**, trong đó **13 test MySQL trực tiếp** chạy bằng SQL
và rollback ở cuối mỗi test. Không chỉ kiểm tra lỗi ở API:

- INSERT Critical thiếu chuyên gia bị chặn; có chuyên gia thì child tự tạo.
- Xóa/đổi phân công chuyên gia bảo đảm bị chặn; đổi bảo đảm sang L3 hợp lệ được phép.
- Nâng severity lên Critical khi thiếu chuyên gia bị chặn.
- Đóng không có hành động bị chặn và không ghi lịch sử thừa.
- Mở lại CLOSED, xóa hành động cuối, xóa nhân viên phụ trách bị chặn.
- PK chặn phân công trùng; CHECK chặn severity sai.
- UPDATE trực tiếp ghi một lịch sử, đúng actor; SQL không actor ghi DB USER().
- Hai loại IOC cùng giá trị cùng tồn tại; cặp trùng và FK sai bị chặn.
- Risk Score thay đổi theo severity, không nhân đôi vì hai tài sản cùng tổ chức.
- VIEW phát hiện Critical NEW quá một giờ và loại khỏi danh sách sau khi nhận xử lý.
- Mức thưởng hiện có trong database khớp đúng cả bốn mức của đề.

API cũng đã chạy chuỗi NEW → INVESTIGATING → CONTAINED → REMEDIATING → CLOSED
với trigger: đúng bốn dòng lịch sử, đúng username từng actor. Tạo và gắn hai
IOC cùng giá trị nhưng khác loại không bị tương quan nhầm. Dữ liệu kiểm chứng
được xóa đúng các ID tạo riêng; dữ liệu seed và admin được giữ nguyên.

Frontend build thành công. Chỉ thay selector IOC để gửi cặp khóa, cột Risk Score
tổ chức không cho nhập tay; các layout và chức năng đã chạy tốt được giữ nguyên.

## 6. Đủ 18 truy vấn SQL thuần

File [sql/queries.sql](../sql/queries.sql) đánh số Q01–Q18; dùng các biến tháng,
khoảng ngày, mã Incident, mốc hiện tại, ngưỡng quá tải và ngưỡng cảnh báo ở đầu.
Kết quả máy đọc: [sql-query-results.json](sql-query-results.json).

Tham số kiểm tra: tháng 11/2026, từ 01/11 đến trước 01/12, Incident `DMINC004`,
ngưỡng quá tải 5, ngưỡng cảnh báo 5, thời điểm kiểm tra ghi trong JSON.

| Câu | Nội dung | Số dòng |
|---|---|---:|
| Q01 | Incident trong khoảng ngày | 25 |
| Q02 | Top tài sản cảnh báo tháng | 8 |
| Q03 | Tổ chức nhiều Critical/High nhất | 1 |
| Q04 | Đang xử lý và vi phạm SLA | 20 |
| Q05 | Thời gian xử lý trung bình theo nhân viên/tháng | 18 |
| Q06 | Incident tham gia theo nhân viên/tháng | 18 |
| Q07 | Technique phổ biến | 4 |
| Q08 | IOC phổ biến, theo đúng cặp | 8 |
| Q09 | Các cặp Incident cùng IOC | 80 |
| Q10 | Tài sản nhiều cảnh báo, chưa có Incident CLOSED | 1 |
| Q11 | Risk Score mọi tổ chức và đối chiếu giá trị lưu | 3 |
| Q12 | Top 10 tổ chức theo Risk Score | 3 |
| Q13 | Lịch sử đầy đủ Incident | 6 |
| Q14 | Nhân viên tham gia Incident | 6 |
| Q15 | Thưởng theo Incident/nhân viên | 48 |
| Q16 | Tổng thưởng và lương+thưởng tháng | 6 |
| Q17 | Nhân viên quá tải đồng thời | 6 |
| Q18 | Incident chưa phân công | 2 |

Đã sửa lỗi cộng Low giả cho tổ chức không có Incident; khử trùng nhân viên có
nhiều vai trò; toàn bộ join IOC dùng đủ cặp loại+giá trị. Q17 dùng quét khoảng
thời gian và xử lý kết thúc trước bắt đầu khi trùng mốc.
Số dòng Q04 có thể tăng khi thời gian trôi qua; bảng trên khớp mốc `now_ref`
được ghi trong file JSON của lần kiểm tra cuối.

## Phần chưa làm

Không còn mục nào trong bốn yêu cầu bị bỏ dở. Vi phạm Critical NEW được đánh
dấu bằng VIEW/truy vấn theo thời gian thực, không dùng event tự ép chuyển trạng
thái. MySQL vẫn yêu cầu quyền tạo/sửa trigger/procedure khi cài migration.
