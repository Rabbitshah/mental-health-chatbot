from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from database import get_db
from models import ChatSession, ChatMessage, User
from dependencies import get_current_user

router = APIRouter(prefix="/history")

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

class SessionRenameRequest(BaseModel):
    title: str

class BulkDeleteRequest(BaseModel):
    session_ids: List[int]

class SessionStatusRequest(BaseModel):
    is_pinned: Optional[bool] = None
    is_archived: Optional[bool] = None

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

@router.get("/", response_model=List[SessionResponse])
def get_all_sessions(
    q: Optional[str] = Query(default=None),
    include_archived: bool = Query(default=False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sessions_query = db.query(ChatSession).filter(ChatSession.user_id == current_user.id)
    if not include_archived:
        sessions_query = sessions_query.filter(ChatSession.is_archived == False)

    search_query = (q or "").strip()
    if search_query:
        like_query = f"%{search_query}%"
        sessions_query = sessions_query.filter(
            or_(
                ChatSession.title.ilike(like_query),
                ChatSession.tag.ilike(like_query),
                ChatSession.messages.any(ChatMessage.text.ilike(like_query)),
            )
        )

    sessions = sessions_query.order_by(ChatSession.is_pinned.desc(), ChatSession.updated_at.desc()).all()
    return [build_session_response(db, session) for session in sessions]

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
def rename_session(session_id: int, request: SessionRenameRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    chat_session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id).first()
    if not chat_session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    chat_session.title = request.title
    db.commit()
    db.refresh(chat_session)

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
    return build_session_response(db, chat_session)

@router.delete("/{session_id}")
def delete_session(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    chat_session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id).first()
    if not chat_session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    db.delete(chat_session)
    db.commit()
    return {"message": "Session deleted successfully"}

@router.delete("/")
def delete_all_sessions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sessions = db.query(ChatSession).filter(ChatSession.user_id == current_user.id).all()

    deleted_count = len(sessions)
    for session in sessions:
        db.delete(session)

    db.commit()
    return {
        "message": "All conversation history deleted successfully",
        "deleted_sessions": deleted_count,
    }
