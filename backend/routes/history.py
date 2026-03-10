from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
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
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    preview: Optional[str] = None

    class Config:
        from_attributes = True

class SessionRenameRequest(BaseModel):
    title: str

@router.get("/", response_model=List[SessionResponse])
def get_all_sessions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sessions = db.query(ChatSession).filter(ChatSession.user_id == current_user.id).order_by(ChatSession.updated_at.desc()).all()
    
    result = []
    for s in sessions:
        message_count = db.query(ChatMessage).filter(ChatMessage.session_id == s.id).count()
        first_ai_msg = db.query(ChatMessage).filter(ChatMessage.session_id == s.id, ChatMessage.sender == 'ai').order_by(ChatMessage.created_at.asc()).first()
        
        preview = first_ai_msg.text[:100] + "..." if first_ai_msg else "Started a new conversation..."
        
        result.append(SessionResponse(
            id=s.id,
            title=s.title,
            tag=s.tag,
            created_at=s.created_at,
            updated_at=s.updated_at,
            message_count=message_count,
            preview=preview
        ))
        
    return result

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
    
    # Return basic info to satisfy the model (we won't need full accurate count for the response here)
    return SessionResponse(
        id=chat_session.id,
        title=chat_session.title,
        tag=chat_session.tag,
        created_at=chat_session.created_at,
        updated_at=chat_session.updated_at,
        message_count=0,
        preview=""
    )

@router.delete("/{session_id}")
def delete_session(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    chat_session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id).first()
    if not chat_session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    db.delete(chat_session)
    db.commit()
    return {"message": "Session deleted successfully"}
