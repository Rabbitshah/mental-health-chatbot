from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request
from jose import JWTError
import os
from dotenv import load_dotenv
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"


def get_user_id_from_request(request: Request) -> str:
    """
    Custom key function for SlowAPI rate limiting.
    Extracts the user ID from the access_token cookie.
    Falls back to the client IP address if no valid token is found.
    """
    token = request.cookies.get("access_token")
    if token:
        try:
            from jose import jwt
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            # Use user_id as identifier (PII scrubbing: avoid email in Redis keys)
            user_id = payload.get("sub")
            if user_id:
                return f"user:{user_id}"
        except (JWTError, Exception):
            pass
    # Fall back to IP address for unauthenticated requests
    return get_remote_address(request)


# Disable rate limiting during tests automatically
import sys
is_testing = "pytest" in sys.modules or "PYTEST_CURRENT_TEST" in os.environ
enabled = os.getenv("RATELIMIT_ENABLED", "true").lower() == "true" and not is_testing

limiter = Limiter(key_func=get_user_id_from_request, enabled=enabled)
