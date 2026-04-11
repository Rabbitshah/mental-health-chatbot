import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from database import get_db
from models import ChatSession, ChatMessage, User
from dependencies import get_current_user
from redis_client import cache_get, cache_set, cache_delete, CacheKeys, CacheTTL

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/history")

# Subtask 9.1: Allowed session tag values
ALLOWED_TAGS = ["General", "Anxiety", "Stress", "Depression", "Sleep", "Relationships", "Work", "Other"]

class MessageResponse(BaseModel):
    id: int
    sender: str
    text: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class SessionResponse(BaseModel):
    id: int
    title: str
    tag: Optional[str] = None
    is_pinned: bool = False
    is_archived: bool = False
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    preview: Optional[str] = None

    class Config:
        from_attributes = True

class SessionUpdateRequest(BaseModel):
    title: Optional[str] = None
    tag: Optional[str] = None

# Keep backward-compatible alias
SessionRenameRequest = SessionUpdateRequest

class BulkDeleteRequest(BaseModel):
    session_ids: List[int]

class SessionStatusRequest(BaseModel):
    is_pinned: Optional[bool] = None
    is_archived: Optional[bool] = None

class PaginatedSessionResponse(BaseModel):
    total: int
    page: int
    page_size: int
    sessions: List[SessionResponse]

def build_session_response(db: Session, session: ChatSession) -> SessionResponse:
    message_count = db.query(ChatMessage).filter(ChatMessage.session_id == session.id).count()
    first_ai_msg = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session.id, ChatMessage.sender == "ai")
        .order_by(ChatMessage.created_at.asc())
        .first()
    )

    preview = first_ai_msg.text[:100] + "..." if first_ai_msg else "Started a new conversation..."

    return SessionResponse(
        id=session.id,
        title=session.title,
        tag=session.tag,
        is_pinned=session.is_pinned,
        is_archived=session.is_archived,
        created_at=session.created_at,
        updated_at=session.updated_at,
        message_count=message_count,
        preview=preview,
    )

@router.get("/", response_model=PaginatedSessionResponse)
def get_all_sessions(
    q: Optional[str] = Query(default=None),
    tag: Optional[str] = Query(default=None),
    include_archived: bool = Query(default=False),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    search_query = (q or "").strip()
    use_cache = not search_query and not include_archived and page == 1 and page_size == 20 and not tag

    if use_cache:
        cache_key = CacheKeys.SESSION_LIST.format(user_id=current_user.id)
        cached = cache_get(cache_key)
        if cached is not None:
            try:
                return json.loads(cached)
            except (json.JSONDecodeError, Exception) as e:
                logger.warning(f"Failed to deserialize cached session list for user {current_user.id}: {e}")

    sessions_query = db.query(ChatSession).filter(ChatSession.user_id == current_user.id)
    if not include_archived:
        sessions_query = sessions_query.filter(ChatSession.is_archived == False)

    # Subtask 9.3: Filter by tag if provided
    if tag is not None:
        sessions_query = sessions_query.filter(ChatSession.tag == tag)

    if search_query:
        like_query = f"%{search_query}%"
        sessions_query = sessions_query.filter(
            or_(
                ChatSession.title.ilike(like_query),
                ChatSession.tag.ilike(like_query),
                ChatSession.messages.any(ChatMessage.text.ilike(like_query)),
            )
        )

    sessions_query = sessions_query.order_by(ChatSession.is_pinned.desc(), ChatSession.updated_at.desc())

    total = sessions_query.count()
    sessions = sessions_query.offset((page - 1) * page_size).limit(page_size).all()
    session_list = [build_session_response(db, session) for session in sessions]

    result = PaginatedSessionResponse(
        total=total,
        page=page,
        page_size=page_size,
        sessions=session_list,
    )

    if use_cache:
        try:
            serialized = json.dumps(
                result.model_dump(),
                default=lambda o: o.isoformat() if isinstance(o, datetime) else str(o),
            )
            cache_set(cache_key, serialized, CacheTTL.SESSION_LIST)
        except Exception as e:
            logger.warning(f"Failed to cache session list for user {current_user.id}: {e}")

    return result

@router.delete("/bulk")
def delete_sessions_bulk(
    request: BulkDeleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session_ids = list({session_id for session_id in request.session_ids if session_id is not None})
    if not session_ids:
        raise HTTPException(status_code=400, detail="No sessions selected")

    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.user_id == current_user.id, ChatSession.id.in_(session_ids))
        .all()
    )

    deleted_count = len(sessions)
    for session in sessions:
        db.delete(session)

    db.commit()

    try:
        cache_delete(CacheKeys.SESSION_LIST.format(user_id=current_user.id))
    except Exception as e:
        logger.warning(f"Cache invalidation failed after bulk delete for user {current_user.id}: {e}")

    return {
        "message": "Selected conversations deleted successfully",
        "deleted_sessions": deleted_count,
    }

@router.get("/{session_id}", response_model=List[MessageResponse])
def get_session_messages(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    chat_session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id).first()
    if not chat_session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    messages = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc()).all()
    return messages

@router.put("/{session_id}", response_model=SessionResponse)
def rename_session(session_id: int, request: SessionUpdateRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    chat_session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id).first()
    if not chat_session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Subtask 9.2: Validate title length (max 100 chars)
    if request.title is not None:
        if len(request.title) > 100:
            raise HTTPException(status_code=422, detail="Title must be 100 characters or fewer")
        chat_session.title = request.title

    # Subtask 9.2: Validate tag against allowed values
    if request.tag is not None:
        if request.tag not in ALLOWED_TAGS:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid tag. Allowed values: {', '.join(ALLOWED_TAGS)}"
            )
        chat_session.tag = request.tag

    # Subtask 9.2: Update updated_at timestamp
    chat_session.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(chat_session)

    try:
        cache_delete(CacheKeys.SESSION_LIST.format(user_id=current_user.id))
    except Exception as e:
        logger.warning(f"Cache invalidation failed after rename for session {session_id}: {e}")

    return build_session_response(db, chat_session)

@router.patch("/{session_id}/status", response_model=SessionResponse)
def update_session_status(
    session_id: int,
    request: SessionStatusRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    chat_session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id).first()
    if not chat_session:
        raise HTTPException(status_code=404, detail="Session not found")

    if request.is_pinned is not None:
        chat_session.is_pinned = request.is_pinned

    if request.is_archived is not None:
        chat_session.is_archived = request.is_archived
        if request.is_archived:
            chat_session.is_pinned = False

    db.commit()
    db.refresh(chat_session)

    try:
        cache_delete(CacheKeys.SESSION_LIST.format(user_id=current_user.id))
    except Exception as e:
        logger.warning(f"Cache invalidation failed after status update for session {session_id}: {e}")

    return build_session_response(db, chat_session)

@router.delete("/{session_id}")
def delete_session(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    chat_session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id).first()
    if not chat_session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    db.delete(chat_session)
    db.commit()

    try:
        cache_delete(CacheKeys.SESSION_LIST.format(user_id=current_user.id))
    except Exception as e:
        logger.warning(f"Cache invalidation failed after delete for session {session_id}: {e}")

    return {"message": "Session deleted successfully"}

@router.delete("/")
def delete_all_sessions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sessions = db.query(ChatSession).filter(ChatSession.user_id == current_user.id).all()

    deleted_count = len(sessions)
    for session in sessions:
        db.delete(session)

    db.commit()

    try:
        cache_delete(CacheKeys.SESSION_LIST.format(user_id=current_user.id))
    except Exception as e:
        logger.warning(f"Cache invalidation failed after delete-all for user {current_user.id}: {e}")

    return {
        "message": "All conversation history deleted successfully",
        "deleted_sessions": deleted_count,
    }
