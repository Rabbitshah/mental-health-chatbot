from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from google.oauth2 import id_token
from google.auth.transport import requests
from sqlalchemy.orm import Session

from models import User
from database import get_db
from jwt_handler import create_access_token

router = APIRouter()

GOOGLE_CLIENT_ID = "175457284636-oct6jlqgg1burgo2p04annu9hnj1bg6g.apps.googleusercontent.com"

@router.post("/google-login")
async def google_login(request: Request, db: Session = Depends(get_db)):
    try:
        body = await request.json()
        token = body.get("credential")  # ✅ Correct key

        if not token:
            raise HTTPException(status_code=400, detail="Token missing")

        idinfo = id_token.verify_oauth2_token(token, requests.Request(), GOOGLE_CLIENT_ID)

        email = idinfo["email"]
        name = idinfo.get("name")
        picture = idinfo.get("picture")

        user = db.query(User).filter(User.email == email).first()

        if not user:
            # Auto-generate a unique username from email
            base_username = email.split("@")[0]
            username = base_username
            counter = 1
            while db.query(User).filter(User.username == username).first():
                username = f"{base_username}{counter}"
                counter += 1
            user = User(name=name, email=email, picture=picture, username=username)
            db.add(user)
            db.commit()
            db.refresh(user)

        token_data = {"sub": str(user.id), "email": user.email}
        jwt_token = create_access_token(token_data)

        return JSONResponse(content={
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "picture": user.picture,
            },
            "token": jwt_token,
        })

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid token")
    except Exception as e:
        print("Google Login Error:", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

