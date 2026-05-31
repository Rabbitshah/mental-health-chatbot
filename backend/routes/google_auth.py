import logging
import os

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from google.auth.transport import requests
from google.oauth2 import id_token
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from database import get_db
from jwt_handler import create_access_token, create_refresh_token
from models import User

load_dotenv()

logger = logging.getLogger(__name__)
router = APIRouter()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
# Validated at startup in main.py via _REQUIRED_ENV_VARS; assert here for safety
# when this module is imported outside the main app (e.g., tests).
assert GOOGLE_CLIENT_ID, "GOOGLE_CLIENT_ID must be set"


def _unique_username(db: Session, requested_username: str) -> str:
    """Return a unique username, appending a random hex suffix when needed."""
    import secrets

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


@router.post("/google-login")
async def google_login(request: Request, db: Session = Depends(get_db)):
    try:
        body = await request.json()
        credential = body.get("credential")

        if not credential:
            raise HTTPException(status_code=400, detail="Token not provided")

        try:
            idinfo = id_token.verify_oauth2_token(
                credential,
                requests.Request(),
                GOOGLE_CLIENT_ID,
            )
        except ValueError as ve:
            logger.warning("Google token verification failed: %s", ve)
            raise HTTPException(status_code=400, detail="Invalid Google token")

        google_user_id: str = idinfo["sub"]
        email: str | None = idinfo.get("email")
        name: str | None = idinfo.get("name")
        picture: str | None = idinfo.get("picture")

        if not email:
            raise HTTPException(status_code=400, detail="Email not provided by Google")

        # Find or create user
        user = db.query(User).filter(User.google_id == google_user_id).first()
        if not user:
            user = db.query(User).filter(User.email == email).first()
            if user:
                # Link existing account to Google
                user.google_id = google_user_id
                if not user.picture and picture:
                    user.picture = picture
                db.commit()
                db.refresh(user)
            else:
                # New user — derive a username from email prefix and ensure uniqueness
                username_base = email.split("@")[0][:42] or "user"
                username = _unique_username(db, username_base)

                user = User(
                    email=email,
                    name=name or username_base,
                    username=username,
                    google_id=google_user_id,
                    picture=picture,
                    password=None,  # Google-only account — no local password
                )
                db.add(user)
                db.commit()
                db.refresh(user)

        # Issue tokens
        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id, db)

        # Build a JSONResponse so we can attach cookies
        response = JSONResponse(
            content={
                "msg": "Google login successful",
                "user": {
                    "id": user.id,
                    "name": user.name,
                    "username": user.username,
                    "email": user.email,
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                    "picture": user.picture,
                    "has_password": bool(user.password),
                    "auth_provider": "google" if user.google_id and not user.password else "local",
                },
                # Tokens are intentionally NOT returned in the body.
                # They are delivered exclusively via HttpOnly cookies.
            }
        )
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=15 * 60,
        )
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=7 * 24 * 60 * 60,
        )
        return response

    except HTTPException:
        raise
    except OperationalError as oe:
        db.rollback()
        logger.error("Database error in Google login: %s", oe, exc_info=True)
        raise HTTPException(status_code=503, detail="Database connection lost. Please try again.")
    except Exception as e:
        logger.error("Unexpected error in Google login: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
