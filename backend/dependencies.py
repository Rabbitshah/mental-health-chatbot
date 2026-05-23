from fastapi import Depends, HTTPException, status, Cookie, Header
from sqlalchemy.orm import Session
from database import get_db
from models import User
from jwt_handler import decode_token

def get_current_user(
    db: Session = Depends(get_db),
    access_token: str | None = Cookie(None),
    auth_header: str | None = Header(None, alias="Authorization")
):
    if not access_token and auth_header and auth_header.startswith("Bearer "):
        access_token = auth_header.split(" ")[1]
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not access_token:
        raise credentials_exception
        
    try:
        payload = decode_token(access_token)
        email: str = payload.get("email")
        if email is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception
        
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
        
    return user
