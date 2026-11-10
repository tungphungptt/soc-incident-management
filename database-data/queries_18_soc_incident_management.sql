-- Compatibility copy. Authoritative file: sql/queries.sql
-- MySQL 8. SQL thuần; đổi các biến SET này trước khi chạy từng truy vấn.
SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;
SET @month_start = CAST(DATE_FORMAT(UTC_DATE(), '%Y-%m-01') AS DATE);
SET @month_end = DATE_ADD(@month_start, INTERVAL 1 MONTH);
SET @date_from = @month_start;
SET @date_to = @month_end;
SET @incident_id = 'DMINC004';
SET @now_ref = UTC_TIMESTAMP(6);
SET @overload_threshold = 5;
SET @min_alerts = 5;

-- Q01. Incident trong khoảng ngày [từ, đến), ưu tiên mức độ nghiêm trọng.
SELECT MaIncident,ThoiGianPhatHien,MucDoNghiemTrong,TrangThai
FROM su_co WHERE ThoiGianPhatHien>=@date_from AND ThoiGianPhatHien<@date_to
ORDER BY FIELD(MucDoNghiemTrong,'CRITICAL','HIGH','MEDIUM','LOW'),ThoiGianPhatHien,MaIncident;

-- Q02. Top 10 tài sản có nhiều cảnh báo nhất trong tháng được chọn.
SELECT a.MaTS,a.Ten,a.MaTC,COUNT(DISTINCT c.MaCanhBao) AS so_canh_bao
FROM tai_san a JOIN canh_bao_tai_san x ON x.MaTS=a.MaTS
JOIN canh_bao c ON c.MaCanhBao=x.MaCanhBao
WHERE c.ThoiGianPhatHien>=@month_start AND c.ThoiGianPhatHien<@month_end
GROUP BY a.MaTS,a.Ten,a.MaTC ORDER BY so_canh_bao DESC,a.MaTS LIMIT 10;

-- Q03. Tổ chức có nhiều Incident Critical+High nhất, giữ các tổ chức đồng hạng.
WITH pairs AS (SELECT DISTINCT a.MaTC,x.MaIncident FROM tai_san_incident x JOIN tai_san a ON a.MaTS=x.MaTS),
counts AS (SELECT o.MaTC,o.TenTC,COUNT(*) AS so_critical_high FROM pairs p
 JOIN to_chuc o ON o.MaTC=p.MaTC JOIN su_co s ON s.MaIncident=p.MaIncident
 WHERE s.MucDoNghiemTrong IN ('CRITICAL','HIGH') GROUP BY o.MaTC,o.TenTC)
SELECT * FROM counts WHERE so_critical_high=(SELECT MAX(so_critical_high) FROM counts) ORDER BY MaTC;

-- Q04. Incident đang xử lý và đã vi phạm SLA tại mốc @now_ref.
SELECT MaIncident,MucDoNghiemTrong,TrangThai,ThoiGianPhatHien,
 TIMESTAMPDIFF(SECOND,ThoiGianPhatHien,@now_ref) AS giay_da_troi,
 TIMESTAMPADD(MINUTE,CASE MucDoNghiemTrong WHEN 'CRITICAL' THEN 60 WHEN 'HIGH' THEN 240 WHEN 'MEDIUM' THEN 720 ELSE 1440 END,ThoiGianPhatHien) AS deadline
FROM su_co WHERE TrangThai IN ('INVESTIGATING','CONTAINED','REMEDIATING')
 AND @now_ref>TIMESTAMPADD(MINUTE,CASE MucDoNghiemTrong WHEN 'CRITICAL' THEN 60 WHEN 'HIGH' THEN 240 WHEN 'MEDIUM' THEN 720 ELSE 1440 END,ThoiGianPhatHien)
ORDER BY ThoiGianPhatHien,MaIncident;

-- Q05. Thời gian xử lý trung bình theo tháng đóng của từng nhân viên.
-- Khử trùng nhân viên+Incident nếu người đó có nhiều vai trò.
WITH participants AS (SELECT DISTINCT MaIncident,MaNV FROM su_co_nhan_vien_soc)
SELECT DATE_FORMAT(s.ThoiGianDong,'%Y-%m') AS thang,n.MaNV,n.HoTen,COUNT(*) AS so_incident_dong,
 ROUND(AVG(TIMESTAMPDIFF(MICROSECOND,s.ThoiGianPhatHien,s.ThoiGianDong)/60000000),1) AS tb_phut_xu_ly
FROM participants a JOIN su_co s ON s.MaIncident=a.MaIncident AND s.TrangThai='CLOSED'
JOIN nhan_vien_soc n ON n.MaNV=a.MaNV GROUP BY thang,n.MaNV,n.HoTen ORDER BY thang,n.MaNV;

-- Q06. Số Incident từng nhân viên tham gia theo tháng phát hiện.
SELECT DATE_FORMAT(s.ThoiGianPhatHien,'%Y-%m') AS thang,n.MaNV,n.HoTen,COUNT(DISTINCT s.MaIncident) AS so_incident
FROM su_co_nhan_vien_soc a JOIN su_co s ON s.MaIncident=a.MaIncident JOIN nhan_vien_soc n ON n.MaNV=a.MaNV
GROUP BY thang,n.MaNV,n.HoTen ORDER BY thang,so_incident DESC,n.MaNV;

-- Q07. Top 10 Technique MITRE xuất hiện trong nhiều Incident nhất.
SELECT k.MaKyThuat,k.TenKyThuat,k.ChienThuat,COUNT(DISTINCT x.MaIncident) AS so_incident
FROM ky_thuat_mitre k JOIN su_co_ky_thuat_mitre x ON x.MaKyThuat=k.MaKyThuat
GROUP BY k.MaKyThuat,k.TenKyThuat,k.ChienThuat ORDER BY so_incident DESC,k.MaKyThuat LIMIT 10;

-- Q08. Top 10 IOC (đúng cặp loại+giá trị) xuất hiện trong nhiều Incident nhất.
SELECT i.LoaiIOC,i.GiaTriIOC,i.MucDoTinCay,COUNT(DISTINCT x.MaIncident) AS so_incident
FROM ioc i JOIN incident_ioc x ON x.LoaiIOC=i.LoaiIOC AND x.GiaTriIOC=i.GiaTriIOC
GROUP BY i.LoaiIOC,i.GiaTriIOC,i.MucDoTinCay ORDER BY so_incident DESC,i.LoaiIOC,i.GiaTriIOC LIMIT 10;

-- Q09. Tất cả cặp Incident có cùng IOC; không ghép nhầm hai loại cùng giá trị.
SELECT a.MaIncident AS incident_1,b.MaIncident AS incident_2,COUNT(*) AS so_ioc_chung,
 GROUP_CONCAT(CONCAT(a.LoaiIOC,':',a.GiaTriIOC) ORDER BY a.LoaiIOC,a.GiaTriIOC SEPARATOR ' | ') AS cac_ioc_chung
FROM incident_ioc a JOIN incident_ioc b ON a.LoaiIOC=b.LoaiIOC AND a.GiaTriIOC=b.GiaTriIOC AND a.MaIncident<b.MaIncident
GROUP BY a.MaIncident,b.MaIncident ORDER BY so_ioc_chung DESC,incident_1,incident_2;

-- Q10. Tài sản nhiều cảnh báo nhưng chưa từng liên quan Incident CLOSED.
SELECT a.MaTS,a.Ten,a.MaTC,COUNT(DISTINCT x.MaCanhBao) AS so_canh_bao
FROM tai_san a JOIN canh_bao_tai_san x ON x.MaTS=a.MaTS GROUP BY a.MaTS,a.Ten,a.MaTC
HAVING COUNT(DISTINCT x.MaCanhBao)>=@min_alerts AND NOT EXISTS(
 SELECT 1 FROM tai_san_incident y JOIN su_co s ON s.MaIncident=y.MaIncident WHERE y.MaTS=a.MaTS AND s.TrangThai='CLOSED')
ORDER BY so_canh_bao DESC,a.MaTS;

-- Q11. Risk Score mọi tổ chức: Critical*10 + High*5 + Medium*2 + Low.
-- DISTINCT tổ chức+Incident; tổ chức không có Incident nhận 0, không cộng Low giả.
WITH pairs AS (SELECT DISTINCT a.MaTC,x.MaIncident FROM tai_san_incident x JOIN tai_san a ON a.MaTS=x.MaTS)
SELECT o.MaTC,o.TenTC,COALESCE(SUM(s.MucDoNghiemTrong='CRITICAL'),0) AS so_critical,COALESCE(SUM(s.MucDoNghiemTrong='HIGH'),0) AS so_high,
 COALESCE(SUM(CASE s.MucDoNghiemTrong WHEN 'CRITICAL' THEN 10 WHEN 'HIGH' THEN 5 WHEN 'MEDIUM' THEN 2 WHEN 'LOW' THEN 1 ELSE 0 END),0) AS risk_score,
 o.DiemRuiRo AS risk_score_luu
FROM to_chuc o LEFT JOIN pairs p ON p.MaTC=o.MaTC LEFT JOIN su_co s ON s.MaIncident=p.MaIncident
GROUP BY o.MaTC,o.TenTC,o.DiemRuiRo ORDER BY risk_score DESC,o.MaTC;

-- Q12. Top 10 tổ chức theo Risk Score, kèm thứ hạng.
WITH pairs AS (SELECT DISTINCT a.MaTC,x.MaIncident FROM tai_san_incident x JOIN tai_san a ON a.MaTS=x.MaTS),
risk AS (SELECT o.MaTC,o.TenTC,COALESCE(SUM(CASE s.MucDoNghiemTrong WHEN 'CRITICAL' THEN 10 WHEN 'HIGH' THEN 5 WHEN 'MEDIUM' THEN 2 WHEN 'LOW' THEN 1 ELSE 0 END),0) AS risk_score
 FROM to_chuc o LEFT JOIN pairs p ON p.MaTC=o.MaTC LEFT JOIN su_co s ON s.MaIncident=p.MaIncident GROUP BY o.MaTC,o.TenTC)
SELECT *,DENSE_RANK() OVER(ORDER BY risk_score DESC) AS hang FROM risk ORDER BY risk_score DESC,MaTC LIMIT 10;

-- Q13. Lịch sử đầy đủ một Incident: đổi trạng thái và hành động, theo thời gian.
SELECT * FROM (
 SELECT h.ThoiDiemThayDoi AS thoi_diem,'TRANG_THAI' AS loai,CONCAT(h.TrangThaiCu,' -> ',h.TrangThaiMoi) AS chi_tiet,
 h.MaNV,COALESCE(h.NguoiThucHien COLLATE utf8mb4_unicode_ci,n.HoTen) AS nguoi_thuc_hien,NULL AS thoi_luong_phut
 FROM lich_su_trang_thai h LEFT JOIN nhan_vien_soc n ON n.MaNV=h.MaNV WHERE h.MaIncident=@incident_id
 UNION ALL
 SELECT a.ThoiGianThucHien,'HANH_DONG',CONCAT(a.HanhDong,': ',a.KetQua),a.MaNV,n.HoTen,a.ThoiLuongPhut
 FROM hanh_dong_xu_ly a LEFT JOIN nhan_vien_soc n ON n.MaNV=a.MaNV WHERE a.MaIncident=@incident_id
) history ORDER BY thoi_diem,loai;

-- Q14. Nhân viên tham gia một Incident: vai trò, vị trí, thời điểm, số hành động.
SELECT n.MaNV,n.HoTen,n.SoNamKinhNghiem,a.VaiTro,a.ViTri,a.ThoiDiemThamGia,
 (SELECT COUNT(*) FROM hanh_dong_xu_ly h WHERE h.MaIncident=a.MaIncident AND h.MaNV=a.MaNV) AS so_hanh_dong
FROM su_co_nhan_vien_soc a JOIN nhan_vien_soc n ON n.MaNV=a.MaNV
WHERE a.MaIncident=@incident_id ORDER BY n.MaNV,a.VaiTro;

-- Q15. Thưởng từng nhân viên/từng Incident CLOSED, không thưởng nếu vi phạm SLA.
-- Chính sách thật: Critical 1.000.000 / High 500.000 / Medium 200.000 / Low 100.000.
WITH participants AS (SELECT DISTINCT MaIncident,MaNV FROM su_co_nhan_vien_soc)
SELECT s.MaIncident,s.MucDoNghiemTrong,s.ThoiGianDong,a.MaNV,
 CASE WHEN s.ThoiGianDong>TIMESTAMPADD(MINUTE,CASE s.MucDoNghiemTrong WHEN 'CRITICAL' THEN 60 WHEN 'HIGH' THEN 240 WHEN 'MEDIUM' THEN 720 ELSE 1440 END,s.ThoiGianPhatHien)
 THEN 0 ELSE p.amount END AS tien_thuong
FROM su_co s JOIN participants a ON a.MaIncident=s.MaIncident LEFT JOIN soc_bonus_policy p ON p.severity COLLATE utf8mb4_unicode_ci=s.MucDoNghiemTrong
WHERE s.TrangThai='CLOSED' ORDER BY s.ThoiGianDong,s.MaIncident,a.MaNV;

-- Q16. Tổng thưởng và lương+thưởng của từng nhân viên trong tháng được chọn.
-- Lương chưa cấu hình giữ NULL, không giả định bằng 0.
WITH participants AS (SELECT DISTINCT MaIncident,MaNV FROM su_co_nhan_vien_soc),
rewards AS (SELECT a.MaNV,s.MaIncident,CASE WHEN s.ThoiGianDong>TIMESTAMPADD(MINUTE,
 CASE s.MucDoNghiemTrong WHEN 'CRITICAL' THEN 60 WHEN 'HIGH' THEN 240 WHEN 'MEDIUM' THEN 720 ELSE 1440 END,s.ThoiGianPhatHien)
 THEN 0 ELSE p.amount END AS tien
 FROM participants a JOIN su_co s ON s.MaIncident=a.MaIncident LEFT JOIN soc_bonus_policy p ON p.severity COLLATE utf8mb4_unicode_ci=s.MucDoNghiemTrong
 WHERE s.TrangThai='CLOSED' AND s.ThoiGianDong>=@month_start AND s.ThoiGianDong<@month_end)
SELECT n.MaNV,n.HoTen,DATE_FORMAT(@month_start,'%Y-%m') AS thang,COUNT(r.MaIncident) AS so_incident_dong,
 COALESCE(SUM(r.tien),0) AS tong_thuong,l.base_salary AS luong_co_ban,l.base_salary+COALESCE(SUM(r.tien),0) AS luong_va_thuong
FROM nhan_vien_soc n LEFT JOIN rewards r ON r.MaNV=n.MaNV
LEFT JOIN soc_monthly_salary l ON l.employee_id COLLATE utf8mb4_unicode_ci=n.MaNV AND l.month=DATE_FORMAT(@month_start,'%Y-%m')
GROUP BY n.MaNV,n.HoTen,l.base_salary ORDER BY tong_thuong DESC,n.MaNV;

-- Q17. Nhân viên xử lý đồng thời quá ngưỡng: quét các khoảng [bắt đầu, kết thúc).
-- Không đếm NEW chưa nhận xử lý; khử trùng nhiều vai trò, chặn khoảng sau @now_ref.
WITH participants AS (SELECT DISTINCT MaIncident,MaNV FROM su_co_nhan_vien_soc),
intervals AS (SELECT a.MaNV,s.MaIncident,s.ThoiGianXuLy AS start_time,LEAST(COALESCE(s.ThoiGianDong,@now_ref),@now_ref) AS end_time
 FROM participants a JOIN su_co s ON s.MaIncident=a.MaIncident WHERE s.ThoiGianXuLy IS NOT NULL AND s.ThoiGianXuLy<@now_ref),
events AS (SELECT MaNV,start_time AS t,1 AS d FROM intervals WHERE start_time<end_time
 UNION ALL SELECT MaNV,end_time,-1 FROM intervals WHERE start_time<end_time),
running AS (SELECT MaNV,t,SUM(d) OVER(PARTITION BY MaNV ORDER BY t,d ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS active_count FROM events)
SELECT n.MaNV,n.HoTen,MAX(r.active_count) AS dong_thoi_toi_da
FROM running r JOIN nhan_vien_soc n ON n.MaNV=r.MaNV GROUP BY n.MaNV,n.HoTen
HAVING MAX(r.active_count)>=@overload_threshold ORDER BY dong_thoi_toi_da DESC,n.MaNV;

-- Q18. Incident chưa có bất kỳ nhân viên phụ trách nào.
SELECT s.MaIncident,s.MucDoNghiemTrong,s.TrangThai,s.ThoiGianPhatHien
FROM su_co s WHERE NOT EXISTS(SELECT 1 FROM su_co_nhan_vien_soc a WHERE a.MaIncident=s.MaIncident)
ORDER BY FIELD(s.MucDoNghiemTrong,'CRITICAL','HIGH','MEDIUM','LOW'),s.ThoiGianPhatHien,s.MaIncident;
