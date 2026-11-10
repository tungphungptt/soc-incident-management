# Ki?m ch?ng MySQL 8.0.46 tr?n soc_schema_test

Ng?y ki?m ch?ng: 10/11/2026 (Asia/Saigon). Kh?ng d?ng Docker; k?t n?i l?y t? backend/.env, kh?ng ghi m?t kh?u v?o b?o c?o.

## Ph?m vi v? th? t?
- ?? t?o m?i soc_schema_test v?i utf8mb4 / utf8mb4_unicode_ci. Kh?ng thao t?c database d? ?n.
- ?? ch?y 01_schema.sql: th?nh c?ng, ?? 18 b?ng InnoDB.
- ?? ch?y migrate_workspaces r?i migrate_business_rules: th?nh c?ng.
- ?? th? seed g?c sau migration, ti?p t?c c?c statement ?? ghi ?? l?i r?i rollback to?n b?.
- Seed g?c d?ng 19 d?ng USE soc_incident_management: ?? chuy?n ri?ng c?u l?nh trong b? ch?y th?nh USE soc_schema_test; file g?c kh?ng ??i.
- ?? ch?y Q01?Q18 sau rollback: 18 truy v?n th?nh c?ng, t?t c? r?ng.
- ?? ki?m ch?ng seed l?ch s? s?a: x?c nh?n c?c b?ng d? li?u th? c?n tr?ng, g? trigger ch? trong soc_schema_test, n?p 03_seed_proposed.sql r?i ch?y l?i hai migration. Kh?ng t?t FOREIGN_KEY_CHECKS.
- Cu?i c?ng database th? c? 18 b?ng v? 17 trigger. Kh?ng DROP DATABASE; kh?ng commit Git.

## Schema cu?i
PK su_co_nhan_vien_soc: (MaIncident, MaNV, VaiTro).

| B?ng | C?t ???c ki?m ch?ng |
|---|---|
| incident_ioc | LoaiIOC: VARCHAR(50) COLLATE utf8mb4_unicode_ci |
| hanh_dong_xu_ly | ThoiLuongPhut: INTEGER |
| lich_su_trang_thai | NguoiThucHien: VARCHAR(128) COLLATE utf8mb4_unicode_ci |
| su_co | DiemRuiRo: INTEGER; MaChuyenGia: VARCHAR(20) COLLATE utf8mb4_unicode_ci; VaiTroChuyenGia: VARCHAR(50) COLLATE utf8mb4_unicode_ci |
| to_chuc | DiemRuiRo: INTEGER |
| su_co_nhan_vien_soc | ThoiDiemThamGia: DATETIME |

T?t c? b?ng c? ENGINE=InnoDB, TABLE_COLLATION=utf8mb4_unicode_ci. C?c truy v?n th?c t? kh?ng g?p l?i c?t thi?u ho?c ki?u d? li?u.

## L?i seed g?c
C?c d?ng d??i ??y l? v? tr? b?t ??u/k?t th?c **c?u INSERT nhi?u d?ng** trong database-data/seed_soc_incident_management.sql. MySQL tr? l?i cho statement, kh?ng x?c ??nh ??y ?? t?ng tuple b? l?i; kh?ng n?n coi d?ng ??u statement l? d?ng tuple g?y l?i.

| D?ng ??u | D?ng cu?i | L?i MySQL |
|---|---|---|
| 336 | 436 | (1644, 'SOC_STATE: new incidents must start at NEW') |
| 438 | 488 | (1644, 'SOC_STATE: new incidents must start at NEW') |
| 491 | 591 | (1452, 'Cannot add or update a child row: a foreign key constraint fails (`soc_schema_test`.`canh_bao`, CONSTRAINT `fk_alert_incident` FOREIGN KEY (`MaIncident`) REFERENCES `su_co` (`MaIncident`) ON DELETE RESTRICT ON UPDATE CASCADE)') |
| 593 | 693 | (1452, 'Cannot add or update a child row: a foreign key constraint fails (`soc_schema_test`.`canh_bao`, CONSTRAINT `fk_alert_incident` FOREIGN KEY (`MaIncident`) REFERENCES `su_co` (`MaIncident`) ON DELETE RESTRICT ON UPDATE CASCADE)') |
| 695 | 795 | (1452, 'Cannot add or update a child row: a foreign key constraint fails (`soc_schema_test`.`canh_bao`, CONSTRAINT `fk_alert_incident` FOREIGN KEY (`MaIncident`) REFERENCES `su_co` (`MaIncident`) ON DELETE RESTRICT ON UPDATE CASCADE)') |
| 797 | 897 | (1452, 'Cannot add or update a child row: a foreign key constraint fails (`soc_schema_test`.`canh_bao`, CONSTRAINT `fk_alert_incident` FOREIGN KEY (`MaIncident`) REFERENCES `su_co` (`MaIncident`) ON DELETE RESTRICT ON UPDATE CASCADE)') |
| 899 | 949 | (1452, 'Cannot add or update a child row: a foreign key constraint fails (`soc_schema_test`.`canh_bao`, CONSTRAINT `fk_alert_incident` FOREIGN KEY (`MaIncident`) REFERENCES `su_co` (`MaIncident`) ON DELETE RESTRICT ON UPDATE CASCADE)') |
| 952 | 1052 | (1452, 'Cannot add or update a child row: a foreign key constraint fails (`soc_schema_test`.`canh_bao_tai_san`, CONSTRAINT `fk_alert_asset_alert` FOREIGN KEY (`MaCanhBao`) REFERENCES `canh_bao` (`MaCanhBao`) ON DELETE RESTRICT ON UPDATE CASCADE)') |
| 1054 | 1154 | (1452, 'Cannot add or update a child row: a foreign key constraint fails (`soc_schema_test`.`canh_bao_tai_san`, CONSTRAINT `fk_alert_asset_alert` FOREIGN KEY (`MaCanhBao`) REFERENCES `canh_bao` (`MaCanhBao`) ON DELETE RESTRICT ON UPDATE CASCADE)') |
| 1156 | 1256 | (1452, 'Cannot add or update a child row: a foreign key constraint fails (`soc_schema_test`.`canh_bao_tai_san`, CONSTRAINT `fk_alert_asset_alert` FOREIGN KEY (`MaCanhBao`) REFERENCES `canh_bao` (`MaCanhBao`) ON DELETE RESTRICT ON UPDATE CASCADE)') |
| 1258 | 1358 | (1452, 'Cannot add or update a child row: a foreign key constraint fails (`soc_schema_test`.`canh_bao_tai_san`, CONSTRAINT `fk_alert_asset_alert` FOREIGN KEY (`MaCanhBao`) REFERENCES `canh_bao` (`MaCanhBao`) ON DELETE RESTRICT ON UPDATE CASCADE)') |
| 1360 | 1460 | (1452, 'Cannot add or update a child row: a foreign key constraint fails (`soc_schema_test`.`canh_bao_tai_san`, CONSTRAINT `fk_alert_asset_alert` FOREIGN KEY (`MaCanhBao`) REFERENCES `canh_bao` (`MaCanhBao`) ON DELETE RESTRICT ON UPDATE CASCADE)') |
| 1463 | 1563 | (1452, 'Cannot add or update a child row: a foreign key constraint fails (`soc_schema_test`.`tai_san_incident`, CONSTRAINT `fk_asset_incident_incident` FOREIGN KEY (`MaIncident`) REFERENCES `su_co` (`MaIncident`) ON DELETE RESTRICT ON UPDATE CASCADE)') |
| 1565 | 1665 | (1452, 'Cannot add or update a child row: a foreign key constraint fails (`soc_schema_test`.`tai_san_incident`, CONSTRAINT `fk_asset_incident_incident` FOREIGN KEY (`MaIncident`) REFERENCES `su_co` (`MaIncident`) ON DELETE RESTRICT ON UPDATE CASCADE)') |
| 1667 | 1717 | (1452, 'Cannot add or update a child row: a foreign key constraint fails (`soc_schema_test`.`tai_san_incident`, CONSTRAINT `fk_asset_incident_incident` FOREIGN KEY (`MaIncident`) REFERENCES `su_co` (`MaIncident`) ON DELETE RESTRICT ON UPDATE CASCADE)') |
| 1720 | 1820 | (1364, "Field 'LoaiIOC' doesn't have a default value") |
| 1822 | 1922 | (1364, "Field 'LoaiIOC' doesn't have a default value") |
| 1924 | 2024 | (1364, "Field 'LoaiIOC' doesn't have a default value") |
| 2026 | 2031 | (1364, "Field 'LoaiIOC' doesn't have a default value") |
| 2034 | 2134 | (1452, 'Cannot add or update a child row: a foreign key constraint fails (`soc_schema_test`.`su_co_ky_thuat_mitre`, CONSTRAINT `fk_incident_tech_incident` FOREIGN KEY (`MaIncident`) REFERENCES `su_co` (`MaIncident`) ON DELETE RESTRICT ON UPDATE CASCADE)') |
| 2136 | 2236 | (1452, 'Cannot add or update a child row: a foreign key constraint fails (`soc_schema_test`.`su_co_ky_thuat_mitre`, CONSTRAINT `fk_incident_tech_incident` FOREIGN KEY (`MaIncident`) REFERENCES `su_co` (`MaIncident`) ON DELETE RESTRICT ON UPDATE CASCADE)') |
| 2238 | 2288 | (1452, 'Cannot add or update a child row: a foreign key constraint fails (`soc_schema_test`.`su_co_ky_thuat_mitre`, CONSTRAINT `fk_incident_tech_incident` FOREIGN KEY (`MaIncident`) REFERENCES `su_co` (`MaIncident`) ON DELETE RESTRICT ON UPDATE CASCADE)') |
| 2291 | 2391 | (1452, 'Cannot add or update a child row: a foreign key constraint fails (`soc_schema_test`.`su_co_nhan_vien_soc`, CONSTRAINT `fk_assignment_incident` FOREIGN KEY (`MaIncident`) REFERENCES `su_co` (`MaIncident`) ON DELETE RESTRICT ON UPDATE CASCADE)') |
| 2393 | 2493 | (1452, 'Cannot add or update a child row: a foreign key constraint fails (`soc_schema_test`.`su_co_nhan_vien_soc`, CONSTRAINT `fk_assignment_incident` FOREIGN KEY (`MaIncident`) REFERENCES `su_co` (`MaIncident`) ON DELETE RESTRICT ON UPDATE CASCADE)') |
| 2495 | 2595 | (1452, 'Cannot add or update a child row: a foreign key constraint fails (`soc_schema_test`.`su_co_nhan_vien_soc`, CONSTRAINT `fk_assignment_incident` FOREIGN KEY (`MaIncident`) REFERENCES `su_co` (`MaIncident`) ON DELETE RESTRICT ON UPDATE CASCADE)') |
| 2597 | 2660 | (1452, 'Cannot add or update a child row: a foreign key constraint fails (`soc_schema_test`.`su_co_nhan_vien_soc`, CONSTRAINT `fk_assignment_incident` FOREIGN KEY (`MaIncident`) REFERENCES `su_co` (`MaIncident`) ON DELETE RESTRICT ON UPDATE CASCADE)') |
| 2663 | 2763 | (1452, 'Cannot add or update a child row: a foreign key constraint fails (`soc_schema_test`.`hanh_dong_xu_ly`, CONSTRAINT `fk_action_incident` FOREIGN KEY (`MaIncident`) REFERENCES `su_co` (`MaIncident`) ON DELETE RESTRICT ON UPDATE CASCADE)') |
| 2765 | 2865 | (1452, 'Cannot add or update a child row: a foreign key constraint fails (`soc_schema_test`.`hanh_dong_xu_ly`, CONSTRAINT `fk_action_incident` FOREIGN KEY (`MaIncident`) REFERENCES `su_co` (`MaIncident`) ON DELETE RESTRICT ON UPDATE CASCADE)') |
| 2867 | 2967 | (1452, 'Cannot add or update a child row: a foreign key constraint fails (`soc_schema_test`.`hanh_dong_xu_ly`, CONSTRAINT `fk_action_incident` FOREIGN KEY (`MaIncident`) REFERENCES `su_co` (`MaIncident`) ON DELETE RESTRICT ON UPDATE CASCADE)') |
| 2969 | 3033 | (1452, 'Cannot add or update a child row: a foreign key constraint fails (`soc_schema_test`.`hanh_dong_xu_ly`, CONSTRAINT `fk_action_incident` FOREIGN KEY (`MaIncident`) REFERENCES `su_co` (`MaIncident`) ON DELETE RESTRICT ON UPDATE CASCADE)') |
| 3036 | 3136 | (1452, 'Cannot add or update a child row: a foreign key constraint fails (`soc_schema_test`.`lich_su_trang_thai`, CONSTRAINT `fk_history_incident` FOREIGN KEY (`MaIncident`) REFERENCES `su_co` (`MaIncident`) ON DELETE RESTRICT ON UPDATE CASCADE)') |
| 3138 | 3238 | (1452, 'Cannot add or update a child row: a foreign key constraint fails (`soc_schema_test`.`lich_su_trang_thai`, CONSTRAINT `fk_history_incident` FOREIGN KEY (`MaIncident`) REFERENCES `su_co` (`MaIncident`) ON DELETE RESTRICT ON UPDATE CASCADE)') |
| 3240 | 3340 | (1452, 'Cannot add or update a child row: a foreign key constraint fails (`soc_schema_test`.`lich_su_trang_thai`, CONSTRAINT `fk_history_incident` FOREIGN KEY (`MaIncident`) REFERENCES `su_co` (`MaIncident`) ON DELETE RESTRICT ON UPDATE CASCADE)') |
| 3342 | 3442 | (1452, 'Cannot add or update a child row: a foreign key constraint fails (`soc_schema_test`.`lich_su_trang_thai`, CONSTRAINT `fk_history_incident` FOREIGN KEY (`MaIncident`) REFERENCES `su_co` (`MaIncident`) ON DELETE RESTRICT ON UPDATE CASCADE)') |
| 3444 | 3458 | (1452, 'Cannot add or update a child row: a foreign key constraint fails (`soc_schema_test`.`lich_su_trang_thai`, CONSTRAINT `fk_history_incident` FOREIGN KEY (`MaIncident`) REFERENCES `su_co` (`MaIncident`) ON DELETE RESTRICT ON UPDATE CASCADE)') |

T?ng c?ng 35 statement l?i. M? 1644: trigger t? ch?i INSERT s? c? kh?ng ? NEW; m? 1364: thi?u LoaiIOC kh?ng c? DEFAULT; m? 1452: FK ??n d? li?u cha kh?ng import ???c. ?? rollback to?n b?, kh?ng gi? d? li?u n?a ch?ng.

## K?t qu? Q01?Q18 sau seed s?a
Tham s? m?c ??nh: th?ng 11/2026, incident DMINC004, th?i ?i?m UTC th?c t? m?y ch?. Tham s? theo seed: th?ng 10/2026, incident INC004, now_ref 2026-10-21 12:00:00.

| Query | S? d?ng m?c ??nh | S? d?ng theo seed |
|---|---:|---:|
| Q01 | 0 | 40 |
| Q02 | 0 | 10 |
| Q03 | 1 | 1 |
| Q04 | 46 | 40 |
| Q05 | 148 | 148 |
| Q06 | 184 | 184 |
| Q07 | 10 | 10 |
| Q08 | 10 | 10 |
| Q09 | 1017 | 1017 |
| Q10 | 6 | 6 |
| Q11 | 20 | 20 |
| Q12 | 10 | 10 |
| Q13 | 0 | 9 |
| Q14 | 0 | 3 |
| Q15 | 228 | 228 |
| Q16 | 30 | 30 |
| Q17 | 8 | 8 |
| Q18 | 9 | 9 |

C? 18 truy v?n kh?ng l?i. Q01/Q02 m?c ??nh r?ng do kho?ng ng?y kh?ng c? d? li?u; Q13/Q14 do m? DMINC004 kh?ng thu?c seed g?c. Q11 kh?p risk_score_luu ? c? hai l??t.
Q16 c? 30 nh?n vi?n nh?ng l??ng ch?a c?u h?nh l? NULL; kh?ng suy di?n th?nh c? d? li?u l??ng. Profile v? account SQLite kh?ng ???c seed trong l?n th? n?y.

## File ?? xu?t v? gi?i h?n
- 02_schema_proposed.sql: gi? nguy?n c?u tr?c ?? ch?y ???c c?a 01_schema.sql, th?m USE soc_schema_test v? b? DROP TABLE ?? tr?nh x?a d? li?u khi ch?y nh?m l?n hai. File d?nh cho database th? m?i/tr?ng; kh?ng th?c thi l?i tr?n database ?ang c? b?ng. B?n n?y ch?a ???c import ??c l?p, c?u tr?c t??ng ???ng 01 ?? ki?m ch?ng.
- 03_seed_proposed.sql: chuy?n USE v? database th?, suy ra LoaiIOC b?ng JOIN v?i ioc, chu?n h?a s?u t?n vai tr? ph?n c?ng theo m? backend. ?? import v? ki?m ch?ng th?nh c?ng.
- Th? t? ?? xu?t cho bootstrap m?i: schema -> seed l?ch s? -> migrate_workspaces -> migrate_business_rules. Seed l?ch s? kh?ng ???c import sau khi c?i trigger workflow.
- B? ch?y x?c nh?n m?i GiaTriIOC trong seed ch? c? m?t lo?i v? ?? 305 li?n k?t sau import; kh?ng ?p c?ch suy lo?i n?y cho t?p d? li?u c? gi? tr? IOC tr?ng gi?a nhi?u lo?i.
- C?n x?c nh?n v?i DDL ngu?n: ?? d?i chu?i/nullability/UNIQUE/ch?nh s?ch FK v? l?a ch?n PK ID thay cho th?i gian. Ki?m ch?ng tr?n schema t?i d?ng kh?ng ch?ng minh schema database d? ?n c? c?ng c?u tr?c.
- C?c c?t ThoiLuongPhut, NguoiThucHien, ThoiDiemThamGia ch?a c? d? li?u seed t??ng ?ng n?n gi? NULL; kh?ng b?a d? li?u.
- Migration t? t?o snapshot m?i trong backend/migration_backups; ch? ch?a schema/d? li?u soc_schema_test.
- run_schema_test.py, prepare_schema_fixes.py, verify_schema_fixes.py l? script m?i ph?c v? t?i l?p; l?n ch?y ch?n ?o?n ban ??u c? l?i escape % c?a PyMySQL trong ch?nh b? ch?y, ?? s?a d?ng sqlalchemy.text v? ch?y l?i Q01?Q18 th?nh c?ng. ??y kh?ng ph?i l?i SQL c?a repo.

## S? d?ng d? li?u cu?i

| B?ng | S? d?ng |
|---|---:|
| canh_bao | 450 |
| canh_bao_tai_san | 500 |
| hanh_dong_xu_ly | 364 |
| incident_ioc | 305 |
| ioc | 100 |
| ky_thuat_mitre | 25 |
| lich_su_trang_thai | 414 |
| nhan_vien_soc | 30 |
| soc_account_profiles | 0 |
| soc_activity_log | 0 |
| soc_bonus_policy | 4 |
| soc_monthly_salary | 0 |
| su_co | 150 |
| su_co_ky_thuat_mitre | 250 |
| su_co_nhan_vien_soc | 363 |
| tai_san | 120 |
| tai_san_incident | 250 |
| to_chuc | 20 |

S? s? c? Critical thi?u chuy?n gia sau migration: 0.

K?t qu? m?y ??c ???c: schema_test_results.json. Database soc_schema_test ???c gi? l?i ch? quy?t ??nh c?a ng??i d?ng.
