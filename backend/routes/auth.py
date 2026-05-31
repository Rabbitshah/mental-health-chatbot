from fastapi import APIRouter, HTTPException, Depends, Header, Response, Cookie, Request
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from pydantic import BaseModel, Field, field_validator
from dotenv import load_dotenv
import re
import json
import logging
import secrets

from redis_client import cache_get, cache_set, cache_delete, CacheKeys, CacheTTL

logger = logging.getLogger(__name__)

from database import (
    SessionLocal,
    engine,
    get_db,
    ensure_chat_session_status_columns,
    ensure_user_preference_columns,
    ensure_wellness_feature_tables,
    ensure_refresh_token_index,
)
from models import User
from database import Base
from jwt_handler import create_access_token, decode_token
from dependencies import get_current_user
from limiter import limiter

router = APIRouter()

# Ensure tables exist — skip ARRAY-typed tables when using SQLite (e.g. tests)
if engine.dialect.name == "sqlite":
    _SQLITE_COMPATIBLE_TABLES = [
        "users", "chat_sessions", "chat_messages",
        "mood_entries", "refresh_tokens", "notifications",
        "safety_plans", "journal_entries",
    ]
    for _tname in _SQLITE_COMPATIBLE_TABLES:
        Base.metadata.tables[_tname].create(bind=engine, checkfirst=True)
else:
    Base.metadata.create_all(bind=engine)
ensure_chat_session_status_columns()
ensure_user_preference_columns()
ensure_wellness_feature_tables()
ensure_refresh_token_index()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserCreate(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=8, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    username: str = Field(..., min_length=3, max_length=50)

    @field_validator('email')
    @classmethod
    def validate_email_format(cls, v):
        v = v.strip()
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, v):
            raise ValueError('Invalid email format')
        return v.lower()

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        v = v.strip()
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        return v

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v):
        checks = [
            len(v) >= 8,
            bool(re.search(r"[a-z]", v)),
            bool(re.search(r"[A-Z]", v)),
            bool(re.search(r"\d", v)),
            bool(re.search(r"[^A-Za-z0-9]", v)),
        ]
        if sum(checks) < 4:
            raise ValueError("Password must include upper/lowercase letters, a number, and a symbol")
        return v



class TokenRefresh(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str | None = None


class UserLogin(BaseModel):
    email: str
    password: str


VALID_NOTIFICATION_FREQUENCIES = {"daily", "weekly", "custom"}

class UserUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    password: str | None = None
    current_password: str | None = None
    dark_mode: bool | None = None
    email_notifications: bool | None = None
    push_notifications: bool | None = None
    notification_frequency: str | None = None
    language: str | None = None

    @field_validator("notification_frequency")
    @classmethod
    def validate_notification_frequency(cls, v):
        if v is not None and v not in VALID_NOTIFICATION_FREQUENCIES:
            raise ValueError(f"notification_frequency must be one of: {', '.join(sorted(VALID_NOTIFICATION_FREQUENCIES))}")
        return v

    @field_validator("email")
    @classmethod
    def validate_update_email(cls, v):
        if v is None:
            return v
        normalized = v.strip().lower()
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, normalized):
            raise ValueError("Invalid email format")
        return normalized

    @field_validator("password")
    @classmethod
    def validate_update_password(cls, v):
        if not v:
            return v
        return UserCreate.validate_password_strength(v)

class UserDelete(BaseModel):
    current_password: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str | None = None


def build_user_payload(user: User) -> dict:
    """Build a safe user payload dict (no password hash)."""
    return {
        "id": user.id,
        "name": user.name,
        "username": user.username,
        "email": user.email,
        "picture": user.picture,
        "has_password": bool(user.password),
        "auth_provider": "google" if getattr(user, "google_id", None) and not user.password else "local",
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "dark_mode": bool(user.dark_mode),
        "email_notifications": bool(user.email_notifications),
        "push_notifications": bool(user.push_notifications),
        "notification_frequency": user.notification_frequency or "daily",
        "language": user.language or "English",
    }

def _unique_username(db: Session, requested_username: str) -> str:
    candidate = requested_username
    if not db.query(User).filter(User.username == candidate).first():
        return candidate

    base = requested_username[:42].rstrip("_-") or "user"
    for _ in range(20):
        suffix = secrets.token_hex(3)
        candidate = f"{base}_{suffix}"
        if not db.query(User).filter(User.username == candidate).first():
            return candidate
    raise HTTPException(status_code=409, detail="Could not generate a unique username")

@router.post("/signup")
@limiter.limit("5/minute")
def signup(request: Request, user: UserCreate, response: Response, db: Session = Depends(get_db)):
    # Check email
    existing_email = db.query(User).filter(User.email == user.email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")

    username = _unique_username(db, user.username)

    # Hash password
    hashed_pw = pwd_context.hash(user.password)

    new_user = User(
        email=user.email,
        password=hashed_pw,
        name=user.name,
        username=username,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token(new_user.id)
    from jwt_handler import create_refresh_token
    refresh_token = create_refresh_token(new_user.id, db)

    # Set HttpOnly cookies — tokens are NOT returned in the response body
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=15 * 60
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=7 * 24 * 60 * 60
    )

    return {
        "msg": "Signup successful",
        "user": build_user_payload(new_user),
    }


@router.post("/login")
@limiter.limit("5/minute")
def login(request: Request, user: UserLogin, response: Response, db: Session = Depends(get_db)):
    email = user.email.strip().lower()
    existing = db.query(User).filter(User.email == email).first()
    if not existing or not existing.password or not pwd_context.verify(user.password, existing.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Create access token (15 minutes)
    access_token = create_access_token(existing.id)

    # Create refresh token (7 days) and store in database
    from jwt_handler import create_refresh_token
    refresh_token = create_refresh_token(existing.id, db)

    # Set HttpOnly cookies — tokens are NOT returned in the response body
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=15 * 60
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=7 * 24 * 60 * 60
    )

    return {
        "msg": "Login successful",
        "user": build_user_payload(existing),
    }


@router.post("/auth/refresh")
@limiter.limit("10/minute")
def refresh_token(
    request: Request,
    response: Response,
    body: TokenRefresh | None = None,
    refresh_token: str = Cookie(None),
    db: Session = Depends(get_db)
):
    """
    Exchange a valid refresh token from cookie or body for a new access token.
    """
    actual_token = refresh_token or (body.refresh_token if body else None)
    
    if not actual_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")

    from jwt_handler import validate_refresh_token, revoke_refresh_token, create_refresh_token
    
    try:
        # Validate the refresh token and get the user
        user = validate_refresh_token(actual_token, db)
        
        # ROTATION: Revoke the old token and issue a new one
        try:
            revoke_refresh_token(actual_token, db)
        except ValueError:
            pass # Already revoked or not found, but validate_refresh_token passed so it's fine
            
        new_refresh_token = create_refresh_token(user.id, db)

        # Issue a new access token
        new_access_token = create_access_token(user.id)

        # Set new cookies — tokens are NOT returned in the response body
        response.set_cookie(
            key="access_token",
            value=new_access_token,
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=15 * 60
        )
        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=7 * 24 * 60 * 60
        )

        return {"msg": "Token refreshed successfully"}
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))



@router.get("/profile")
def get_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user = current_user
    cache_key = CacheKeys.USER_PROFILE.format(user_id=user.id)
    try:
        cached = cache_get(cache_key)
        if cached:
            return json.loads(cached)
    except Exception as e:
        logger.warning(f"Cache GET failed for profile {user.id}: {e}")

    profile_data = build_user_payload(user)

    try:
        cache_set(cache_key, json.dumps(profile_data), CacheTTL.USER_PROFILE)
    except Exception as e:
        logger.warning(f"Cache SET failed for profile {user.id}: {e}")

    return profile_data


@router.put("/profile")
@limiter.limit("10/minute")
def update_profile(
    request: Request,
    update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user = db.merge(current_user)
    requires_password_verification = any([
        update.name is not None and update.name != user.name,
        update.email is not None and update.email != user.email,
        bool(update.password),
    ])

    # Require current password only for sensitive account changes on accounts that already have a local password.
    if user.password and requires_password_verification:
        if not update.current_password:
            raise HTTPException(status_code=400, detail="Current password is required")
        if not pwd_context.verify(update.current_password, user.password):
            raise HTTPException(status_code=401, detail="Current password is incorrect")
    # Apply updates
    if update.name:
        user.name = update.name
    if update.email and update.email != user.email:
        # Ensure email is unique
        if db.query(User).filter(User.email == update.email).first():
            raise HTTPException(status_code=400, detail="Email already in use")
        user.email = update.email
    if update.password:
        user.password = pwd_context.hash(update.password)
    if update.dark_mode is not None:
        user.dark_mode = update.dark_mode
    if update.email_notifications is not None:
        user.email_notifications = update.email_notifications
    if update.push_notifications is not None:
        user.push_notifications = update.push_notifications
    if update.notification_frequency is not None:
        user.notification_frequency = update.notification_frequency
    if update.language:
        user.language = update.language

    db.commit()
    db.refresh(user)

    try:
        cache_delete(CacheKeys.USER_PROFILE.format(user_id=user.id))
    except Exception as e:
        logger.warning(f"Cache DELETE failed for profile {user.id}: {e}")

    return {
        "msg": "Profile updated",
        "user": build_user_payload(user),
    }

@router.delete("/profile")
@limiter.limit("5/minute")
def delete_profile(
    request: Request,
    delete_req: UserDelete,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user = current_user

    if user.password:
        if not delete_req.current_password:
            raise HTTPException(status_code=400, detail="Current password is required")
        if not pwd_context.verify(delete_req.current_password, user.password):
            raise HTTPException(status_code=401, detail="Current password is incorrect")

    db.delete(user)
    db.commit()
    return {"msg": "Account deleted successfully"}

@router.get("/privacy-summary")
def get_privacy_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user = current_user

    message_count = sum(len(session.messages) for session in user.sessions)
    archived_sessions = sum(1 for session in user.sessions if session.is_archived)
    pinned_sessions = sum(1 for session in user.sessions if session.is_pinned)

    return {
        "sessions": len(user.sessions),
        "messages": message_count,
        "mood_entries": len(user.moods),
        "archived_sessions": archived_sessions,
        "pinned_sessions": pinned_sessions,
        "preferences": {
            "dark_mode": bool(user.dark_mode),
            "email_notifications": bool(user.email_notifications),
            "push_notifications": bool(user.push_notifications),
            "language": user.language or "English",
        },
    }

@router.get('/me')
def get_me(current_user: User = Depends(get_current_user)):
    return build_user_payload(current_user)

@router.post("/logout")
@limiter.limit("20/minute")
def logout(request: Request, response: Response, logout_data: LogoutRequest = None, db: Session = Depends(get_db)):
    # 1. Try to revoke the refresh token if provided
    refresh_token = request.cookies.get("refresh_token")
    
    # Fallback to body if not in cookie (for test compatibility)
    if not refresh_token and logout_data:
        refresh_token = logout_data.refresh_token
        
    if refresh_token:
        try:
            from jwt_handler import revoke_refresh_token
            revoke_refresh_token(refresh_token, db)
        except Exception as e:
            # Token might not exist or already be revoked, we ignore and proceed with logout
            logger.warning(f"Logout revocation failed: {str(e)}")
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"msg": "Logged out successfully"}
