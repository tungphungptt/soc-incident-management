from datetime import datetime, timedelta, timezone
from functools import wraps
from .accounts import find_account, verify_password, public_account
from jose import jwt, JWTError
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .config import settings

bearer = HTTPBearer(auto_error=False)
ALGORITHM = "HS256"

def authenticate(username: str, password: str) -> bool:
    account = find_account(username)
    return bool(account and account['active'] and verify_password(password, account['password_hash']))

def create_token(username: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": username, "iat": now, "exp": now + timedelta(minutes=settings.jwt_expire_minutes)}
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)

def current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer)):
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise ValueError("Missing subject")
        account = find_account(username)
        if not account or not account['active']:
            raise ValueError('Account disabled')
        return public_account(account)
    except (JWTError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid or expired token")
