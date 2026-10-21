from datetime import datetime, timezone
from typing import Any
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import select, insert, update, delete, func, and_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from .config import settings
from .db import engine, TABLES, get_table, db_health
from .security import authenticate, create_token, current_user

app = FastAPI(title=settings.app_name, version="1.0.0", description="SOC employee and incident operations API")
origins = [x.strip() for x in settings.cors_origins.split(",") if x.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
prefix = settings.api_prefix

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
    return {"access_token": create_token(body.username), "token_type": "bearer", "user": {"username": body.username, "role": "SOC_MANAGER"}}

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
        try:
            table = get_table(name)
            result.append({"name": name, "columns": [
                {"name": c.name, "type": str(c.type), "nullable": c.nullable,
                 "primary_key": c.primary_key, "autoincrement": bool(c.autoincrement)}
                for c in table.columns
            ], "primary_key": [c.name for c in table.primary_key.columns]})
        except Exception:
            result.append({"name": name, "columns": [], "primary_key": [], "available": False})
    return result

@app.get(prefix + "/tables/{table_name}")
def list_rows(table_name: str, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
              search: str | None = None, user=Depends(current_user)):
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
    table = require_table(table_name)
    unknown = set(payload) - set(table.columns.keys())
    if unknown:
        raise HTTPException(status_code=422, detail={"unknown_fields": sorted(unknown)})
    try:
        with engine.begin() as conn:
            result = conn.execute(insert(table).values(**payload))
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
            result = conn.execute(update(table).where(pk == key).values(**payload))
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
    table = require_table(table_name)
    pks = list(table.primary_key.columns)
    if len(pks) != 1:
        raise HTTPException(status_code=400, detail="Deletion is disabled for tables with composite or missing primary keys.")
    try:
        with engine.begin() as conn:
            result = conn.execute(delete(table).where(pks[0] == key))
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
    with engine.connect() as conn:
        for name in ("su_co", "canh_bao", "nhan_vien_soc", "tai_san", "ioc", "to_chuc"):
            try:
                table = get_table(name)
                metrics[name] = conn.execute(select(func.count()).select_from(table)).scalar_one()
            except Exception:
                metrics[name] = None
        try:
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
    table = require_table("su_co")
    with engine.connect() as conn:
        rows = conn.execute(select(table).limit(500)).mappings().all()
    return {"items": [serialize_row(dict(r)) for r in rows], "note": "Summary based on existing incident records; no synthetic values added."}
