# Báo cáo bộ dữ liệu seed – soc_incident_management

Nguồn schema: `schema_soc_fixed.sql` (mysqldump 8.0.46, 14 bảng). Dữ liệu sinh bằng `generate_seed.py` (seed ngẫu nhiên cố định 20261021, chạy lại cho ra đúng cùng một file). Mốc "hiện tại" giả lập của bộ dữ liệu: **2026-10-21 12:00:00**.

## A. Cách thiết kế dữ liệu
- Mỗi incident thuộc 1 trong 7 kịch bản (brute force, PowerShell độc hại, ransomware, tấn công web, rò rỉ dữ liệu, phishing, di chuyển ngang). Kịch bản quyết định loại cảnh báo, nguồn phát hiện, kỹ thuật MITRE, loại IOC và loại hành động xử lý, nên dữ liệu có tương quan thay vì ngẫu nhiên rời rạc.
- IP: tài sản dùng dải RFC 1918 (10.x, 172.16.x) và 192.0.2.0/24 cho cloud; kẻ tấn công/IOC dùng 203.0.113.0/24 và 198.51.100.0/24. Domain dùng `.example`. Hash là SHA-256/SHA-1/MD5 của chuỗi mẫu, không phải mã độc thật.
- Cảnh báo luôn gắn tài sản thuộc đúng tập tài sản của incident chứa nó; IP đích/nguồn của cảnh báo khớp IP tài sản.
- Mốc thời gian incident tròn phút để dễ kiểm chứng; mọi ID có quy tắc (TC001, NV001, TS001, INC001, CB001, IOC001, mã T-ID MITRE).
- Có 3 tài sản "nóng" (CSDL của 3 tổ chức CRITICAL) chỉ nằm trong incident chưa đóng nhưng có rất nhiều cảnh báo, phục vụ truy vấn 10.

## B. Giả định và hạn chế của schema
1. `hanh_dong_xu_ly` và `lich_su_trang_thai` có khóa chính tự tăng (`MaHanhDong`, `MaLichSu`), nên không còn rủi ro trùng `ThoiGianThucHien` như prompt gốc giả định. File seed vẫn ghi **ID tường minh** (1..N, theo thứ tự thời gian) để chạy lại ra kết quả giống nhau. Hệ quả: nếu bảng đã có dòng, ID sẽ đụng khóa chính.
2. `su_co.ThoiGianXuLy` và `ThoiGianDong` cho phép NULL: incident NEW có cả hai NULL; chưa CLOSED thì `ThoiGianDong` NULL. Quy ước: `ThoiGianXuLy` = lúc bắt đầu xử lý = lúc chuyển NEW → INVESTIGATING.
3. `canh_bao.MaIncident NOT NULL`: mọi cảnh báo thuộc đúng 1 incident; không có cảnh báo mồ côi.
4. `su_co_nhan_vien_soc` khóa chính `(MaIncident, MaNV)`: mỗi nhân viên chỉ một dòng/incident. `ViTri` = vị trí trong incident (vd. Incident Lead), `VaiTro` = vai trò nghiệp vụ.
5. `nhan_vien_soc` không có cột vai trò/cấp độ. Mình gán mỗi nhân viên một vai trò chính (2 Manager, 3 L3, 9 L2, 4 IR, 3 TH, 9 L1) và `VaiTro` trong phân công theo vai trò đó; 8 nhân viên L2/L3 đôi khi đảm nhận vai trò phụ (Incident Responder/Threat Hunter). Vai trò chính chỉ tồn tại ở quy ước dữ liệu, schema không ràng buộc.
6. Không có CHECK/ENUM: mọi giá trị mức độ, trạng thái, loại là chuỗi tự do. Bộ này dùng `CRITICAL/HIGH/MEDIUM/LOW` và `NEW/INVESTIGATING/CONTAINED/REMEDIATING/CLOSED`. **File seed cũ (`soc_incident_seed_data.sql`) dùng giá trị khác** (`Cao`, `Low`, `Đã đóng`...); không trộn hai bộ trong cùng database vì dashboard/GROUP BY sẽ tách thành nhóm riêng.
7. `ThoiGian` (cột thứ hai trong `hanh_dong_xu_ly`) không rõ ngữ nghĩa; mình đặt bằng `ThoiGianThucHien`.
8. Không có bảng lương/thưởng/ca trực: chỉ tính được **thưởng** theo công thức giả định (Q15–Q16, mức tiền là tham số giả lập), **không tính được tổng lương**.
9. `su_co` không có `MaTC`: tổ chức suy ra qua tài sản. Quy tắc: mỗi incident tính **một lần cho mỗi tổ chức liên quan**. Có 6 incident (CRITICAL/HIGH) liên quan tài sản của 2 tổ chức, nên được tính cho cả hai.
10. `DiemRuiRo` của incident là điểm riêng theo khoảng (CRITICAL 80–100, HIGH 60–79, MEDIUM 35–59, LOW 5–34), không liên quan Risk Score tổ chức.
11. MITRE: 25 ID/tên/tactic là kỹ thuật cấp cao thật của ATT&CK Enterprise theo hiểu biết của mình; mình **không có mạng nên chưa đối chiếu trực tuyến**. Mỗi kỹ thuật chỉ ghi 1 tactic (một số kỹ thuật như T1078, T1053 thuộc nhiều tactic). Phần mô tả do mình tự viết. Cần kiểm tra lại với attack.mitre.org.

## C–D. File
- `seed_soc_incident_management.sql`: 41 câu INSERT nhiều dòng, một transaction, thứ tự theo khóa ngoại, không INSERT IGNORE, không tắt FOREIGN_KEY_CHECKS, không DROP/ALTER/TRUNCATE. Khối `DELETE` dọn dữ liệu cũ nằm trong comment, mặc định tắt.
- `verify_soc_incident_management.sql`: đếm bảng, 38 kiểm tra ràng buộc (kỳ vọng 0), danh sách SLA, Risk Score, độ đa dạng N-N.
- `queries_18_soc_incident_management.sql`: 18 truy vấn nghiệp vụ.

## Số lượng thực tế
| Bảng | Mục tiêu | Thực tế | | Bảng | Mục tiêu | Thực tế |
|---|---:|---:|---|---|---:|---:|
| to_chuc | 20 | 20 | | tai_san_incident | 250 | 250 |
| nhan_vien_soc | 30 | 30 | | incident_ioc | 300 | 305 |
| tai_san | 120 | 120 | | su_co_ky_thuat_mitre | 250 | 250 |
| su_co | 150 | 150 | | su_co_nhan_vien_soc | 300 | 363 |
| canh_bao | 450 | 450 | | hanh_dong_xu_ly | 350 | 364 |
| ioc | 100 | 100 | | lich_su_trang_thai | 400 | 414 |
| ky_thuat_mitre | 25 | 25 | | canh_bao_tai_san | 500 | 500 |

(`incident_ioc` = 305 vì 5 liên kết bổ sung để mọi IOC được dùng ít nhất một lần.)

## E. Cách chạy
**MySQL CLI (PowerShell, database đang trống, schema đã tạo):**
```powershell
mysql -u root -p --default-character-set=utf8mb4 soc_incident_management < seed_soc_incident_management.sql
mysql -u root -p --default-character-set=utf8mb4 soc_incident_management < verify_soc_incident_management.sql
```
**Workbench:** File → Open SQL Script → chạy toàn bộ (Ctrl+Shift+Enter). Nếu lỗi giữa chừng, chạy `ROLLBACK;` (file nằm trong một transaction).
**Nếu database đã có dữ liệu cũ** (ví dụ từ file seed trước): hãy sao lưu, rồi bỏ comment khối `DELETE` đầu file seed, hoặc dùng database mới. Mặc định file không xóa gì.

## F. Truy vấn trong 18 yêu cầu
Cả 18 truy vấn chạy được với schema hiện tại (xem `queries_18_...sql`), trừ hai điểm cần lưu ý:
- **Q15, Q16 (thưởng, lương):** chỉ tính được thưởng theo công thức giả định; tổng lương cần thêm nguồn dữ liệu (lương cơ bản). Nếu muốn, đề xuất migration riêng, chưa áp dụng.
- **Q17:** nguồn "đồng thời" định nghĩa theo khoảng `[ThoiGianXuLy, ThoiGianDong hoặc mốc hiện tại]`; schema không có ca trực nên không phân biệt thời gian nhân viên thực sự làm việc.

## G. Kết quả kiểm tra tính nhất quán
**Phương pháp:** môi trường của mình **không có MySQL**. Mình nạp đúng các `CREATE TABLE` trong `schema_soc_fixed.sql` vào **SQLite 3.45** (bỏ phần cú pháp riêng của MySQL) với `PRAGMA foreign_keys=ON`, chạy toàn bộ file seed, rồi chạy file kiểm tra và 18 truy vấn. Với các hàm MySQL không có trong SQLite (`TIMESTAMPDIFF`, `DATE_FORMAT`, `CONCAT`, `GROUP_CONCAT ... SEPARATOR`) mình dùng lớp tương thích tự viết. **Chưa chạy thử trên MySQL 8.0 thật**; bạn nên chạy `verify_...sql` sau khi import để xác nhận.

Kết quả trên SQLite: nạp thành công, `PRAGMA foreign_key_check` rỗng, 38/38 kiểm tra ràng buộc bằng 0 (khóa ngoại, thứ tự thời gian, chuỗi lịch sử liên tục và khớp trạng thái hiện tại, không CLOSED→NEW, CRITICAL luôn có L2/L3, CLOSED luôn có hành động, không trùng IOC/phân công/email).

Các tình huống nghiệp vụ có trong dữ liệu (đếm trên SQLite):
- Severity: 22 CRITICAL, 40 HIGH, 52 MEDIUM, 36 LOW. Trạng thái: 90 CLOSED, 14 NEW, 17 INVESTIGATING, 15 CONTAINED, 14 REMEDIATING.
- 5 incident CRITICAL đang NEW: 2 chưa quá 1 giờ (25 và 40 phút), 3 quá 1 giờ (130 phút, 300 phút, 3 ngày).
- Đang xử lý: 40 vi phạm SLA, 6 chưa vi phạm. Đã đóng: 54 đúng SLA, 36 trễ SLA.
- 9 incident NEW chưa có người phụ trách (Q18); 4 incident INVESTIGATING chưa có hành động xử lý.
- Q17: NV007 tối đa 18 incident đồng thời, NV006 13, NV015 12.
- Incident đóng trải đủ 10 tháng 2026 (T1–T10), phục vụ Q5/Q6/Q15/Q16.
- 6 incident liên quan hai tổ chức; IOC dùng chung nhiều nhất xuất hiện trong 24 incident; kỹ thuật MITRE xuất hiện nhiều nhất (T1059) trong 29 incident.
- Một số hạn chế: tổ chức có Risk Score cao nhất là tổ chức mức HIGH (không phải CRITICAL) do phân bố ngẫu nhiên có kiểm soát; loại cảnh báo Web Attack khá ít (13).
