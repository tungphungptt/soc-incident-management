-- MySQL 8.0.16+. Run after: python -m scripts.migrate_business_rules
-- Installer reads this file; mysql CLI also supports SOURCE sql/triggers.sql.
-- Actor variables are optional. Without an application actor, USER() is recorded.
DELIMITER $$
DROP PROCEDURE IF EXISTS soc_refresh_risk$$
CREATE PROCEDURE soc_refresh_risk()
BEGIN
  UPDATE to_chuc o SET DiemRuiRo=(
    SELECT COALESCE(SUM(CASE s.MucDoNghiemTrong
      WHEN 'CRITICAL' THEN 10 WHEN 'HIGH' THEN 5 WHEN 'MEDIUM' THEN 2 WHEN 'LOW' THEN 1 ELSE 0 END),0)
    FROM su_co s WHERE EXISTS (
      SELECT 1 FROM tai_san_incident x JOIN tai_san a ON a.MaTS=x.MaTS
      WHERE x.MaIncident=s.MaIncident AND a.MaTC=o.MaTC));
END$$

DROP TRIGGER IF EXISTS soc_incident_bi$$
CREATE TRIGGER soc_incident_bi BEFORE INSERT ON su_co FOR EACH ROW
BEGIN
  IF NEW.TrangThai <> 'NEW' THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='SOC_STATE: new incidents must start at NEW';
  END IF;
  IF NEW.MucDoNghiemTrong='CRITICAL' THEN
    IF NEW.MaChuyenGia IS NULL OR NEW.VaiTroChuyenGia IS NULL
       OR NEW.VaiTroChuyenGia NOT IN ('SOC_L2','SOC_L3')
       OR NOT EXISTS(SELECT 1 FROM nhan_vien_soc WHERE MaNV=NEW.MaChuyenGia) THEN
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='SOC_CRITICAL: supply an L2/L3 expert for atomic assignment';
    END IF;
  END IF;
END$$

DROP TRIGGER IF EXISTS soc_incident_ai$$
CREATE TRIGGER soc_incident_ai AFTER INSERT ON su_co FOR EACH ROW
BEGIN
  IF NEW.MucDoNghiemTrong='CRITICAL' THEN
    INSERT INTO su_co_nhan_vien_soc(MaIncident,MaNV,VaiTro,ViTri,ThoiDiemThamGia)
      VALUES(NEW.MaIncident,NEW.MaChuyenGia,NEW.VaiTroChuyenGia,'Critical expert',UTC_TIMESTAMP(6));
  END IF;
  CALL soc_refresh_risk();
END$$

DROP TRIGGER IF EXISTS soc_incident_bu$$
CREATE TRIGGER soc_incident_bu BEFORE UPDATE ON su_co FOR EACH ROW
BEGIN
  DECLARE expert_id VARCHAR(20);
  DECLARE expert_role VARCHAR(50);
  DECLARE expert_count INTEGER;
  IF NEW.MucDoNghiemTrong='CRITICAL' THEN
    IF NEW.MaChuyenGia IS NULL THEN
      SELECT MaNV,VaiTro INTO expert_id,expert_role FROM su_co_nhan_vien_soc
        WHERE MaIncident=OLD.MaIncident AND VaiTro IN ('SOC_L2','SOC_L3') ORDER BY MaNV,VaiTro LIMIT 1 FOR UPDATE;
      SET NEW.MaChuyenGia=expert_id;
      SET NEW.VaiTroChuyenGia=expert_role;
    END IF;
    SELECT COUNT(*) INTO expert_count FROM su_co_nhan_vien_soc
      WHERE MaIncident=OLD.MaIncident AND MaNV=NEW.MaChuyenGia AND VaiTro=NEW.VaiTroChuyenGia
        AND VaiTro IN ('SOC_L2','SOC_L3') FOR UPDATE;
    IF expert_count=0 THEN
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='SOC_CRITICAL: an L2/L3 participant is required';
    END IF;
  ELSE
    SET NEW.MaChuyenGia=NULL;
    SET NEW.VaiTroChuyenGia=NULL;
  END IF;
  IF NOT (NEW.TrangThai <=> OLD.TrangThai) THEN
    IF OLD.TrangThai='CLOSED' THEN
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='SOC_CLOSED: closed incidents cannot be reopened';
    END IF;
    IF NOT ((OLD.TrangThai='NEW' AND NEW.TrangThai='INVESTIGATING')
      OR (OLD.TrangThai='INVESTIGATING' AND NEW.TrangThai='CONTAINED')
      OR (OLD.TrangThai='CONTAINED' AND NEW.TrangThai='REMEDIATING')
      OR (OLD.TrangThai='REMEDIATING' AND NEW.TrangThai='CLOSED')) THEN
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='SOC_STATE: invalid state transition';
    END IF;
    IF NEW.TrangThai='CLOSED' AND NOT EXISTS(
      SELECT 1 FROM hanh_dong_xu_ly h WHERE h.MaIncident=OLD.MaIncident) THEN
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='SOC_ACTION: an action is required before closing';
    END IF;
    IF NEW.TrangThai='INVESTIGATING' THEN
      SET NEW.ThoiGianXuLy=COALESCE(NEW.ThoiGianXuLy,UTC_TIMESTAMP(6));
    END IF;
    IF NEW.TrangThai='CLOSED' THEN
      SET NEW.ThoiGianDong=COALESCE(NEW.ThoiGianDong,UTC_TIMESTAMP(6));
    END IF;
  END IF;
END$$

DROP TRIGGER IF EXISTS soc_incident_au$$
CREATE TRIGGER soc_incident_au AFTER UPDATE ON su_co FOR EACH ROW
BEGIN
  DECLARE change_time DATETIME(6);
  DECLARE actor_id VARCHAR(20);
  IF NOT (NEW.TrangThai <=> OLD.TrangThai) THEN
    SET change_time=COALESCE(@soc_change_time,UTC_TIMESTAMP(6));
    SET actor_id=@soc_actor_employee;
    IF actor_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM nhan_vien_soc WHERE MaNV=actor_id) THEN
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='SOC_ACTOR: unknown employee';
    END IF;
    WHILE EXISTS(SELECT 1 FROM lich_su_trang_thai WHERE ThoiDiemThayDoi=change_time) DO
      SET change_time=TIMESTAMPADD(MICROSECOND,1,change_time);
    END WHILE;
    INSERT INTO lich_su_trang_thai(ThoiDiemThayDoi,TrangThaiCu,TrangThaiMoi,MaIncident,MaNV,NguoiThucHien)
      VALUES(change_time,OLD.TrangThai,NEW.TrangThai,NEW.MaIncident,actor_id,COALESCE(@soc_actor_username,USER()));
  END IF;
  CALL soc_refresh_risk();
END$$

DROP TRIGGER IF EXISTS soc_incident_ad$$
CREATE TRIGGER soc_incident_ad AFTER DELETE ON su_co FOR EACH ROW
BEGIN
  CALL soc_refresh_risk();
END$$

DROP TRIGGER IF EXISTS soc_assignment_bd$$
CREATE TRIGGER soc_assignment_bd BEFORE DELETE ON su_co_nhan_vien_soc FOR EACH ROW
BEGIN
  DECLARE severity VARCHAR(20);
  DECLARE expert_id VARCHAR(20);
  DECLARE expert_role VARCHAR(50);
  SELECT MucDoNghiemTrong,MaChuyenGia,VaiTroChuyenGia INTO severity,expert_id,expert_role
    FROM su_co WHERE MaIncident=OLD.MaIncident FOR UPDATE;
  IF severity='CRITICAL' AND OLD.MaNV=expert_id AND OLD.VaiTro=expert_role THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='SOC_CRITICAL: reassign the designated expert before removing this participant';
  END IF;
END$$

DROP TRIGGER IF EXISTS soc_assignment_bu$$
CREATE TRIGGER soc_assignment_bu BEFORE UPDATE ON su_co_nhan_vien_soc FOR EACH ROW
BEGIN
  DECLARE severity VARCHAR(20);
  DECLARE expert_id VARCHAR(20);
  DECLARE expert_role VARCHAR(50);
  SELECT MucDoNghiemTrong,MaChuyenGia,VaiTroChuyenGia INTO severity,expert_id,expert_role
    FROM su_co WHERE MaIncident=OLD.MaIncident FOR UPDATE;
  IF severity='CRITICAL' AND OLD.MaNV=expert_id AND OLD.VaiTro=expert_role
    AND NOT(NEW.MaIncident=OLD.MaIncident AND NEW.MaNV=OLD.MaNV AND NEW.VaiTro=OLD.VaiTro) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='SOC_CRITICAL: cannot replace the last expert with a non-expert';
  END IF;
END$$

-- Duplicate assignment is enforced by PRIMARY KEY (MaIncident,MaNV,VaiTro).
DROP TRIGGER IF EXISTS soc_employee_bd$$
CREATE TRIGGER soc_employee_bd BEFORE DELETE ON nhan_vien_soc FOR EACH ROW
BEGIN
  IF EXISTS(SELECT 1 FROM su_co_nhan_vien_soc WHERE MaNV=OLD.MaNV) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='SOC_EMPLOYEE: employee participates in an incident';
  END IF;
END$$

DROP TRIGGER IF EXISTS soc_action_bd$$
CREATE TRIGGER soc_action_bd BEFORE DELETE ON hanh_dong_xu_ly FOR EACH ROW
BEGIN
  DECLARE state VARCHAR(50);
  SELECT TrangThai INTO state FROM su_co WHERE MaIncident=OLD.MaIncident FOR UPDATE;
  IF state='CLOSED' AND NOT EXISTS(SELECT 1 FROM hanh_dong_xu_ly h
    WHERE h.MaIncident=OLD.MaIncident AND h.ThoiGianThucHien<>OLD.ThoiGianThucHien) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='SOC_ACTION: cannot delete the last action of a closed incident';
  END IF;
END$$

DROP TRIGGER IF EXISTS soc_action_bu$$
CREATE TRIGGER soc_action_bu BEFORE UPDATE ON hanh_dong_xu_ly FOR EACH ROW
BEGIN
  DECLARE state VARCHAR(50);
  SELECT TrangThai INTO state FROM su_co WHERE MaIncident=OLD.MaIncident FOR UPDATE;
  IF state='CLOSED' AND NEW.MaIncident<>OLD.MaIncident AND NOT EXISTS(SELECT 1 FROM hanh_dong_xu_ly h
    WHERE h.MaIncident=OLD.MaIncident AND h.ThoiGianThucHien<>OLD.ThoiGianThucHien) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='SOC_ACTION: cannot move the last action of a closed incident';
  END IF;
END$$

DROP TRIGGER IF EXISTS soc_asset_link_ai$$
CREATE TRIGGER soc_asset_link_ai AFTER INSERT ON tai_san_incident FOR EACH ROW
BEGIN
  CALL soc_refresh_risk();
END$$
DROP TRIGGER IF EXISTS soc_asset_link_au$$
CREATE TRIGGER soc_asset_link_au AFTER UPDATE ON tai_san_incident FOR EACH ROW
BEGIN
  CALL soc_refresh_risk();
END$$
DROP TRIGGER IF EXISTS soc_asset_link_ad$$
CREATE TRIGGER soc_asset_link_ad AFTER DELETE ON tai_san_incident FOR EACH ROW
BEGIN
  CALL soc_refresh_risk();
END$$
DROP TRIGGER IF EXISTS soc_asset_au$$
CREATE TRIGGER soc_asset_au AFTER UPDATE ON tai_san FOR EACH ROW
BEGIN
  CALL soc_refresh_risk();
END$$
DROP TRIGGER IF EXISTS soc_asset_ad$$
CREATE TRIGGER soc_asset_ad AFTER DELETE ON tai_san FOR EACH ROW
BEGIN
  CALL soc_refresh_risk();
END$$
DROP TRIGGER IF EXISTS soc_org_bi$$
CREATE TRIGGER soc_org_bi BEFORE INSERT ON to_chuc FOR EACH ROW
BEGIN
  SET NEW.DiemRuiRo=0;
END$$
DROP TRIGGER IF EXISTS soc_org_bu$$
CREATE TRIGGER soc_org_bu BEFORE UPDATE ON to_chuc FOR EACH ROW
BEGIN
  SET NEW.DiemRuiRo=(SELECT COALESCE(SUM(CASE s.MucDoNghiemTrong
    WHEN 'CRITICAL' THEN 10 WHEN 'HIGH' THEN 5 WHEN 'MEDIUM' THEN 2 WHEN 'LOW' THEN 1 ELSE 0 END),0)
    FROM su_co s WHERE EXISTS(SELECT 1 FROM tai_san_incident x JOIN tai_san a ON a.MaTS=x.MaTS
    WHERE x.MaIncident=s.MaIncident AND a.MaTC=NEW.MaTC));
END$$
DELIMITER ;

-- A live view handles the passage of time; a trigger/CHECK cannot fire merely
-- because one hour elapsed. No global event_scheduler setting is required.
CREATE OR REPLACE VIEW soc_critical_new_violations AS
SELECT MaIncident,ThoiGianPhatHien,
       TIMESTAMPADD(HOUR,1,ThoiGianPhatHien) AS Deadline,
       TIMESTAMPDIFF(SECOND,TIMESTAMPADD(HOUR,1,ThoiGianPhatHien),UTC_TIMESTAMP()) AS OverdueSeconds,
       1 AS ViPham
FROM su_co
WHERE MucDoNghiemTrong='CRITICAL' AND TrangThai='NEW'
  AND ThoiGianPhatHien<TIMESTAMPADD(HOUR,-1,UTC_TIMESTAMP());
