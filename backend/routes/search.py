from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from models import User
from dependencies import get_current_user
from limiter import limiter

router = APIRouter()


@router.get("/search")
@limiter.limit("30/minute")
def search_messages(
    request: Request,
    q: Optional[str] = None,
    tag: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Search chat messages with optional filters.
    Full implementation in task 12.
    """
    from sqlalchemy import or_
    from models import ChatSession, ChatMessage
    from datetime import datetime

    query = db.query(ChatSession).filter(ChatSession.user_id == current_user.id)

    if tag:
        query = query.filter(ChatSession.tag == tag)

    if start:
        try:
            start_dt = datetime.fromisoformat(start)
            query = query.filter(ChatSession.created_at >= start_dt)
        except ValueError:
            pass

    if end:
        try:
            end_dt = datetime.fromisoformat(end)
            query = query.filter(ChatSession.created_at <= end_dt)
        except ValueError:
            pass

    sessions = query.all()

    results = []
    for session in sessions:
        if q:
            # Case-insensitive search across message text
            matching_msg = (
                db.query(ChatMessage)
                .filter(
                    ChatMessage.session_id == session.id,
                    ChatMessage.text.ilike(f"%{q}%"),
                )
                .first()
            )
            if not matching_msg:
                continue
            # Build snippet with context
            text = matching_msg.text
            idx = text.lower().find(q.lower())
            start_idx = max(0, idx - 50)
            end_idx = min(len(text), idx + len(q) + 50)
            snippet = ("..." if start_idx > 0 else "") + text[start_idx:end_idx] + ("..." if end_idx < len(text) else "")
        else:
            snippet = None

        results.append({
            "session_id": session.id,
            "session_title": session.title,
            "message_snippet": snippet,
            "created_at": session.created_at,
            "tag": session.tag,
        })

    return results
