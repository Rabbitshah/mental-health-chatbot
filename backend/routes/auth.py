from fastapi import APIRouter, HTTPException, Depends, Header
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from pydantic import BaseModel
from dotenv import load_dotenv

from database import SessionLocal, engine
from models import User
from database import Base
from jwt_handler import create_access_token, decode_token

import os

router = APIRouter()

# Load env (for DB, secret, etc.)
load_dotenv()

# Ensure tables exist
Base.metadata.create_all(bind=engine)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserCreate(BaseModel):
    email: str
    password: str
    name: str
    username: str


class UserLogin(BaseModel):
    email: str
    password: str


class UserUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    password: str | None = None
    current_password: str

class UserDelete(BaseModel):
    current_password: str

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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
        "user": {
            "name": new_user.name,
            "username": new_user.username,
            "email": new_user.email,
            "created_at": new_user.created_at.isoformat() if new_user.created_at else None,
        },
        "token": token,
    }


@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user.email).first()
    if not existing or not pwd_context.verify(user.password, existing.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"email": existing.email})

    return {
        "token": token,
        "user": {
            "name": existing.name,
            "username": existing.username,
            "email": existing.email,
            "created_at": existing.created_at.isoformat() if existing.created_at else None,
        },
    }


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

    # Check current password
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

    db.commit()
    db.refresh(user)

    return {
        "msg": "Profile updated",
        "user": {
            "name": user.name,
            "username": user.username,
            "email": user.email,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        },
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

    if not pwd_context.verify(delete_req.current_password, user.password):
        raise HTTPException(status_code=401, detail="Current password is incorrect")

    db.delete(user)
    db.commit()
    return {"msg": "Account deleted successfully"}

@router.get("/export")
def export_data(
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
            "created_at": user.created_at.isoformat() if user.created_at else None
        },
        "sessions": []
    }

    for session in user.sessions:
        session_data = {
            "title": session.title,
            "created_at": session.created_at.isoformat(),
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
