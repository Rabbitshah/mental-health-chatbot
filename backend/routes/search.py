from fastapi import APIRouter, Depends, Request, Query, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

from database import get_db
from models import User, ChatSession, ChatMessage
from dependencies import get_current_user
from limiter import limiter

router = APIRouter()

SNIPPET_CONTEXT = 50  # characters of context around the match


class SearchResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    session_id: int
    session_title: str
    message_snippet: Optional[str]
    created_at: datetime
    tag: Optional[str]


def build_snippet(text: str, query: str, context: int = SNIPPET_CONTEXT) -> str:
    """Build a snippet with ~context characters around the matched query text."""
    idx = text.lower().find(query.lower())
    if idx == -1:
        # Fallback: return beginning of text
        return text[:context * 2] + ("..." if len(text) > context * 2 else "")

    start_idx = max(0, idx - context)
    end_idx = min(len(text), idx + len(query) + context)

    prefix = "..." if start_idx > 0 else ""
    suffix = "..." if end_idx < len(text) else ""
    return prefix + text[start_idx:end_idx] + suffix


@router.get("/search", response_model=List[SearchResult])
@limiter.limit("30/minute")
def search_messages(
    request: Request,
    q: Optional[str] = Query(default=None, description="Search query text"),
    tag: Optional[str] = Query(default=None, description="Filter by session tag"),
    start: Optional[str] = Query(default=None, description="Start date (ISO format)"),
    end: Optional[str] = Query(default=None, description="End date (ISO format)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Search chat messages with optional filters.

    - **q**: Case-insensitive text search across message content (Req 7.1, 7.2)
    - **tag**: Filter sessions by tag (Req 7.3)
    - **start/end**: Filter sessions by date range (Req 7.4)
    - Filters can be combined (Req 7.5)
    - Returns message snippets with context around matched text (Req 7.6)
    """
    # Parse date range parameters
    start_dt: Optional[datetime] = None
    end_dt: Optional[datetime] = None

    if start:
        try:
            start_dt = datetime.fromisoformat(start)
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid start date format. Use ISO format (e.g. 2024-01-01 or 2024-01-01T00:00:00)")

    if end:
        try:
            end_dt = datetime.fromisoformat(end)
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid end date format. Use ISO format (e.g. 2024-01-31 or 2024-01-31T23:59:59)")

    # Build base session query for the current user
    sessions_query = db.query(ChatSession).filter(ChatSession.user_id == current_user.id)

    # Req 7.3: Filter by tag if provided
    if tag:
        sessions_query = sessions_query.filter(ChatSession.tag == tag)

    # Req 7.4: Filter by date range if provided
    if start_dt:
        sessions_query = sessions_query.filter(ChatSession.created_at >= start_dt)
    if end_dt:
        sessions_query = sessions_query.filter(ChatSession.created_at <= end_dt)

    sessions = sessions_query.order_by(ChatSession.updated_at.desc()).all()

    results: List[SearchResult] = []

    if q and q.strip():
        # Req 7.1, 7.2: Fetch the earliest matching message per session in ONE query,
        # avoiding the N+1 pattern (one query per session).
        from sqlalchemy import func
        from sqlalchemy import select as sa_select

        session_ids = [s.id for s in sessions]
        if not session_ids:
            return results

        # Subquery: earliest matching message id per session
        min_id_subq = (
            sa_select(func.min(ChatMessage.id))
            .where(
                ChatMessage.session_id.in_(session_ids),
                ChatMessage.text.ilike(f"%{q}%"),
            )
            .group_by(ChatMessage.session_id)
            .scalar_subquery()
        )
        matching_msgs = (
            db.query(ChatMessage)
            .filter(ChatMessage.id.in_(min_id_subq))
            .all()
        )
        # Build a lookup: session_id -> first matching message
        match_map = {msg.session_id: msg for msg in matching_msgs}

        for session in sessions:
            msg = match_map.get(session.id)
            if not msg:
                continue  # no matching message in this session
            results.append(
                SearchResult(
                    session_id=session.id,
                    session_title=session.title,
                    message_snippet=build_snippet(msg.text, q),
                    created_at=session.created_at,
                    tag=session.tag,
                )
            )
    else:
        # No text query — include all matching sessions without a snippet
        results = [
            SearchResult(
                session_id=session.id,
                session_title=session.title,
                message_snippet=None,
                created_at=session.created_at,
                tag=session.tag,
            )
            for session in sessions
        ]

    return results
