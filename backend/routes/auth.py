from fastapi import APIRouter, HTTPException, Depends, Header, Request
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from pydantic import BaseModel, Field, validator
from dotenv import load_dotenv
import re
import json
import logging

from redis_client import cache_get, cache_set, cache_delete, CacheKeys, CacheTTL

logger = logging.getLogger(__name__)

from database import (
    SessionLocal,
    engine,
    ensure_chat_session_status_columns,
    ensure_user_preference_columns,
)
from models import User
from database import Base
from jwt_handler import create_access_token, decode_token
from limiter import limiter

import os

router = APIRouter()

# Load env (for DB, secret, etc.)
load_dotenv()

# Ensure tables exist
Base.metadata.create_all(bind=engine)
ensure_chat_session_status_columns()
ensure_user_preference_columns()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserCreate(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=8, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    username: str = Field(..., min_length=3, max_length=50)

    @validator('email')
    def validate_email_format(cls, v):
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, v):
            raise ValueError('Invalid email format')
        return v.lower()

    @validator('username')
    def validate_username(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        return v


class UserLogin(BaseModel):
    email: str
    password: str


class UserUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    password: str | None = None
    current_password: str | None = None
    dark_mode: bool | None = None
    email_notifications: bool | None = None
    push_notifications: bool | None = None
    language: str | None = None

class UserDelete(BaseModel):
    current_password: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def build_user_payload(user: User) -> dict:
    """Build a safe user payload dict (no password hash)."""
    return {
        "name": user.name,
        "username": user.username,
        "email": user.email,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }

@router.post("/signup")
def signup(user: UserCreate, db: Session = Depends(get_db)):
    # Check email
    existing_email = db.query(User).filter(User.email == user.email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Check username
    existing_username = db.query(User).filter(User.username == user.username).first()
    if existing_username:
        raise HTTPException(status_code=400, detail="Username already taken")

    # Hash password
    hashed_pw = pwd_context.hash(user.password)

    new_user = User(
        email=user.email,
        password=hashed_pw,
        name=user.name,
        username=user.username,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token({"email": new_user.email})

    return {
        "msg": "Signup successful",
        "user": build_user_payload(new_user),
        "token": token,
    }


@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user.email).first()
    if not existing or not existing.password or not pwd_context.verify(user.password, existing.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Create access token (15 minutes)
    access_token = create_access_token({"email": existing.email})
    
    # Create refresh token (7 days) and store in database
    from jwt_handler import create_refresh_token
    refresh_token = create_refresh_token(existing.id, db)

    return {
        "token": access_token,
        "refresh_token": refresh_token,
        "user": {
            "name": existing.name,
            "username": existing.username,
            "email": existing.email,
            "created_at": existing.created_at.isoformat() if existing.created_at else None,
        },
    }


@router.post("/auth/refresh")
def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """
    Exchange a valid refresh token for a new access token.
    """
    from jwt_handler import validate_refresh_token
    
    try:
        # Validate the refresh token and get the user
        user = validate_refresh_token(request.refresh_token, db)
        
        # Issue a new access token
        new_access_token = create_access_token({"email": user.email})
        
        return {
            "token": new_access_token,
            "token_type": "bearer"
        }
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/logout")
def logout(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """
    Revoke a refresh token to log out the user.
    """
    from jwt_handler import revoke_refresh_token
    
    try:
        revoke_refresh_token(request.refresh_token, db)
        return {"msg": "Logged out successfully"}
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/profile")
def get_profile(
    db: Session = Depends(get_db),
    authorization: str = Header(None),
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = authorization.split(" ")[1]
    try:
        payload = decode_token(token)
        user_email = payload.get("email")
        if not user_email:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    cache_key = CacheKeys.USER_PROFILE.format(user_id=user.id)
    try:
        cached = cache_get(cache_key)
        if cached:
            return json.loads(cached)
    except Exception as e:
        logger.warning(f"Cache GET failed for profile {user.id}: {e}")

    profile_data = {
        "name": user.name,
        "username": user.username,
        "email": user.email,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "dark_mode": bool(user.dark_mode),
        "email_notifications": bool(user.email_notifications),
        "push_notifications": bool(user.push_notifications),
        "language": user.language or "English",
    }

    try:
        cache_set(cache_key, json.dumps(profile_data), CacheTTL.USER_PROFILE)
    except Exception as e:
        logger.warning(f"Cache SET failed for profile {user.id}: {e}")

    return profile_data


@router.put("/profile")
def update_profile(
    update: UserUpdate,
    db: Session = Depends(get_db),
    authorization: str = Header(None),
):
    # Get bearer token
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = authorization.split(" ")[1]

    # Decode JWT
    try:
        payload = decode_token(token)
        user_email = payload.get("email")
        if not user_email:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Find user
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

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
def delete_profile(
    delete_req: UserDelete,
    db: Session = Depends(get_db),
    authorization: str = Header(None),
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ")[1]
    try:
        payload = decode_token(token)
        user_email = payload.get("email")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.password:
        if not delete_req.current_password:
            raise HTTPException(status_code=400, detail="Current password is required")
        if not pwd_context.verify(delete_req.current_password, user.password):
            raise HTTPException(status_code=401, detail="Current password is incorrect")

    db.delete(user)
    db.commit()
    return {"msg": "Account deleted successfully"}

@router.get("/export")
@limiter.limit("5/hour")
def export_data(
    request: Request,
    db: Session = Depends(get_db),
    authorization: str = Header(None),
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ")[1]
    try:
        payload = decode_token(token)
        user_email = payload.get("email")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    data = {
        "user": {
            "name": user.name,
            "email": user.email,
            "username": user.username,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "preferences": {
                "dark_mode": bool(user.dark_mode),
                "email_notifications": bool(user.email_notifications),
                "push_notifications": bool(user.push_notifications),
                "language": user.language or "English",
            },
        },
        "sessions": []
    }

    for session in user.sessions:
        session_data = {
            "id": session.id,
            "title": session.title,
            "tag": session.tag,
            "is_pinned": bool(session.is_pinned),
            "is_archived": bool(session.is_archived),
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat() if session.updated_at else None,
            "messages": [
                {
                    "sender": msg.sender,
                    "text": msg.text,
                    "created_at": msg.created_at.isoformat()
                } for msg in session.messages
            ]
        }
        data["sessions"].append(session_data)

    data["moods"] = [
        {
            "mood_score": m.mood_score,
            "energy_level": m.energy_level,
            "stress_level": m.stress_level,
            "date": m.date.isoformat()
        } for m in user.moods
    ]

    return data

@router.get("/privacy-summary")
def get_privacy_summary(
    db: Session = Depends(get_db),
    authorization: str = Header(None),
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ")[1]
    try:
        payload = decode_token(token)
        user_email = payload.get("email")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

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
