"""
Request logging middleware for the mental health chatbot backend.
Requirement 16.1, 16.2
"""
import time
import traceback

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from logger import get_logger

logger = get_logger(__name__)

# Header used by JWT auth


def _extract_user_id(request: Request) -> str | None:
    """Best-effort extraction of user identity from the access_token cookie."""
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        import os
        from jose import jwt

        secret = os.getenv("SECRET_KEY", "")
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return payload.get("sub")
    except Exception:
        return None


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs every incoming request and its response.

    On success logs: timestamp (in JsonFormatter), method, path, user_id,
    status_code, response_time_ms.

    On unhandled exception logs: the same fields plus the full stack trace.
    Requirement 16.1, 16.2
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()
        user_id = _extract_user_id(request)
        path = request.url.path
        method = request.method

        try:
            response: Response = await call_next(request)
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)

            logger.info(
                "request completed",
                extra={
                    "method": method,
                    "path": path,
                    "user_id": user_id,
                    "status_code": response.status_code,
                    "response_time_ms": elapsed_ms,
                },
            )
            return response

        except Exception as exc:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.error(
                "unhandled exception during request",
                extra={
                    "method": method,
                    "path": path,
                    "user_id": user_id,
                    "response_time_ms": elapsed_ms,
                    "exception": traceback.format_exc(),
                },
                exc_info=True,
            )
            raise
