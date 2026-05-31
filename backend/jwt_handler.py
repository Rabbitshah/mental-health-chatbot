from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
import os
import secrets
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from pathlib import Path

# Load environment from backend/.env
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("SECRET_KEY")
assert SECRET_KEY, (
    "SECRET_KEY environment variable must be set. "
    "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15  # Updated from 60 to 15 minutes
REFRESH_TOKEN_EXPIRE_DAYS = 7

def create_access_token(user_id: int, expires_delta: timedelta | None = None) -> str:
    """Create a short-lived JWT access token containing the user's ID as 'sub'."""
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode = {"sub": str(user_id), "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise

def create_refresh_token(user_id: int, db: Session) -> str:
    """
    Create a refresh token for a user and store it in the database.
    
    Args:
        user_id: The ID of the user
        db: Database session
        
    Returns:
        The refresh token string
    """
    from models import RefreshToken
    
    # Generate a secure random token
    token = secrets.token_urlsafe(32)
    
    # Calculate expiry (stored as UTC, timezone-aware to match _utcnow() in models)
    expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    # Store in database
    refresh_token = RefreshToken(
        user_id=user_id,
        token=token,
        expires_at=expires_at,
        revoked=False
    )
    db.add(refresh_token)
    db.commit()
    
    return token

def validate_refresh_token(token: str, db: Session):
    """
    Validate a refresh token against the database.
    
    Args:
        token: The refresh token string
        db: Database session
        
    Returns:
        The User object if token is valid
        
    Raises:
        ValueError: If token is invalid, expired, or revoked
    """
    from models import RefreshToken, User
    
    # Query the token from database
    refresh_token = db.query(RefreshToken).filter(
        RefreshToken.token == token
    ).first()
    
    if not refresh_token:
        raise ValueError("Invalid refresh token")
    
    if refresh_token.revoked:
        raise ValueError("Refresh token has been revoked")
    
    expires_at = refresh_token.expires_at
    # Make expires_at timezone-aware if it was stored naïvely (legacy rows)
    if expires_at.tzinfo is None:
        from datetime import timezone as _tz
        expires_at = expires_at.replace(tzinfo=_tz.utc)
    if expires_at < datetime.now(timezone.utc):
        raise ValueError("Refresh token has expired")
    
    # Get the associated user
    user = db.query(User).filter(User.id == refresh_token.user_id).first()
    
    if not user:
        raise ValueError("User not found")
    
    return user

def revoke_refresh_token(token: str, db: Session) -> None:
    """
    Revoke a refresh token by marking it as revoked in the database.
    
    Args:
        token: The refresh token string
        db: Database session
        
    Raises:
        ValueError: If token is not found
    """
    from models import RefreshToken
    
    refresh_token = db.query(RefreshToken).filter(
        RefreshToken.token == token
    ).first()
    
    if not refresh_token:
        raise ValueError("Refresh token not found")
    
    refresh_token.revoked = True
    db.commit()
