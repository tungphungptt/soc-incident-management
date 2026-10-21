-- =====================================================================
-- verify_soc_incident_management.sql  (MySQL 8.0+)
-- Moc thoi gian tham chieu: '2026-10-21 12:00:00'
-- Cac khoi "KIEM TRA RANG BUOC" can tra ve so_vi_pham = 0.
-- =====================================================================
USE soc_incident_management;

-- ---- A. So luong ban ghi tung bang
SELECT 'to_chuc' AS bang, COUNT(*) AS so_ban_ghi FROM to_chuc UNION ALL
SELECT 'nhan_vien_soc', COUNT(*) FROM nhan_vien_soc UNION ALL
SELECT 'tai_san', COUNT(*) FROM tai_san UNION ALL
SELECT 'su_co', COUNT(*) FROM su_co UNION ALL
SELECT 'canh_bao', COUNT(*) FROM canh_bao UNION ALL
SELECT 'ioc', COUNT(*) FROM ioc UNION ALL
SELECT 'ky_thuat_mitre', COUNT(*) FROM ky_thuat_mitre UNION ALL
SELECT 'canh_bao_tai_san', COUNT(*) FROM canh_bao_tai_san UNION ALL
SELECT 'tai_san_incident', COUNT(*) FROM tai_san_incident UNION ALL
SELECT 'incident_ioc', COUNT(*) FROM incident_ioc UNION ALL
SELECT 'su_co_ky_thuat_mitre', COUNT(*) FROM su_co_ky_thuat_mitre UNION ALL
SELECT 'su_co_nhan_vien_soc', COUNT(*) FROM su_co_nhan_vien_soc UNION ALL
SELECT 'hanh_dong_xu_ly', COUNT(*) FROM hanh_dong_xu_ly UNION ALL
SELECT 'lich_su_trang_thai', COUNT(*) FROM lich_su_trang_thai;

-- ---- B. Phan bo incident theo severity x trang thai
SELECT MucDoNghiemTrong, TrangThai, COUNT(*) AS so_incident
FROM su_co GROUP BY MucDoNghiemTrong, TrangThai ORDER BY MucDoNghiemTrong, TrangThai;

-- ---- C. KIEM TRA RANG BUOC (ky vong so_vi_pham = 0)
SELECT 'FK: canh_bao -> su_co' AS kiem_tra, COUNT(*) AS so_vi_pham FROM canh_bao x LEFT JOIN su_co y ON y.MaIncident = x.MaIncident WHERE y.MaIncident IS NULL UNION ALL
SELECT 'FK: canh_bao_tai_san -> canh_bao', COUNT(*) FROM canh_bao_tai_san x LEFT JOIN canh_bao y ON y.MaCanhBao = x.MaCanhBao WHERE y.MaCanhBao IS NULL UNION ALL
SELECT 'FK: canh_bao_tai_san -> tai_san', COUNT(*) FROM canh_bao_tai_san x LEFT JOIN tai_san y ON y.MaTS = x.MaTS WHERE y.MaTS IS NULL UNION ALL
SELECT 'FK: tai_san -> to_chuc', COUNT(*) FROM tai_san x LEFT JOIN to_chuc y ON y.MaTC = x.MaTC WHERE y.MaTC IS NULL UNION ALL
SELECT 'FK: tai_san_incident -> tai_san', COUNT(*) FROM tai_san_incident x LEFT JOIN tai_san y ON y.MaTS = x.MaTS WHERE y.MaTS IS NULL UNION ALL
SELECT 'FK: tai_san_incident -> su_co', COUNT(*) FROM tai_san_incident x LEFT JOIN su_co y ON y.MaIncident = x.MaIncident WHERE y.MaIncident IS NULL UNION ALL
SELECT 'FK: incident_ioc -> su_co', COUNT(*) FROM incident_ioc x LEFT JOIN su_co y ON y.MaIncident = x.MaIncident WHERE y.MaIncident IS NULL UNION ALL
SELECT 'FK: incident_ioc -> ioc', COUNT(*) FROM incident_ioc x LEFT JOIN ioc y ON y.GiaTriIOC = x.GiaTriIOC WHERE y.GiaTriIOC IS NULL UNION ALL
SELECT 'FK: su_co_ky_thuat_mitre -> su_co', COUNT(*) FROM su_co_ky_thuat_mitre x LEFT JOIN su_co y ON y.MaIncident = x.MaIncident WHERE y.MaIncident IS NULL UNION ALL
SELECT 'FK: su_co_ky_thuat_mitre -> ky_thuat_mitre', COUNT(*) FROM su_co_ky_thuat_mitre x LEFT JOIN ky_thuat_mitre y ON y.MaKyThuat = x.MaKyThuat WHERE y.MaKyThuat IS NULL UNION ALL
SELECT 'FK: su_co_nhan_vien_soc -> su_co', COUNT(*) FROM su_co_nhan_vien_soc x LEFT JOIN su_co y ON y.MaIncident = x.MaIncident WHERE y.MaIncident IS NULL UNION ALL
SELECT 'FK: su_co_nhan_vien_soc -> nhan_vien_soc', COUNT(*) FROM su_co_nhan_vien_soc x LEFT JOIN nhan_vien_soc y ON y.MaNV = x.MaNV WHERE y.MaNV IS NULL UNION ALL
SELECT 'FK: hanh_dong_xu_ly -> su_co', COUNT(*) FROM hanh_dong_xu_ly x LEFT JOIN su_co y ON y.MaIncident = x.MaIncident WHERE y.MaIncident IS NULL UNION ALL
SELECT 'FK: hanh_dong_xu_ly -> nhan_vien_soc', COUNT(*) FROM hanh_dong_xu_ly x LEFT JOIN nhan_vien_soc y ON y.MaNV = x.MaNV WHERE y.MaNV IS NULL UNION ALL
SELECT 'FK: lich_su_trang_thai -> su_co', COUNT(*) FROM lich_su_trang_thai x LEFT JOIN su_co y ON y.MaIncident = x.MaIncident WHERE y.MaIncident IS NULL UNION ALL
SELECT 'FK: lich_su_trang_thai -> nhan_vien_soc', COUNT(*) FROM lich_su_trang_thai x LEFT JOIN nhan_vien_soc y ON y.MaNV = x.MaNV WHERE y.MaNV IS NULL UNION ALL
SELECT 'Thu tu thoi gian su_co sai', COUNT(*) FROM su_co WHERE ThoiGianPhatHien < ThoiGianBatDau OR ThoiGianXuLy < ThoiGianPhatHien OR ThoiGianDong < ThoiGianXuLy UNION ALL
SELECT 'NEW nhung co moc XuLy/Dong', COUNT(*) FROM su_co WHERE TrangThai = 'NEW' AND (ThoiGianXuLy IS NOT NULL OR ThoiGianDong IS NOT NULL) UNION ALL
SELECT 'Khong NEW nhung thieu ThoiGianXuLy', COUNT(*) FROM su_co WHERE TrangThai <> 'NEW' AND ThoiGianXuLy IS NULL UNION ALL
SELECT 'CLOSED thieu ThoiGianDong', COUNT(*) FROM su_co WHERE TrangThai = 'CLOSED' AND ThoiGianDong IS NULL UNION ALL
SELECT 'Chua CLOSED nhung co ThoiGianDong', COUNT(*) FROM su_co WHERE TrangThai <> 'CLOSED' AND ThoiGianDong IS NOT NULL UNION ALL
SELECT 'Incident khong co canh bao', COUNT(*) FROM su_co s WHERE NOT EXISTS (SELECT 1 FROM canh_bao c WHERE c.MaIncident = s.MaIncident) UNION ALL
SELECT 'Incident khong co tai san', COUNT(*) FROM su_co s WHERE NOT EXISTS (SELECT 1 FROM tai_san_incident t WHERE t.MaIncident = s.MaIncident) UNION ALL
SELECT 'Canh bao gan tai san ngoai tap tai san cua incident', COUNT(*) FROM canh_bao_tai_san x JOIN canh_bao c ON c.MaCanhBao = x.MaCanhBao WHERE NOT EXISTS (SELECT 1 FROM tai_san_incident t WHERE t.MaIncident = c.MaIncident AND t.MaTS = x.MaTS) UNION ALL
SELECT 'Canh bao khong co tai san', COUNT(*) FROM canh_bao c WHERE NOT EXISTS (SELECT 1 FROM canh_bao_tai_san x WHERE x.MaCanhBao = c.MaCanhBao) UNION ALL
SELECT 'Canh bao o tuong lai (sau NOW_REF)', COUNT(*) FROM canh_bao WHERE ThoiGianPhatHien > '2026-10-21 12:00:00' UNION ALL
SELECT 'Incident CRITICAL thieu nhan vien L2/L3', COUNT(*) FROM su_co s WHERE s.MucDoNghiemTrong = 'CRITICAL' AND NOT EXISTS (SELECT 1 FROM su_co_nhan_vien_soc a WHERE a.MaIncident = s.MaIncident AND a.VaiTro IN ('SOC Analyst L2', 'SOC Analyst L3')) UNION ALL
SELECT 'Incident CLOSED khong co hanh dong xu ly', COUNT(*) FROM su_co s WHERE s.TrangThai = 'CLOSED' AND NOT EXISTS (SELECT 1 FROM hanh_dong_xu_ly h WHERE h.MaIncident = s.MaIncident) UNION ALL
SELECT 'Hanh dong ngoai cua so XuLy..Dong/NOW', COUNT(*) FROM hanh_dong_xu_ly h JOIN su_co s ON s.MaIncident = h.MaIncident WHERE h.ThoiGianThucHien < s.ThoiGianXuLy OR h.ThoiGianThucHien > COALESCE(s.ThoiGianDong, '2026-10-21 12:00:00') UNION ALL
SELECT 'Hanh dong do nhan vien khong duoc phan cong', COUNT(*) FROM hanh_dong_xu_ly h WHERE NOT EXISTS (SELECT 1 FROM su_co_nhan_vien_soc a WHERE a.MaIncident = h.MaIncident AND a.MaNV = h.MaNV) UNION ALL
SELECT 'Lich su do nhan vien khong duoc phan cong', COUNT(*) FROM lich_su_trang_thai h WHERE NOT EXISTS (SELECT 1 FROM su_co_nhan_vien_soc a WHERE a.MaIncident = h.MaIncident AND a.MaNV = h.MaNV) UNION ALL
SELECT 'Lich su: chuyen tu CLOSED', COUNT(*) FROM lich_su_trang_thai WHERE TrangThaiCu = 'CLOSED' UNION ALL
SELECT 'Lich su: quay lai trang thai thap hon', COUNT(*) FROM lich_su_trang_thai WHERE (CASE TrangThaiMoi WHEN 'NEW' THEN 1 WHEN 'INVESTIGATING' THEN 2 WHEN 'CONTAINED' THEN 3 WHEN 'REMEDIATING' THEN 4 WHEN 'CLOSED' THEN 5 END) <= (CASE TrangThaiCu WHEN 'NEW' THEN 1 WHEN 'INVESTIGATING' THEN 2 WHEN 'CONTAINED' THEN 3 WHEN 'REMEDIATING' THEN 4 WHEN 'CLOSED' THEN 5 END) UNION ALL
SELECT 'Lich su: chuoi khong lien tuc', COUNT(*) FROM (SELECT TrangThaiCu, LAG(TrangThaiMoi) OVER (PARTITION BY MaIncident ORDER BY ThoiDiemThayDoi, MaLichSu) AS prev FROM lich_su_trang_thai) t WHERE (prev IS NULL AND TrangThaiCu <> 'NEW') OR (prev IS NOT NULL AND prev <> TrangThaiCu) UNION ALL
SELECT 'Lich su: trang thai cuoi khac su_co.TrangThai', COUNT(*) FROM su_co s JOIN (SELECT MaIncident, TrangThaiMoi, ROW_NUMBER() OVER (PARTITION BY MaIncident ORDER BY ThoiDiemThayDoi DESC, MaLichSu DESC) AS rn FROM lich_su_trang_thai) h ON h.MaIncident = s.MaIncident AND h.rn = 1 WHERE h.TrangThaiMoi <> s.TrangThai UNION ALL
SELECT 'Incident khong NEW nhung khong co lich su', COUNT(*) FROM su_co s WHERE s.TrangThai <> 'NEW' AND NOT EXISTS (SELECT 1 FROM lich_su_trang_thai h WHERE h.MaIncident = s.MaIncident) UNION ALL
SELECT 'IOC trung (LoaiIOC, GiaTriIOC)', COUNT(*) FROM (SELECT LoaiIOC, GiaTriIOC FROM ioc GROUP BY LoaiIOC, GiaTriIOC HAVING COUNT(*) > 1) d UNION ALL
SELECT 'Phan cong trung (MaIncident, MaNV)', COUNT(*) FROM (SELECT MaIncident, MaNV FROM su_co_nhan_vien_soc GROUP BY MaIncident, MaNV HAVING COUNT(*) > 1) d UNION ALL
SELECT 'Email nhan vien trung', COUNT(*) FROM (SELECT Email FROM nhan_vien_soc GROUP BY Email HAVING COUNT(*) > 1) d UNION ALL
SELECT 'Gia tri MucDo ngoai tap CRITICAL/HIGH/MEDIUM/LOW', COUNT(*) FROM su_co WHERE MucDoNghiemTrong NOT IN ('CRITICAL','HIGH','MEDIUM','LOW');

-- ---- D. Incident dang xu ly vi pham SLA tai moc NOW_REF = 2026-10-21 12:00:00
SELECT s.MaIncident, s.MucDoNghiemTrong, s.TrangThai, s.ThoiGianPhatHien,
       TIMESTAMPDIFF(MINUTE, s.ThoiGianPhatHien, '2026-10-21 12:00:00') AS phut_da_troi,
       CASE s.MucDoNghiemTrong WHEN 'CRITICAL' THEN 60 WHEN 'HIGH' THEN 240 WHEN 'MEDIUM' THEN 720 ELSE 1440 END AS sla_phut,
       CASE WHEN TIMESTAMPDIFF(MINUTE, s.ThoiGianPhatHien, '2026-10-21 12:00:00') >
            CASE s.MucDoNghiemTrong WHEN 'CRITICAL' THEN 60 WHEN 'HIGH' THEN 240 WHEN 'MEDIUM' THEN 720 ELSE 1440 END
            THEN 'VI PHAM' ELSE 'TRONG SLA' END AS ket_luan
FROM su_co s
WHERE s.TrangThai IN ('INVESTIGATING', 'CONTAINED', 'REMEDIATING')
ORDER BY ket_luan DESC, s.ThoiGianPhatHien;

-- ---- E. Risk Score tung to chuc (moi incident chi tinh 1 lan / to chuc)
WITH inc_org AS (
  SELECT DISTINCT t.MaTC, x.MaIncident FROM tai_san_incident x JOIN tai_san t ON t.MaTS = x.MaTS
)
SELECT o.MaTC, o.TenTC, o.MucDoQuanTrong,
       SUM(CASE WHEN s.MucDoNghiemTrong = 'CRITICAL' THEN 1 ELSE 0 END) AS so_critical,
       SUM(CASE WHEN s.MucDoNghiemTrong = 'HIGH' THEN 1 ELSE 0 END) AS so_high,
       SUM(CASE WHEN s.MucDoNghiemTrong = 'MEDIUM' THEN 1 ELSE 0 END) AS so_medium,
       SUM(CASE WHEN s.MucDoNghiemTrong = 'LOW' THEN 1 ELSE 0 END) AS so_low,
       SUM(CASE s.MucDoNghiemTrong WHEN 'CRITICAL' THEN 10 WHEN 'HIGH' THEN 5 WHEN 'MEDIUM' THEN 2 ELSE 1 END) AS risk_score
FROM to_chuc o JOIN inc_org io ON io.MaTC = o.MaTC JOIN su_co s ON s.MaIncident = io.MaIncident
GROUP BY o.MaTC, o.TenTC, o.MucDoQuanTrong
ORDER BY risk_score DESC, o.MaTC;

-- ---- F. Do da dang cua cac bang lien ket N-N (min / max / trung binh tren moi incident)
SELECT 'canh_bao_tai_san: so tai san / canh bao' AS chi_so, MIN(n) AS min_n, MAX(n) AS max_n, ROUND(AVG(n), 2) AS avg_n FROM (SELECT MaCanhBao, COUNT(*) AS n FROM canh_bao_tai_san GROUP BY MaCanhBao) a UNION ALL
SELECT 'tai_san_incident: so tai san / incident', MIN(n), MAX(n), ROUND(AVG(n), 2) FROM (SELECT MaIncident, COUNT(*) AS n FROM tai_san_incident GROUP BY MaIncident) a UNION ALL
SELECT 'tai_san_incident: so incident / tai san', MIN(n), MAX(n), ROUND(AVG(n), 2) FROM (SELECT MaTS, COUNT(*) AS n FROM tai_san_incident GROUP BY MaTS) a UNION ALL
SELECT 'incident_ioc: so IOC / incident (co IOC)', MIN(n), MAX(n), ROUND(AVG(n), 2) FROM (SELECT MaIncident, COUNT(*) AS n FROM incident_ioc GROUP BY MaIncident) a UNION ALL
SELECT 'incident_ioc: so incident / IOC', MIN(n), MAX(n), ROUND(AVG(n), 2) FROM (SELECT GiaTriIOC, COUNT(*) AS n FROM incident_ioc GROUP BY GiaTriIOC) a UNION ALL
SELECT 'mitre: so ky thuat / incident', MIN(n), MAX(n), ROUND(AVG(n), 2) FROM (SELECT MaIncident, COUNT(*) AS n FROM su_co_ky_thuat_mitre GROUP BY MaIncident) a UNION ALL
SELECT 'mitre: so incident / ky thuat', MIN(n), MAX(n), ROUND(AVG(n), 2) FROM (SELECT MaKyThuat, COUNT(*) AS n FROM su_co_ky_thuat_mitre GROUP BY MaKyThuat) a UNION ALL
SELECT 'phan cong: so nhan vien / incident (co nguoi)', MIN(n), MAX(n), ROUND(AVG(n), 2) FROM (SELECT MaIncident, COUNT(*) AS n FROM su_co_nhan_vien_soc GROUP BY MaIncident) a UNION ALL
SELECT 'phan cong: so incident / nhan vien', MIN(n), MAX(n), ROUND(AVG(n), 2) FROM (SELECT MaNV, COUNT(*) AS n FROM su_co_nhan_vien_soc GROUP BY MaNV) a UNION ALL
SELECT 'hanh dong: so hanh dong / incident (co hanh dong)', MIN(n), MAX(n), ROUND(AVG(n), 2) FROM (SELECT MaIncident, COUNT(*) AS n FROM hanh_dong_xu_ly GROUP BY MaIncident) a;
