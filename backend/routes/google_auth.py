from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from google.oauth2 import id_token
from google.auth.transport import requests
from sqlalchemy.orm import Session

from backend.models import User
from backend.database import get_db
from backend.jwt_handler import create_access_token

router = APIRouter()

GOOGLE_CLIENT_ID = "175457284636-oct6jlqgg1burgo2p04annu9hnj1bg6g.apps.googleusercontent.com"


@router.post("/google-login")
async def google_login(request: Request, db: Session = Depends(get_db)):
    body = await request.json()
    token = body.get("token")

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

        # Find or create user
        user = db.query(User).filter(User.google_id == google_user_id).first()
        if not user:
            username = email.split("@")[0] if email else None
            user = User(
                email=email,
                name=name,
                username=username,
                google_id=google_user_id,
                picture=picture,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        jwt_token = create_access_token({"email": user.email})

        return JSONResponse(
            content={
                "user": {
                    "id": user.id,
                    "name": user.name,
                    "username": user.username,
                    "email": user.email,
                    "picture": user.picture,
                },
                "token": jwt_token,
            }
        )

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid token")
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")
