from datetime import datetime, timezone
from typing import Any
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import select, insert, update, delete, func, and_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError, DBAPIError
from .config import settings
from .db import engine, TABLES, get_table, db_health
from .security import authenticate, create_token, current_user
from .accounts import initialize, connect, find_account, public_account, password_hash, permissions, ROLES, account_event
from .workspaces import router as workspace_router
from .workspace_schema import log
from fastapi.responses import JSONResponse
import sqlite3

app = FastAPI(title=settings.app_name, version="1.0.0", description="SOC employee and incident operations API")
app.include_router(workspace_router)

@app.exception_handler(IntegrityError)
async def constraint_error(request, exc):
    return JSONResponse(status_code=409, content={"detail": "Dữ liệu đã tồn tại hoặc vi phạm liên kết. Hãy tải lại và kiểm tra thông tin."})

@app.exception_handler(DBAPIError)
async def database_rule_error(request, exc):
    args=getattr(exc.orig,'args',())
    message=str(args[1]) if len(args)>1 else ''
    labels={
        'SOC_CRITICAL':'Sự cố Critical phải có ít nhất một nhân viên L2/L3 tham gia.',
        'SOC_ACTION':'Sự cố CLOSED phải có ít nhất một hành động xử lý.',
        'SOC_CLOSED':'Không thể mở lại sự cố đã CLOSED.',
        'SOC_STATE':'Chuyển trạng thái không hợp lệ.',
        'SOC_EMPLOYEE':'Không thể xóa nhân viên đang phụ trách Incident.',
        'SOC_ACTOR':'Người thực hiện chưa liên kết nhân viên hợp lệ.',
    }
    if args and args[0]==1644:
        detail=next((v for k,v in labels.items() if message.startswith(k)), 'Dữ liệu vi phạm ràng buộc nghiệp vụ MySQL.')
        return JSONResponse(status_code=409,content={'detail':detail})
    return JSONResponse(status_code=503,content={'detail':'Cơ sở dữ liệu tạm thời không sẵn sàng. Hãy tải lại và thử lại.'})
origins = [x.strip() for x in settings.cors_origins.split(",") if x.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
prefix = settings.api_prefix

@app.on_event("startup")
def initialize_accounts():
    initialize()

def require_permission(user, table, action):
    if action not in permissions(user['role'], table):
        raise HTTPException(status_code=403, detail="You do not have permission for this action")

def require_safe_crud(table):
    if table in {'su_co', 'su_co_nhan_vien_soc', 'hanh_dong_xu_ly', 'lich_su_trang_thai', 'ioc', 'incident_ioc', 'su_co_ky_thuat_mitre'}:
        raise HTTPException(409, 'Hãy dùng thao tác chuyên biệt trong khu vực làm việc để bảo toàn quy trình và lịch sử.')

def validate_directory(conn, table_name, payload):
    if table_name == 'tai_san' and 'MaTC' in payload:
        org = get_table('to_chuc')
        if not payload['MaTC'] or not conn.execute(select(org).where(org.c.MaTC == payload['MaTC'])).first():
            raise HTTPException(409, 'Mỗi tài sản phải thuộc một tổ chức có thật.')

def require_admin(user):
    if user['role'] != 'ADMIN':
        raise HTTPException(status_code=403, detail="Administrator permission required")

class AccountRequest(BaseModel):
    username: str
    password: str
    role: str

class AccountUpdate(BaseModel):
    role: str
    active: bool = True
    password: str | None = None

@app.get(prefix + '/roles')
def roles(user=Depends(current_user)):
    return [{'id': key, 'label': value[0], 'description': value[1]} for key, value in ROLES.items()]

@app.get(prefix + '/accounts')
def list_accounts(user=Depends(current_user)):
    require_admin(user)
    with connect() as conn:
        return [dict(row) for row in conn.execute('SELECT username, role, active FROM accounts ORDER BY username')]

@app.post(prefix + '/accounts', status_code=201)
def create_account(body: AccountRequest, user=Depends(current_user)):
    require_admin(user)
    if body.role not in ROLES or not body.username.strip() or len(body.password) < 10:
        raise HTTPException(422, 'Valid role, username and password of at least 10 characters required')
    try:
        with connect() as conn:
            conn.execute('INSERT INTO accounts VALUES (?, ?, ?, 1)', (body.username.strip(), password_hash(body.password), body.role))
            account_event(conn, user['username'], 'CREATE_ACCOUNT', body.username.strip(), body.role)
    except sqlite3.IntegrityError:
        raise HTTPException(409, 'Username already exists')
    return public_account(find_account(body.username.strip()))

@app.put(prefix + '/accounts/{username}')
def edit_account(username: str, body: AccountUpdate, user=Depends(current_user)):
    require_admin(user)
    if body.role not in ROLES or (body.password is not None and len(body.password) < 10):
        raise HTTPException(422, 'Invalid role or password must have at least 10 characters')
    if username == user['username'] and (body.role != 'ADMIN' or not body.active):
        raise HTTPException(409, 'Cannot remove your own administrator access')
    with connect() as conn:
        result = conn.execute('UPDATE accounts SET role=?, active=? WHERE username=?', (body.role, int(body.active), username))
        if result.rowcount == 0:
            raise HTTPException(404, 'Account not found')
        if body.password:
            conn.execute('UPDATE accounts SET password_hash=? WHERE username=?', (password_hash(body.password), username))
        account_event(conn, user['username'], 'UPDATE_ACCOUNT', username, f'role={body.role}; active={body.active}; password_changed={body.password is not None}')
    return public_account(find_account(username))


class LoginRequest(BaseModel):
    username: str
    password: str

@app.get("/health")
def health():
    try:
        db_health()
        return {"status": "ok", "database": "connected"}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database unavailable: {type(exc).__name__}")

@app.post(prefix + "/auth/login")
def login(body: LoginRequest):
    if not authenticate(body.username, body.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return {"access_token": create_token(body.username), "token_type": "bearer", "user": public_account(find_account(body.username))}

@app.get(prefix + "/auth/me")
def me(user=Depends(current_user)):
    return user

def serialize_row(row: dict[str, Any]):
    out = {}
    for key, value in row.items():
        if hasattr(value, "isoformat"):
            out[key] = value.isoformat()
        elif isinstance(value, bytes):
            out[key] = value.decode("utf-8", errors="replace")
        else:
            out[key] = value
    return out

def require_table(name: str):
    try:
        return get_table(name)
    except KeyError:
        raise HTTPException(status_code=404, detail="Unsupported table")
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Could not reflect table '{name}'. Check DB schema and connection.")

@app.get(prefix + "/meta/tables")
def table_metadata(user=Depends(current_user)):
    result = []
    for name in TABLES:
        if 'read' not in permissions(user['role'], name):
            continue
        try:
            table = get_table(name)
            result.append({"name": name, "permissions": permissions(user['role'], name), "columns": [
                {"name": c.name, "type": str(c.type), "nullable": c.nullable,
                 "primary_key": c.primary_key, "autoincrement": c is table.autoincrement_column,
                 "read_only": name == 'to_chuc' and c.name == 'DiemRuiRo'}
                for c in table.columns
            ], "primary_key": [c.name for c in table.primary_key.columns]})
        except Exception:
            result.append({"name": name, "permissions": permissions(user['role'], name), "columns": [], "primary_key": [], "available": False})
    return result

@app.get(prefix + "/tables/{table_name}")
def list_rows(table_name: str, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
              search: str | None = None, user=Depends(current_user)):
    require_permission(user, table_name, 'read')
    table = require_table(table_name)
    stmt = select(table)
    if search:
        text_cols = [c for c in table.columns if any(t in str(c.type).upper() for t in ("CHAR", "TEXT", "ENUM"))]
        if text_cols:
            stmt = stmt.where(and_(*[]) if False else __import__("sqlalchemy").or_(*[c.like(f"%{search}%") for c in text_cols]))
    with engine.connect() as conn:
        total_stmt = select(func.count()).select_from(stmt.subquery())
        total = conn.execute(total_stmt).scalar_one()
        rows = conn.execute(stmt.order_by(*(list(table.primary_key.columns) if len(table.primary_key.columns) else [])).limit(page_size).offset((page-1)*page_size)).mappings().all()
    return {"items": [serialize_row(dict(r)) for r in rows], "page": page, "page_size": page_size, "total": total}

@app.get(prefix + "/tables/{table_name}/{key}")
def get_row(table_name: str, key: str, user=Depends(current_user)):
    require_permission(user, table_name, 'read')
    table = require_table(table_name)
    pks = list(table.primary_key.columns)
    if len(pks) != 1:
        raise HTTPException(status_code=400, detail="This table has a composite or missing primary key; use the list view.")
    pk = pks[0]
    with engine.connect() as conn:
        row = conn.execute(select(table).where(pk == key)).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="Record not found")
    return serialize_row(dict(row))

@app.post(prefix + "/tables/{table_name}", status_code=201)
def create_row(table_name: str, payload: dict[str, Any], user=Depends(current_user)):
    require_permission(user, table_name, 'create')
    require_safe_crud(table_name)
    table = require_table(table_name)
    unknown = set(payload) - set(table.columns.keys())
    if unknown:
        raise HTTPException(status_code=422, detail={"unknown_fields": sorted(unknown)})
    try:
        with engine.begin() as conn:
            validate_directory(conn, table_name, payload)
            result = conn.execute(insert(table).values(**payload))
            log(conn, user, 'CREATE_DIRECTORY', table_name)
            pks = list(table.primary_key.columns)
            if len(pks) == 1 and result.inserted_primary_key and result.inserted_primary_key[0] is not None:
                row = conn.execute(select(table).where(pks[0] == result.inserted_primary_key[0])).mappings().first()
                if row:
                    return serialize_row(dict(row))
        return {"message": "Created", "primary_key": list(payload.get(c.name) for c in table.primary_key.columns)}
    except IntegrityError as exc:
        raise HTTPException(status_code=409, detail="Constraint violation: duplicate key or invalid relationship.")
    except SQLAlchemyError:
        raise HTTPException(status_code=400, detail="Could not create record. Check required fields and database constraints.")

@app.put(prefix + "/tables/{table_name}/{key}")
def update_row(table_name: str, key: str, payload: dict[str, Any], user=Depends(current_user)):
    require_permission(user, table_name, 'update')
    require_safe_crud(table_name)
    table = require_table(table_name)
    pks = list(table.primary_key.columns)
    if len(pks) != 1:
        raise HTTPException(status_code=400, detail="Editing is disabled for tables with composite or missing primary keys.")
    pk = pks[0]
    if pk.name in payload:
        raise HTTPException(status_code=422, detail="Primary key cannot be changed.")
    unknown = set(payload) - set(table.columns.keys())
    if unknown:
        raise HTTPException(status_code=422, detail={"unknown_fields": sorted(unknown)})
    try:
        with engine.begin() as conn:
            validate_directory(conn, table_name, payload)
            result = conn.execute(update(table).where(pk == key).values(**payload))
            log(conn, user, 'UPDATE_DIRECTORY', table_name, key)
            if result.rowcount == 0:
                exists = conn.execute(select(pk).where(pk == key)).first()
                if not exists:
                    raise HTTPException(status_code=404, detail="Record not found")
            row = conn.execute(select(table).where(pk == key)).mappings().first()
            return serialize_row(dict(row)) if row else {"message": "Updated"}
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Constraint violation: duplicate key or invalid relationship.")
    except SQLAlchemyError:
        raise HTTPException(status_code=400, detail="Could not update record.")

@app.delete(prefix + "/tables/{table_name}/{key}")
def delete_row(table_name: str, key: str, user=Depends(current_user)):
    require_permission(user, table_name, 'delete')
    require_safe_crud(table_name)
    table = require_table(table_name)
    pks = list(table.primary_key.columns)
    if len(pks) != 1:
        raise HTTPException(status_code=400, detail="Deletion is disabled for tables with composite or missing primary keys.")
    try:
        with engine.begin() as conn:
            if table_name == 'nhan_vien_soc':
                assignment = get_table('su_co_nhan_vien_soc')
                if conn.execute(select(assignment).where(assignment.c.MaNV == key)).first():
                    raise HTTPException(409, 'Không thể xóa nhân viên đang hoặc đã tham gia Incident. Hãy khóa tài khoản để giữ lịch sử.')
                from .workspace_schema import profiles
                if conn.execute(select(profiles).where(profiles.c.employee_id == key)).first():
                    raise HTTPException(409, 'Nhân viên đang liên kết tài khoản, không thể xóa hồ sơ.')
            result = conn.execute(delete(table).where(pks[0] == key))
            log(conn, user, 'DELETE_DIRECTORY', table_name, key)
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="Record not found")
        return {"message": "Deleted"}
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Cannot delete this record because related records exist.")
    except SQLAlchemyError:
        raise HTTPException(status_code=400, detail="Could not delete record.")

@app.get(prefix + "/dashboard")
def dashboard(user=Depends(current_user)):
    metrics = {}
    if user['role'] == 'ADMIN':
        return {"metrics": metrics, "generated_at": datetime.now(timezone.utc).isoformat()}
    with engine.connect() as conn:
        for name in ("su_co", "canh_bao", "nhan_vien_soc", "tai_san", "ioc", "to_chuc"):
            if 'read' not in permissions(user['role'], name):
                continue
            try:
                table = get_table(name)
                metrics[name] = conn.execute(select(func.count()).select_from(table)).scalar_one()
            except Exception:
                metrics[name] = None
        try:
            require_permission(user, 'su_co', 'read')
            incident = get_table("su_co")
            cols = {c.name.lower(): c.name for c in incident.columns}
            status_col = cols.get("trangthai") or cols.get("trang_thai") or cols.get("status")
            severity_col = cols.get("mucdo") or cols.get("muc_do") or cols.get("severity")
            if status_col:
                metrics["incidents_by_status"] = {str(r[0] or "UNKNOWN"): r[1] for r in conn.execute(select(incident.c[status_col], func.count()).group_by(incident.c[status_col]))}
            if severity_col:
                metrics["incidents_by_severity"] = {str(r[0] or "UNKNOWN"): r[1] for r in conn.execute(select(incident.c[severity_col], func.count()).group_by(incident.c[severity_col]))}
        except Exception:
            metrics["incidents_by_status"] = {}
            metrics["incidents_by_severity"] = {}
    return {"metrics": metrics, "generated_at": datetime.now(timezone.utc).isoformat()}

@app.get(prefix + "/reports/incident-summary")
def incident_summary(user=Depends(current_user)):
    require_permission(user, 'su_co', 'read')
    table = require_table("su_co")
    with engine.connect() as conn:
        rows = conn.execute(select(table).limit(500)).mappings().all()
    return {"items": [serialize_row(dict(r)) for r in rows], "note": "Summary based on existing incident records; no synthetic values added."}
