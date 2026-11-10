-- Schema tái dựng từ code/seed trong repo; MySQL 8.0.16+.
-- Chọn database đích trước khi chạy. File này KHÔNG được tự động thực thi.
-- CẢNH BÁO: DROP bên dưới xóa dữ liệu 18 bảng MySQL nếu thực thi file.
-- 14 bảng nghiệp vụ + 4 bảng workspace; accounts/account_events vẫn ở SQLite.
-- Nguồn: backend/app/db.py, workspace_schema.py, scripts/migrate_*.py,
-- scripts/seed_demo_data.py, database-data/seed_soc_incident_management.sql,
-- sql/queries.sql, sql/triggers.sql. Không phải bản dump schema thực tế.
-- TODO: xác nhận độ dài VARCHAR, nullability, UNIQUE và chính sách FK của
-- các bảng nghiệp vụ với schema_soc_fixed.sql (file nguồn không có trong repo).
-- VARCHAR(20) cho mã NV và VARCHAR(50) cho loại IOC/vai trò có bằng chứng
-- trong migrate_business_rules.py; nhiều độ dài khác là lựa chọn dự kiến.
-- TODO: xác nhận PK hành động/lịch sử: seed dùng ID tự tăng, test dùng thời gian.
-- Chọn ID tự tăng theo seed; thời gian chỉ có INDEX, không ép UNIQUE vì
-- dữ liệu seed có thể ghi nhiều sự kiện cùng thời điểm.
-- TODO: seed SQL cũ thiếu incident_ioc.LoaiIOC; phải bổ sung/backfill loại
-- trước khi import vào schema này. Không đặt DEFAULT loại IOC giả.
-- Seed cũ cũng không có MaChuyenGia/VaiTroChuyenGia: cần backfill chuyên gia
-- trước khi cài triggers. Không import seed cũ sau khi cài triggers workflow.
-- CHECK chỉ kiểm tra miền đã có trong migration; workflow liên bảng nằm ở
-- sql/triggers.sql, chưa được cài bởi file này. Không tự thêm CHECK vai trò
-- phân công vì seed cũ có tên vai trò nghiệp vụ khác mã tài khoản hiện tại.
-- Không tạo FK username sang accounts: accounts nằm ở SQLite riêng.

SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;

DROP TABLE IF EXISTS soc_activity_log;
DROP TABLE IF EXISTS soc_bonus_policy;
DROP TABLE IF EXISTS soc_monthly_salary;
DROP TABLE IF EXISTS soc_account_profiles;
DROP TABLE IF EXISTS lich_su_trang_thai;
DROP TABLE IF EXISTS hanh_dong_xu_ly;
DROP TABLE IF EXISTS su_co_nhan_vien_soc;
DROP TABLE IF EXISTS su_co_ky_thuat_mitre;
DROP TABLE IF EXISTS incident_ioc;
DROP TABLE IF EXISTS tai_san_incident;
DROP TABLE IF EXISTS canh_bao_tai_san;
DROP TABLE IF EXISTS canh_bao;
DROP TABLE IF EXISTS su_co;
DROP TABLE IF EXISTS ioc;
DROP TABLE IF EXISTS ky_thuat_mitre;
DROP TABLE IF EXISTS tai_san;
DROP TABLE IF EXISTS nhan_vien_soc;
DROP TABLE IF EXISTS to_chuc;

-- Tổ chức sở hữu tài sản; điểm rủi ro được migration/trigger bổ sung.
CREATE TABLE to_chuc (
  MaTC VARCHAR(20) NOT NULL PRIMARY KEY,
  TenTC VARCHAR(255) NOT NULL,
  DiaChi VARCHAR(255) NULL,
  LinhVucHoatDong VARCHAR(255) NULL,
  SoLuongNhanVien INT NULL,
  MucDoQuanTrong VARCHAR(20) NOT NULL,
  DiemRuiRo INT NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Nhân viên SOC; vai trò đăng nhập không lưu trong bảng này.
CREATE TABLE nhan_vien_soc (
  MaNV VARCHAR(20) NOT NULL PRIMARY KEY,
  CMT VARCHAR(50) NOT NULL,
  HoTen VARCHAR(255) NOT NULL,
  NgaySinh DATE NULL,
  SoDienThoai VARCHAR(50) NULL,
  Email VARCHAR(255) NULL,
  SoNamKinhNghiem INT NULL
  -- TODO: xác nhận UNIQUE CMT/Email; chưa có DDL gốc để áp đặt.
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tài sản thuộc một tổ chức.
CREATE TABLE tai_san (
  MaTS VARCHAR(20) NOT NULL PRIMARY KEY,
  Ten VARCHAR(255) NOT NULL,
  LoaiTaiSan VARCHAR(100) NOT NULL,
  DiaChiIP VARCHAR(45) NULL,
  HeDieuHanh VARCHAR(100) NULL,
  ViTri VARCHAR(255) NULL,
  MucDoQuanTrong VARCHAR(20) NOT NULL,
  MaTC VARCHAR(20) NOT NULL,
  CONSTRAINT fk_asset_org FOREIGN KEY (MaTC) REFERENCES to_chuc(MaTC)
    ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Danh mục kỹ thuật MITRE ATT&CK.
CREATE TABLE ky_thuat_mitre (
  MaKyThuat VARCHAR(20) NOT NULL PRIMARY KEY,
  TenKyThuat VARCHAR(255) NOT NULL,
  ChienThuat VARCHAR(255) NOT NULL,
  MoTa TEXT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Chỉ dấu tấn công, định danh bằng cặp loại và giá trị sau migration.
CREATE TABLE ioc (
  LoaiIOC VARCHAR(50) NOT NULL,
  GiaTriIOC VARCHAR(100) NOT NULL,
  Nguon VARCHAR(100) NOT NULL,
  ThoiGianPhatHien DATETIME(6) NOT NULL,
  MucDoTinCay VARCHAR(20) NOT NULL,
  PRIMARY KEY (LoaiIOC, GiaTriIOC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Sự cố và các mốc xử lý; sự cố mới chưa có thời gian xử lý/đóng.
CREATE TABLE su_co (
  MaIncident VARCHAR(20) NOT NULL PRIMARY KEY,
  ThoiGianBatDau DATETIME(6) NOT NULL,
  ThoiGianPhatHien DATETIME(6) NOT NULL,
  ThoiGianXuLy DATETIME(6) NULL,
  ThoiGianDong DATETIME(6) NULL,
  MucDoNghiemTrong VARCHAR(20) NOT NULL,
  TrangThai VARCHAR(50) NOT NULL,
  MoTa TEXT NULL,
  DiemRuiRo INT NULL,
  MaChuyenGia VARCHAR(20) NULL,
  VaiTroChuyenGia VARCHAR(50) NULL,
  CONSTRAINT soc_critical_expert_employee FOREIGN KEY (MaChuyenGia)
    REFERENCES nhan_vien_soc(MaNV) ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT chk_incident_severity CHECK (MucDoNghiemTrong IN ('CRITICAL','HIGH','MEDIUM','LOW')),
  CONSTRAINT chk_incident_state CHECK (TrangThai IN ('NEW','INVESTIGATING','CONTAINED','REMEDIATING','CLOSED')),
  INDEX ix_incident_detected (ThoiGianPhatHien),
  INDEX ix_incident_closed (TrangThai, ThoiGianDong)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Cảnh báo thuộc một sự cố theo seed gốc.
CREATE TABLE canh_bao (
  MaCanhBao VARCHAR(20) NOT NULL PRIMARY KEY,
  LoaiCanhBao VARCHAR(100) NOT NULL,
  IPNguon VARCHAR(45) NULL,
  IPDich VARCHAR(45) NULL,
  ThoiGianPhatHien DATETIME(6) NOT NULL,
  NguonPhatHien VARCHAR(255) NOT NULL,
  MucDoNghiemTrong VARCHAR(20) NOT NULL,
  NoiDung TEXT NULL,
  MaIncident VARCHAR(20) NOT NULL,
  CONSTRAINT fk_alert_incident FOREIGN KEY (MaIncident) REFERENCES su_co(MaIncident)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  INDEX ix_alert_detected (ThoiGianPhatHien)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Liên kết cảnh báo và tài sản bị ảnh hưởng.
CREATE TABLE canh_bao_tai_san (
  MaCanhBao VARCHAR(20) NOT NULL,
  MaTS VARCHAR(20) NOT NULL,
  PRIMARY KEY (MaCanhBao, MaTS),
  CONSTRAINT fk_alert_asset_alert FOREIGN KEY (MaCanhBao) REFERENCES canh_bao(MaCanhBao)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_alert_asset_asset FOREIGN KEY (MaTS) REFERENCES tai_san(MaTS)
    ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Liên kết tài sản và sự cố.
CREATE TABLE tai_san_incident (
  MaTS VARCHAR(20) NOT NULL,
  MaIncident VARCHAR(20) NOT NULL,
  PRIMARY KEY (MaTS, MaIncident),
  CONSTRAINT fk_asset_incident_asset FOREIGN KEY (MaTS) REFERENCES tai_san(MaTS)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_asset_incident_incident FOREIGN KEY (MaIncident) REFERENCES su_co(MaIncident)
    ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Liên kết sự cố với đúng cặp loại và giá trị IOC.
CREATE TABLE incident_ioc (
  MaIncident VARCHAR(20) NOT NULL,
  LoaiIOC VARCHAR(50) NOT NULL,
  GiaTriIOC VARCHAR(100) NOT NULL,
  PRIMARY KEY (MaIncident, LoaiIOC, GiaTriIOC),
  CONSTRAINT fk_incident_ioc_incident FOREIGN KEY (MaIncident) REFERENCES su_co(MaIncident)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_incident_ioc_pair FOREIGN KEY (LoaiIOC, GiaTriIOC) REFERENCES ioc(LoaiIOC, GiaTriIOC)
    ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Kỹ thuật MITRE được quan sát trong sự cố.
CREATE TABLE su_co_ky_thuat_mitre (
  MaIncident VARCHAR(20) NOT NULL,
  MaKyThuat VARCHAR(20) NOT NULL,
  PRIMARY KEY (MaIncident, MaKyThuat),
  CONSTRAINT fk_incident_tech_incident FOREIGN KEY (MaIncident) REFERENCES su_co(MaIncident)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_incident_tech_tech FOREIGN KEY (MaKyThuat) REFERENCES ky_thuat_mitre(MaKyThuat)
    ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Phân công nhân viên; cho phép nhiều vai trò trên cùng sự cố sau migration.
CREATE TABLE su_co_nhan_vien_soc (
  MaIncident VARCHAR(20) NOT NULL,
  MaNV VARCHAR(20) NOT NULL,
  VaiTro VARCHAR(50) NOT NULL,
  ViTri VARCHAR(255) NULL,
  ThoiDiemThamGia DATETIME NULL,
  PRIMARY KEY (MaIncident, MaNV, VaiTro),
  CONSTRAINT fk_assignment_incident FOREIGN KEY (MaIncident) REFERENCES su_co(MaIncident)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT soc_su_co_nhan_vien_soc_employee_restrict FOREIGN KEY (MaNV) REFERENCES nhan_vien_soc(MaNV)
    ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Hành động xử lý; giữ cả hai cột thời gian mà backend và seed dùng.
CREATE TABLE hanh_dong_xu_ly (
  MaHanhDong INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  ThoiGianThucHien DATETIME(6) NOT NULL,
  ThoiGian DATETIME(6) NOT NULL,
  HanhDong VARCHAR(255) NOT NULL,
  KetQua TEXT NULL,
  MaIncident VARCHAR(20) NOT NULL,
  MaNV VARCHAR(20) NOT NULL,
  ThoiLuongPhut INT NULL,
  CONSTRAINT fk_action_incident FOREIGN KEY (MaIncident) REFERENCES su_co(MaIncident)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT soc_hanh_dong_xu_ly_employee_restrict FOREIGN KEY (MaNV) REFERENCES nhan_vien_soc(MaNV)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  INDEX ix_action_time (ThoiGianThucHien)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Lịch sử chuyển trạng thái, có thể do người dùng SQL không gắn nhân viên.
CREATE TABLE lich_su_trang_thai (
  MaLichSu INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  ThoiDiemThayDoi DATETIME(6) NOT NULL,
  TrangThaiCu VARCHAR(50) NOT NULL,
  TrangThaiMoi VARCHAR(50) NOT NULL,
  MaIncident VARCHAR(20) NOT NULL,
  MaNV VARCHAR(20) NULL,
  NguoiThucHien VARCHAR(128) NULL,
  CONSTRAINT fk_history_incident FOREIGN KEY (MaIncident) REFERENCES su_co(MaIncident)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT soc_lich_su_trang_thai_employee_restrict FOREIGN KEY (MaNV) REFERENCES nhan_vien_soc(MaNV)
    ON UPDATE CASCADE ON DELETE RESTRICT,
  INDEX ix_history_time (ThoiDiemThayDoi)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Liên kết tài khoản SQLite với nhân viên; phản ánh workspace_schema.py.
CREATE TABLE soc_account_profiles (
  username VARCHAR(100) NOT NULL PRIMARY KEY,
  employee_id VARCHAR(20) NOT NULL UNIQUE
  -- TODO: ORM chưa khai báo FK employee_id; xác nhận trước khi bổ sung.
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Lương cơ bản theo nhân viên và tháng.
CREATE TABLE soc_monthly_salary (
  employee_id VARCHAR(20) NOT NULL,
  month VARCHAR(7) NOT NULL,
  base_salary DECIMAL(15,2) NOT NULL,
  PRIMARY KEY (employee_id, month)
  -- TODO: ORM chưa khai báo FK hoặc CHECK lương/tháng; hiện API kiểm tra.
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Chính sách thưởng theo mức độ; dữ liệu chính sách do migration/seed nạp.
CREATE TABLE soc_bonus_policy (
  severity VARCHAR(20) NOT NULL PRIMARY KEY,
  amount DECIMAL(15,2) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Nhật ký thao tác nghiệp vụ, tách với account_events trong SQLite.
CREATE TABLE soc_activity_log (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(100) NOT NULL,
  action VARCHAR(100) NOT NULL,
  target VARCHAR(150) NOT NULL,
  detail TEXT NULL,
  created_at DATETIME NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
