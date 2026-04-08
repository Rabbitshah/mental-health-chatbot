from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from limiter import limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
import os
from dotenv import load_dotenv

from routes.auth import router as auth_router
from routes.chat import router as chat_router  
from routes import google_auth
from routes.history import router as history_router
from routes.insights import router as insights_router
from routes.search import router as search_router

load_dotenv()

# --- Task 3.1: CORS startup validation ---
cors_origins_str = os.getenv("CORS_ORIGINS")
if not cors_origins_str:
    raise RuntimeError(
        "CORS_ORIGINS environment variable is not set. "
        "Please set it in your .env file (see .env.example for reference). "
        "Example: CORS_ORIGINS=http://localhost:5173,http://localhost:3000"
    )
cors_origins = [origin.strip() for origin in cors_origins_str.split(",") if origin.strip()]

# --- Task 3.3: Security headers middleware ---
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
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
        if ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        return response

app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(SecurityHeadersMiddleware)

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
