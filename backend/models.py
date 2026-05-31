from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float, Text, Boolean, ARRAY, Index
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base


def _utcnow():
    """Return current UTC time as a timezone-aware datetime."""
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String)
    username = Column(String, unique=True, index=True, nullable=True)
    password = Column(String, nullable=True)
    google_id = Column(String, nullable=True)
    picture = Column(String, nullable=True)
    dark_mode = Column(Boolean, nullable=False, default=False)
    email_notifications = Column(Boolean, nullable=False, default=True)
    push_notifications = Column(Boolean, nullable=False, default=True)
    notification_frequency = Column(String, nullable=False, default="daily")
    language = Column(String, nullable=False, default="English")
    created_at = Column(DateTime, default=_utcnow)

    sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    moods = relationship("MoodEntry", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    crisis_events = relationship("CrisisEvent", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    safety_plan = relationship("SafetyPlan", back_populates="user", cascade="all, delete-orphan", uselist=False)
    journals = relationship("JournalEntry", back_populates="user", cascade="all, delete-orphan")

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    title = Column(String, nullable=False, default="New Conversation")
    title_is_auto = Column(Boolean, nullable=False, default=True)
    tag = Column(String, nullable=True, default="General", index=True)
    summary = Column(Text, nullable=True)
    is_pinned = Column(Boolean, nullable=False, default=False)
    is_archived = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, index=True)

    user = relationship("User", back_populates="sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), index=True)
    sender = Column(String, nullable=False) # 'user' or 'ai'
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=_utcnow, index=True)

    __table_args__ = (
        Index("idx_messages_session_created", "session_id", "created_at"),
    )

    session = relationship("ChatSession", back_populates="messages")

class MoodEntry(Base):
    __tablename__ = "mood_entries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    mood_score = Column(Float, nullable=False) # e.g. 1 to 10
    energy_level = Column(Float, nullable=False)
    stress_level = Column(Float, nullable=False)
    date = Column(DateTime, default=_utcnow, index=True)

    __table_args__ = (
        Index("idx_mood_user_date", "user_id", "date"),
    )

    user = relationship("User", back_populates="moods")

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token = Column(String, unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=_utcnow)
    revoked = Column(Boolean, default=False)

    user = relationship("User", back_populates="refresh_tokens")

    # Composite index speeds up cleanup queries: WHERE revoked = false AND expires_at < now()
    __table_args__ = (
        Index("ix_refresh_tokens_revoked_expires_at", "revoked", "expires_at"),
    )

class CrisisEvent(Base):
    __tablename__ = "crisis_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    message_id = Column(Integer, ForeignKey("chat_messages.id"), nullable=True)
    keywords = Column(ARRAY(String), nullable=True)
    confidence = Column(Float, nullable=False, default=0.0)
    detection_method = Column(String, nullable=False, default="keyword")
    created_at = Column(DateTime, default=_utcnow, index=True)

    user = relationship("User", back_populates="crisis_events")
    message = relationship("ChatMessage")

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    type = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    read = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=_utcnow, index=True)

    __table_args__ = (
        Index("idx_notifications_user_read", "user_id", "read"),
    )

    user = relationship("User", back_populates="notifications")

class SafetyPlan(Base):
    __tablename__ = "safety_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    warning_signs = Column(Text, nullable=False, default="[]")
    coping_strategies = Column(Text, nullable=False, default="[]")
    trusted_contacts = Column(Text, nullable=False, default="[]")
    professional_contacts = Column(Text, nullable=False, default="[]")
    safe_environment_steps = Column(Text, nullable=False, default="[]")
    reasons_to_stay = Column(Text, nullable=False, default="[]")
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, index=True)
    created_at = Column(DateTime, default=_utcnow)

    user = relationship("User", back_populates="safety_plan")

class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String, nullable=False, default="Reflection")
    mood_label = Column(String, nullable=True)
    mood_score = Column(Float, nullable=True)
    trigger = Column(Text, nullable=True)
    thought = Column(Text, nullable=True)
    body_feeling = Column(Text, nullable=True)
    reframe = Column(Text, nullable=True)
    next_step = Column(Text, nullable=True)
    tags = Column(Text, nullable=False, default="[]")
    created_at = Column(DateTime, default=_utcnow, index=True)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, index=True)

    __table_args__ = (
        Index("idx_journal_user_created", "user_id", "created_at"),
    )

    user = relationship("User", back_populates="journals")
