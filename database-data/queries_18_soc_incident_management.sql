-- =====================================================================
-- queries_18_soc_incident_management.sql  (MySQL 8.0+)
-- 18 truy van nghiep vu. Tham so (thang, ma incident, moc NOW_REF) viet truc tiep
-- de de chinh. NOW_REF = '2026-10-21 12:00:00'.
-- SLA (phut): CRITICAL 60, HIGH 240, MEDIUM 720, LOW 1440.
-- Quy tac to chuc cua incident: SU_CO -> TAI_SAN_INCIDENT -> TAI_SAN -> TO_CHUC,
-- dung SELECT DISTINCT (MaTC, MaIncident) de 1 incident chi tinh 1 lan / to chuc.
-- Incident lien quan tai san cua nhieu to chuc: tinh 1 lan cho MOI to chuc lien quan.
-- =====================================================================
USE soc_incident_management;

-- Q1. Incident trong khoang thoi gian, sap xep theo severity
SELECT MaIncident, ThoiGianPhatHien, MucDoNghiemTrong, TrangThai
FROM su_co
WHERE ThoiGianPhatHien >= '2026-03-01 00:00:00' AND ThoiGianPhatHien < '2026-04-01 00:00:00'
ORDER BY CASE MucDoNghiemTrong WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 WHEN 'MEDIUM' THEN 3 ELSE 4 END, ThoiGianPhatHien;

-- Q2. Top 10 tai san co nhieu canh bao nhat trong mot thang (thang 2026-09)
SELECT ts.MaTS, ts.Ten, ts.MaTC, COUNT(DISTINCT cb.MaCanhBao) AS so_canh_bao
FROM canh_bao_tai_san x
JOIN canh_bao cb ON cb.MaCanhBao = x.MaCanhBao
JOIN tai_san ts ON ts.MaTS = x.MaTS
WHERE cb.ThoiGianPhatHien >= '2026-09-01 00:00:00' AND cb.ThoiGianPhatHien < '2026-10-01 00:00:00'
GROUP BY ts.MaTS, ts.Ten, ts.MaTC
ORDER BY so_canh_bao DESC, ts.MaTS
LIMIT 10;

-- Q3. To chuc co nhieu incident CRITICAL + HIGH nhat
WITH inc_org AS (
  SELECT DISTINCT t.MaTC, x.MaIncident FROM tai_san_incident x JOIN tai_san t ON t.MaTS = x.MaTS
)
SELECT o.MaTC, o.TenTC, o.MucDoQuanTrong, COUNT(*) AS so_incident_critical_high
FROM inc_org io
JOIN su_co s ON s.MaIncident = io.MaIncident AND s.MucDoNghiemTrong IN ('CRITICAL', 'HIGH')
JOIN to_chuc o ON o.MaTC = io.MaTC
GROUP BY o.MaTC, o.TenTC, o.MucDoQuanTrong
ORDER BY so_incident_critical_high DESC, o.MaTC
LIMIT 10;

-- Q4. Incident dang xu ly va vi pham SLA (tinh tu ThoiGianPhatHien den NOW_REF)
SELECT s.MaIncident, s.MucDoNghiemTrong, s.TrangThai, s.ThoiGianPhatHien,
       TIMESTAMPDIFF(MINUTE, s.ThoiGianPhatHien, '2026-10-21 12:00:00') AS phut_da_troi,
       CASE s.MucDoNghiemTrong WHEN 'CRITICAL' THEN 60 WHEN 'HIGH' THEN 240 WHEN 'MEDIUM' THEN 720 ELSE 1440 END AS sla_phut
FROM su_co s
WHERE s.TrangThai IN ('INVESTIGATING', 'CONTAINED', 'REMEDIATING')
  AND TIMESTAMPDIFF(MINUTE, s.ThoiGianPhatHien, '2026-10-21 12:00:00') >
      CASE s.MucDoNghiemTrong WHEN 'CRITICAL' THEN 60 WHEN 'HIGH' THEN 240 WHEN 'MEDIUM' THEN 720 ELSE 1440 END
ORDER BY s.ThoiGianPhatHien;

-- Q5. Thoi gian xu ly trung binh (phut) cua tung nhan vien theo thang dong incident
--     (incident CLOSED: ThoiGianDong - ThoiGianPhatHien; moi incident tinh cho moi nhan vien duoc phan cong)
SELECT DATE_FORMAT(s.ThoiGianDong, '%Y-%m') AS thang, nv.MaNV, nv.HoTen,
       COUNT(*) AS so_incident_dong, ROUND(AVG(TIMESTAMPDIFF(MINUTE, s.ThoiGianPhatHien, s.ThoiGianDong)), 1) AS tb_phut_xu_ly
FROM su_co_nhan_vien_soc a
JOIN su_co s ON s.MaIncident = a.MaIncident AND s.TrangThai = 'CLOSED'
JOIN nhan_vien_soc nv ON nv.MaNV = a.MaNV
GROUP BY thang, nv.MaNV, nv.HoTen
ORDER BY thang, nv.MaNV;

-- Q6. So incident moi nhan vien tham gia theo tung thang (theo ThoiGianPhatHien)
SELECT DATE_FORMAT(s.ThoiGianPhatHien, '%Y-%m') AS thang, nv.MaNV, nv.HoTen, COUNT(DISTINCT s.MaIncident) AS so_incident
FROM su_co_nhan_vien_soc a
JOIN su_co s ON s.MaIncident = a.MaIncident
JOIN nhan_vien_soc nv ON nv.MaNV = a.MaNV
GROUP BY thang, nv.MaNV, nv.HoTen
ORDER BY thang, so_incident DESC, nv.MaNV;

-- Q7. Ky thuat MITRE ATT&CK xuat hien nhieu nhat
SELECT k.MaKyThuat, k.TenKyThuat, k.ChienThuat, COUNT(DISTINCT x.MaIncident) AS so_incident
FROM su_co_ky_thuat_mitre x JOIN ky_thuat_mitre k ON k.MaKyThuat = x.MaKyThuat
GROUP BY k.MaKyThuat, k.TenKyThuat, k.ChienThuat
ORDER BY so_incident DESC, k.MaKyThuat
LIMIT 10;

-- Q8. IOC xuat hien trong nhieu incident nhat
SELECT i.GiaTriIOC, i.LoaiIOC, i.MucDoTinCay, COUNT(DISTINCT x.MaIncident) AS so_incident
FROM incident_ioc x JOIN ioc i ON i.GiaTriIOC = x.GiaTriIOC
GROUP BY i.GiaTriIOC, i.LoaiIOC, i.MucDoTinCay
ORDER BY so_incident DESC, i.GiaTriIOC
LIMIT 10;

-- Q9. Cac cap incident co chung IOC
SELECT a.MaIncident AS incident_1, b.MaIncident AS incident_2, COUNT(*) AS so_ioc_chung, GROUP_CONCAT(a.GiaTriIOC SEPARATOR ' | ') AS cac_ioc_chung
FROM incident_ioc a JOIN incident_ioc b ON a.GiaTriIOC = b.GiaTriIOC AND a.MaIncident < b.MaIncident
GROUP BY a.MaIncident, b.MaIncident
ORDER BY so_ioc_chung DESC, incident_1, incident_2
LIMIT 50;

-- Q10. Tai san co nhieu canh bao (>= 5) nhung chua tung lien quan incident CLOSED
SELECT ts.MaTS, ts.Ten, ts.MaTC, COUNT(DISTINCT x.MaCanhBao) AS so_canh_bao
FROM tai_san ts JOIN canh_bao_tai_san x ON x.MaTS = ts.MaTS
GROUP BY ts.MaTS, ts.Ten, ts.MaTC
HAVING COUNT(DISTINCT x.MaCanhBao) >= 5
   AND NOT EXISTS (SELECT 1 FROM tai_san_incident ti JOIN su_co s ON s.MaIncident = ti.MaIncident
                   WHERE ti.MaTS = ts.MaTS AND s.TrangThai = 'CLOSED')
ORDER BY so_canh_bao DESC, ts.MaTS;

-- Q11. Risk Score cua tung to chuc = Critical*10 + High*5 + Medium*2 + Low
WITH inc_org AS (
  SELECT DISTINCT t.MaTC, x.MaIncident FROM tai_san_incident x JOIN tai_san t ON t.MaTS = x.MaTS
)
SELECT o.MaTC, o.TenTC,
       SUM(CASE WHEN s.MucDoNghiemTrong = 'CRITICAL' THEN 1 ELSE 0 END) AS so_critical,
       SUM(CASE WHEN s.MucDoNghiemTrong = 'HIGH' THEN 1 ELSE 0 END) AS so_high,
       SUM(CASE WHEN s.MucDoNghiemTrong = 'MEDIUM' THEN 1 ELSE 0 END) AS so_medium,
       SUM(CASE WHEN s.MucDoNghiemTrong = 'LOW' THEN 1 ELSE 0 END) AS so_low,
       SUM(CASE s.MucDoNghiemTrong WHEN 'CRITICAL' THEN 10 WHEN 'HIGH' THEN 5 WHEN 'MEDIUM' THEN 2 ELSE 1 END) AS risk_score
FROM to_chuc o
LEFT JOIN inc_org io ON io.MaTC = o.MaTC
LEFT JOIN su_co s ON s.MaIncident = io.MaIncident
GROUP BY o.MaTC, o.TenTC
ORDER BY risk_score DESC, o.MaTC;

-- Q12. Top 10 to chuc co Risk Score cao nhat
WITH inc_org AS (
  SELECT DISTINCT t.MaTC, x.MaIncident FROM tai_san_incident x JOIN tai_san t ON t.MaTS = x.MaTS
)
SELECT o.MaTC, o.TenTC,
       SUM(CASE s.MucDoNghiemTrong WHEN 'CRITICAL' THEN 10 WHEN 'HIGH' THEN 5 WHEN 'MEDIUM' THEN 2 ELSE 1 END) AS risk_score,
       RANK() OVER (ORDER BY SUM(CASE s.MucDoNghiemTrong WHEN 'CRITICAL' THEN 10 WHEN 'HIGH' THEN 5 WHEN 'MEDIUM' THEN 2 ELSE 1 END) DESC) AS hang
FROM to_chuc o JOIN inc_org io ON io.MaTC = o.MaTC JOIN su_co s ON s.MaIncident = io.MaIncident
GROUP BY o.MaTC, o.TenTC
ORDER BY risk_score DESC, o.MaTC
LIMIT 10;

-- Q13. Toan bo lich su xu ly cua mot incident (INC057): doi trang thai + hanh dong, theo thoi gian
SELECT thoi_diem, loai, chi_tiet, MaNV, HoTen FROM (
  SELECT h.ThoiDiemThayDoi AS thoi_diem, 'DOI TRANG THAI' AS loai, CONCAT(h.TrangThaiCu, ' -> ', h.TrangThaiMoi) AS chi_tiet, h.MaNV, nv.HoTen
  FROM lich_su_trang_thai h JOIN nhan_vien_soc nv ON nv.MaNV = h.MaNV WHERE h.MaIncident = 'INC057'
  UNION ALL
  SELECT a.ThoiGianThucHien, 'HANH DONG', CONCAT(a.HanhDong, ': ', a.KetQua), a.MaNV, nv.HoTen
  FROM hanh_dong_xu_ly a JOIN nhan_vien_soc nv ON nv.MaNV = a.MaNV WHERE a.MaIncident = 'INC057'
) t ORDER BY thoi_diem;

-- Q14. Toan bo nhan vien tham gia xu ly mot incident (INC057)
SELECT a.MaNV, nv.HoTen, nv.SoNamKinhNghiem, a.ViTri, a.VaiTro,
       (SELECT COUNT(*) FROM hanh_dong_xu_ly h WHERE h.MaIncident = a.MaIncident AND h.MaNV = a.MaNV) AS so_hanh_dong
FROM su_co_nhan_vien_soc a JOIN nhan_vien_soc nv ON nv.MaNV = a.MaNV
WHERE a.MaIncident = 'INC057'
ORDER BY a.ViTri, a.MaNV;

-- Q15. Thuong theo severity cho tung (incident, nhan vien); KHONG thuong neu vi pham SLA.
--      GIA DINH (schema khong co bang thuong): chi incident CLOSED, moi nhan vien duoc phan cong nhan day du muc thuong.
--      Muc thuong (VND) la THAM SO GIA LAP: CRITICAL 1.000.000 / HIGH 600.000 / MEDIUM 300.000 / LOW 100.000.
SELECT s.MaIncident, s.MucDoNghiemTrong, a.MaNV,
       TIMESTAMPDIFF(MINUTE, s.ThoiGianPhatHien, s.ThoiGianDong) AS phut_xu_ly,
       CASE s.MucDoNghiemTrong WHEN 'CRITICAL' THEN 60 WHEN 'HIGH' THEN 240 WHEN 'MEDIUM' THEN 720 ELSE 1440 END AS sla_phut,
       CASE WHEN TIMESTAMPDIFF(MINUTE, s.ThoiGianPhatHien, s.ThoiGianDong) >
                 CASE s.MucDoNghiemTrong WHEN 'CRITICAL' THEN 60 WHEN 'HIGH' THEN 240 WHEN 'MEDIUM' THEN 720 ELSE 1440 END
            THEN 0
            ELSE CASE s.MucDoNghiemTrong WHEN 'CRITICAL' THEN 1000000 WHEN 'HIGH' THEN 600000 WHEN 'MEDIUM' THEN 300000 ELSE 100000 END
       END AS tien_thuong
FROM su_co s JOIN su_co_nhan_vien_soc a ON a.MaIncident = s.MaIncident
WHERE s.TrangThai = 'CLOSED'
ORDER BY s.ThoiGianDong, s.MaIncident, a.MaNV;

-- Q16. Tong thuong cua nhan vien theo thang dong incident (cung gia dinh Q15).
--      LUONG CO BAN: schema khong co du lieu -> KHONG the tinh tong luong, chi tinh duoc tong thuong.
WITH thuong AS (
  SELECT DATE_FORMAT(s.ThoiGianDong, '%Y-%m') AS thang, a.MaNV,
         CASE WHEN TIMESTAMPDIFF(MINUTE, s.ThoiGianPhatHien, s.ThoiGianDong) >
                   CASE s.MucDoNghiemTrong WHEN 'CRITICAL' THEN 60 WHEN 'HIGH' THEN 240 WHEN 'MEDIUM' THEN 720 ELSE 1440 END
              THEN 0
              ELSE CASE s.MucDoNghiemTrong WHEN 'CRITICAL' THEN 1000000 WHEN 'HIGH' THEN 600000 WHEN 'MEDIUM' THEN 300000 ELSE 100000 END
         END AS tien
  FROM su_co s JOIN su_co_nhan_vien_soc a ON a.MaIncident = s.MaIncident
  WHERE s.TrangThai = 'CLOSED'
)
SELECT t.thang, t.MaNV, nv.HoTen, COUNT(*) AS so_incident_dong, SUM(t.tien) AS tong_thuong
FROM thuong t JOIN nhan_vien_soc nv ON nv.MaNV = t.MaNV
GROUP BY t.thang, t.MaNV, nv.HoTen
ORDER BY t.thang, tong_thuong DESC, t.MaNV;

-- Q17. Nhan vien xu ly qua nhieu incident dong thoi (nguong >= 5 incident cung luc tai NOW_REF-based timeline).
--      Khoang thoi gian xu ly cua incident = [ThoiGianXuLy (neu NULL thi ThoiGianPhatHien), ThoiGianDong (neu NULL thi NOW_REF)].
--      Quet su kien: +1 khi bat dau, -1 khi ket thuc; ket thuc xu ly truoc bat dau khi trung thoi diem.
WITH iv AS (
  SELECT a.MaNV, s.MaIncident,
         COALESCE(s.ThoiGianXuLy, s.ThoiGianPhatHien) AS bat_dau,
         COALESCE(s.ThoiGianDong, '2026-10-21 12:00:00') AS ket_thuc
  FROM su_co_nhan_vien_soc a JOIN su_co s ON s.MaIncident = a.MaIncident
),
ev AS (
  SELECT MaNV, bat_dau AS t, 1 AS d FROM iv
  UNION ALL
  SELECT MaNV, ket_thuc AS t, -1 AS d FROM iv
),
run AS (
  SELECT MaNV, t, SUM(d) OVER (PARTITION BY MaNV ORDER BY t, d ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS dang_xu_ly
  FROM ev
)
SELECT r.MaNV, nv.HoTen, MAX(r.dang_xu_ly) AS so_incident_dong_thoi_toi_da
FROM run r JOIN nhan_vien_soc nv ON nv.MaNV = r.MaNV
GROUP BY r.MaNV, nv.HoTen
HAVING MAX(r.dang_xu_ly) >= 5
ORDER BY so_incident_dong_thoi_toi_da DESC, r.MaNV;

-- Q18. Incident chua co nguoi phu trach
SELECT s.MaIncident, s.MucDoNghiemTrong, s.TrangThai, s.ThoiGianPhatHien
FROM su_co s
WHERE NOT EXISTS (SELECT 1 FROM su_co_nhan_vien_soc a WHERE a.MaIncident = s.MaIncident)
ORDER BY s.ThoiGianPhatHien;
