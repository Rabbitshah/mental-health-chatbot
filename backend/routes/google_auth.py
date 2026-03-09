from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from google.oauth2 import id_token
from google.auth.transport import requests
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()  # This will load from .env in the current directory

from models import User
from database import get_db
from jwt_handler import create_access_token

router = APIRouter()

# Get Google Client ID from environment variables
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
if not GOOGLE_CLIENT_ID:
    raise ValueError("GOOGLE_CLIENT_ID environment variable not set")

# Rest of your google_auth.py code remains the same...


@router.post("/google-login")
async def google_login(request: Request, db: Session = Depends(get_db)):
    try:
        body = await request.json()
        token = body.get("credential")

        if not token:
            raise HTTPException(status_code=400, detail="Token not provided")

        try:
            # Verify Google ID token
            idinfo = id_token.verify_oauth2_token(
                token,
                requests.Request(),
                GOOGLE_CLIENT_ID,
            )

            google_user_id = idinfo["sub"]
            email = idinfo.get("email")
            name = idinfo.get("name")
            picture = idinfo.get("picture")

            if not email:
                raise HTTPException(status_code=400, detail="Email not provided by Google")

            # Find or create user
            user = db.query(User).filter(User.google_id == google_user_id).first()
            
            if not user:
                # Try to find by email
                user = db.query(User).filter(User.email == email).first()
                if user:
                    # Update existing user with google_id
                    user.google_id = google_user_id
                    if not user.picture and picture:
                        user.picture = picture
                    db.commit()
                    db.refresh(user)
                else:
                    # Create new user
                    username = email.split('@')[0]
                    # Ensure username is unique
                    existing_user = db.query(User).filter(User.username == username).first()
                    if existing_user:
                        username = f"{username}_{google_user_id[-6:]}"
                    
                    user = User(
                        email=email,
                        name=name or email.split('@')[0],
                        username=username,
                        google_id=google_user_id,
                        picture=picture,
                        password=None  # No password for Google users
                    )
                    db.add(user)
                    db.commit()
                    db.refresh(user)

            jwt_token = create_access_token({"email": user.email})

            return {
                "user": {
                    "id": user.id,
                    "name": user.name,
                    "username": user.username,
                    "email": user.email,
                    "picture": user.picture,
                },
                "token": jwt_token
            }

        except ValueError as ve:
            print(f"ValueError in Google token verification: {str(ve)}")
            raise HTTPException(status_code=400, detail=f"Invalid token: {str(ve)}")

    except OperationalError as oe:
        db.rollback()
        print(f"Database error in Google login: {str(oe)}")
        raise HTTPException(status_code=503, detail="Database connection lost. Please try again.")
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Unexpected error in Google login: {str(e)}\n{error_details}")
        raise HTTPException(status_code=500, detail="Internal server error")