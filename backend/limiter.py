from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request
from jose import JWTError
import os

SECRET_KEY = os.getenv("SECRET_KEY", "your_default_secret_key")
ALGORITHM = "HS256"


def get_user_id_from_request(request: Request) -> str:
    """
    Custom key function for SlowAPI rate limiting.

    Extracts the user ID from the JWT token in the Authorization header.
    Falls back to the client IP address if no valid token is found.
    """
    authorization: str = request.headers.get("Authorization", "")
    if authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1]
        try:
            from jose import jwt
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            # Use email as the user identifier (matches the token payload structure)
            user_email = payload.get("email")
            if user_email:
                return f"user:{user_email}"
        except (JWTError, Exception):
            pass
    # Fall back to IP address for unauthenticated requests
    return get_remote_address(request)


limiter = Limiter(key_func=get_user_id_from_request)
