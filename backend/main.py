from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from limiter import limiter
from slowapi.errors import RateLimitExceeded
import os
from dotenv import load_dotenv

from logger import setup_logging, get_logger
from middleware import RequestLoggingMiddleware

from routes.auth import router as auth_router
from routes.chat import router as chat_router  
from routes import google_auth
from routes.history import router as history_router
from routes.insights import router as insights_router
from routes.search import router as search_router
from routes.export import router as export_router
from routes.notifications import router as notifications_router
from routes.wellness import router as wellness_router

load_dotenv()

# --- Task 18.1: Initialize structured logging ---
setup_logging()
logger = get_logger(__name__)

# --- Task 23.2: Validate required environment variables on startup ---
_REQUIRED_ENV_VARS = {
    "SECRET_KEY": "JWT signing secret. Set a long random string.",
    "DATABASE_URL": "PostgreSQL connection URL. Example: postgresql://user:pass@localhost:5432/db",
    "GEMINI_API_KEY": "Google Gemini API key for AI responses.",
    "CORS_ORIGINS": (
        "Comma-separated list of allowed frontend origins. "
        "Example: CORS_ORIGINS=http://localhost:5173,http://localhost:3000"
    ),
}

_missing = [
    f"  {var}: {hint}"
    for var, hint in _REQUIRED_ENV_VARS.items()
    if not os.getenv(var)
]
if _missing:
    raise RuntimeError(
        "Missing required environment variables (see .env.example for reference):\n"
        + "\n".join(_missing)
    )

cors_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "").split(",")
    if origin.strip()
]

# --- Task 3.3: Security headers middleware ---
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, environment: str = ENVIRONMENT):
        super().__init__(app)
        self.environment = environment

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https:;"
        )
        if self.environment == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        return response

app = FastAPI()
app.state.limiter = limiter

# --- Task 18.5: Rate limit violation logging ---
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    user_id = None
    token = request.cookies.get("access_token")
    if token:
        try:
            import os as _os
            from jose import jwt as _jwt
            payload = _jwt.decode(token, _os.getenv("SECRET_KEY", ""), algorithms=["HS256"])
            user_id = payload.get("sub")
        except Exception:
            pass

    logger.warning(
        "rate limit exceeded",
        extra={
            "user_id": user_id,
            "path": request.url.path,
            "method": request.method,
            "limit": str(exc.detail) if hasattr(exc, "detail") else str(exc),
        },
    )
    return JSONResponse(
        status_code=429,
        content={"detail": f"Rate limit exceeded: {exc.detail}"},
        headers={"Retry-After": "60"},
    )

async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Log the full error internally via RequestLoggingMiddleware (which handles this)
    # but return a clean message to the client.
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Our team has been notified."},
    )

app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
app.add_exception_handler(Exception, global_exception_handler)

app.add_middleware(SecurityHeadersMiddleware)

# --- Task 18.2: Request logging middleware ---
app.add_middleware(RequestLoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Cross-Origin-Opener-Policy"],
)

app.include_router(auth_router)  
app.include_router(chat_router)  
app.include_router(google_auth.router) 
app.include_router(history_router)
app.include_router(insights_router)
app.include_router(search_router)
app.include_router(export_router)
app.include_router(notifications_router)
app.include_router(wellness_router)
