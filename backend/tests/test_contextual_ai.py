"""
Unit tests for contextual AI conversation history (Task 8).

Tests:
- get_session_history: limited to 50 messages, ordered oldest-first
- format_history_for_gemini: correct role mapping and parts structure
- New session with no history produces empty list
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine, event, StaticPool
from sqlalchemy.orm import sessionmaker

from database import Base
from models import User, ChatSession, ChatMessage
from routes.chat import get_session_history, format_history_for_gemini

# ---------------------------------------------------------------------------
# Per-test in-memory SQLite engine (fresh DB for each test)
# ---------------------------------------------------------------------------

_TABLES_TO_CREATE = ["users", "chat_sessions", "chat_messages"]


@pytest.fixture
def db():
    """Fresh in-memory SQLite DB per test."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _enable_fk(dbapi_conn, _):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    for name in _TABLES_TO_CREATE:
        Base.metadata.tables[name].create(bind=engine, checkfirst=True)

    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def user(db):
    u = User(email="ctx_test@example.com", name="Ctx User", username="ctx_user", password="x")
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture
def chat_session(db, user):
    s = ChatSession(user_id=user.id, title="Test Session", tag="General")
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


def _add_messages(db, session_id: int, count: int):
    """Helper: add `count` alternating user/ai messages with distinct timestamps."""
    base_time = datetime(2024, 1, 1, 0, 0, 0)
    for i in range(count):
        sender = "user" if i % 2 == 0 else "ai"
        msg = ChatMessage(
            session_id=session_id,
            sender=sender,
            text=f"Message {i}",
            created_at=base_time + timedelta(seconds=i),
        )
        db.add(msg)
    db.commit()


# ---------------------------------------------------------------------------
# Tests for get_session_history (8.1)
# ---------------------------------------------------------------------------

class TestGetSessionHistory:
    def test_empty_session_returns_empty_list(self, db, chat_session):
        """New session with no messages returns empty list."""
        result = get_session_history(chat_session.id, db)
        assert result == []

    def test_returns_messages_ordered_oldest_first(self, db, chat_session):
        """Messages are returned in chronological order (oldest first)."""
        _add_messages(db, chat_session.id, 5)
        result = get_session_history(chat_session.id, db)
        assert len(result) == 5
        for i in range(len(result) - 1):
            assert result[i].created_at <= result[i + 1].created_at

    def test_limits_to_50_messages(self, db, chat_session):
        """When session has more than 50 messages, only the last 50 are returned."""
        _add_messages(db, chat_session.id, 60)
        result = get_session_history(chat_session.id, db)
        assert len(result) == 50

    def test_returns_most_recent_50_when_over_limit(self, db, chat_session):
        """The 50 returned messages are the most recent ones."""
        _add_messages(db, chat_session.id, 60)
        all_msgs = (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id == chat_session.id)
            .order_by(ChatMessage.created_at.asc())
            .all()
        )
        result = get_session_history(chat_session.id, db)
        # The oldest message in the result should be the 11th overall (index 10)
        assert result[0].id == all_msgs[10].id

    def test_returns_all_messages_when_under_limit(self, db, chat_session):
        """When session has fewer than 50 messages, all are returned."""
        _add_messages(db, chat_session.id, 20)
        result = get_session_history(chat_session.id, db)
        assert len(result) == 20

    def test_custom_limit_respected(self, db, chat_session):
        """Custom limit parameter is respected."""
        _add_messages(db, chat_session.id, 30)
        result = get_session_history(chat_session.id, db, limit=10)
        assert len(result) == 10


# ---------------------------------------------------------------------------
# Tests for format_history_for_gemini (8.2)
# ---------------------------------------------------------------------------

class TestFormatHistoryForGemini:
    def test_empty_messages_returns_empty_list(self):
        """Empty message list produces empty history."""
        assert format_history_for_gemini([]) == []

    def test_user_sender_maps_to_user_role(self):
        """DB sender 'user' maps to Gemini role 'user'."""
        msg = ChatMessage(sender="user", text="Hello", session_id=1)
        result = format_history_for_gemini([msg])
        assert result[0]["role"] == "user"

    def test_ai_sender_maps_to_model_role(self):
        """DB sender 'ai' maps to Gemini role 'model'."""
        msg = ChatMessage(sender="ai", text="Hi there", session_id=1)
        result = format_history_for_gemini([msg])
        assert result[0]["role"] == "model"

    def test_parts_structure_is_list_of_text_dicts(self):
        """Each message's parts is a list containing a dict with 'text' key."""
        msg = ChatMessage(sender="user", text="Test message", session_id=1)
        result = format_history_for_gemini([msg])
        assert isinstance(result[0]["parts"], list)
        assert len(result[0]["parts"]) == 1
        assert result[0]["parts"][0] == {"text": "Test message"}

    def test_multiple_messages_preserve_order(self):
        """Multiple messages are formatted in the same order they are provided."""
        msgs = [
            ChatMessage(sender="user", text="First", session_id=1),
            ChatMessage(sender="ai", text="Second", session_id=1),
            ChatMessage(sender="user", text="Third", session_id=1),
        ]
        result = format_history_for_gemini(msgs)
        assert len(result) == 3
        assert result[0] == {"role": "user", "parts": [{"text": "First"}]}
        assert result[1] == {"role": "model", "parts": [{"text": "Second"}]}
        assert result[2] == {"role": "user", "parts": [{"text": "Third"}]}

    def test_text_content_is_preserved(self):
        """Message text is preserved exactly in the formatted output."""
        text = "I've been feeling anxious about work lately."
        msg = ChatMessage(sender="user", text=text, session_id=1)
        result = format_history_for_gemini([msg])
        assert result[0]["parts"][0]["text"] == text
