from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

load_dotenv()

app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

cors_origins_str = os.getenv("CORS_ORIGINS", "http://localhost:5173")
cors_origins = [origin.strip() for origin in cors_origins_str.split(",") if origin.strip()]

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
