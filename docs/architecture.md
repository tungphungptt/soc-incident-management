# Architecture

## Runtime flow

React SPA → FastAPI `/api/v1` → SQLAlchemy Core reflection → existing MySQL 8 database.

The API reflects existing tables at runtime rather than declaring a second incompatible schema. This design is intentional because the supplied ZIP contains INSERT seed data and business queries, but no full CREATE TABLE dump.

## Table-to-module map

| Existing table | UI module / purpose |
|---|---|
| `to_chuc` | Organizations |
| `nhan_vien_soc` | SOC employees |
| `tai_san` | Assets |
| `su_co` | Incidents |
| `canh_bao` | Alerts |
| `ioc` | Indicators of compromise |
| `ky_thuat_mitre` | MITRE ATT&CK techniques |
| `canh_bao_tai_san` | Alert-asset relation |
| `tai_san_incident` | Incident-asset relation |
| `incident_ioc` | Incident-IOC relation |
| `su_co_ky_thuat_mitre` | Incident-technique relation |
| `su_co_nhan_vien_soc` | Incident assignments |
| `hanh_dong_xu_ly` | Response action history |
| `lich_su_trang_thai` | Status history |

## Safety model

- Table names are allowlisted in backend code.
- Column names are checked against reflected schema before writes.
- Values are sent through SQLAlchemy bound parameters.
- App startup does not seed, drop, or alter the database.
- Foreign key and unique constraints remain enforced by MySQL.
- Generic deletion may be rejected by the database if related records exist.

## Production gaps

Use persistent user/role tables, permission checks per resource/action, a transaction-safe incident lifecycle service, composite-key support, rate limiting, centralized audit logging, migrations, and integration tests before production use.
