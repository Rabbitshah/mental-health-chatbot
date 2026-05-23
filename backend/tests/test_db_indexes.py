"""
Tests to verify required database indexes exist at the SQLAlchemy metadata level.

Validates: Requirements 13.1, 13.2, 13.3, 13.4
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from sqlalchemy import inspect as sa_inspect
from models import User, ChatSession, ChatMessage, MoodEntry, Base


def get_index_columns(table):
    """Return a set of frozensets, each representing the columns in one index."""
    return {frozenset(idx.columns.keys()) for idx in table.indexes}


def get_indexed_columns(table):
    """Return a flat set of all individually indexed column names."""
    cols = set()
    for idx in table.indexes:
        cols.update(idx.columns.keys())
    return cols


# Req 13.1 — index on users.email
def test_users_email_index():
    """Req 13.1: users.email must be indexed for login query performance."""
    indexed = get_indexed_columns(User.__table__)
    assert "email" in indexed, "Missing index on users.email (Req 13.1)"


# Req 13.2 — index on chat_sessions.user_id
def test_chat_sessions_user_id_index():
    """Req 13.2: chat_sessions.user_id must be indexed for session retrieval."""
    indexed = get_indexed_columns(ChatSession.__table__)
    assert "user_id" in indexed, "Missing index on chat_sessions.user_id (Req 13.2)"


# Req 13.3 — composite index on (chat_messages.session_id, chat_messages.created_at)
def test_chat_messages_composite_index():
    """Req 13.3: composite index on (chat_messages.session_id, chat_messages.created_at)."""
    index_column_sets = get_index_columns(ChatMessage.__table__)
    composite = frozenset({"session_id", "created_at"})
    assert composite in index_column_sets, (
        "Missing composite index on (chat_messages.session_id, chat_messages.created_at) (Req 13.3). "
        f"Found indexes: {index_column_sets}"
    )


# Req 13.4 — index on mood_entries.user_id AND mood_entries.date
def test_mood_entries_user_id_index():
    """Req 13.4: mood_entries.user_id must be indexed for analytics queries."""
    indexed = get_indexed_columns(MoodEntry.__table__)
    assert "user_id" in indexed, "Missing index on mood_entries.user_id (Req 13.4)"


def test_mood_entries_date_index():
    """Req 13.4: mood_entries.date must be indexed for analytics queries."""
    indexed = get_indexed_columns(MoodEntry.__table__)
    assert "date" in indexed, "Missing index on mood_entries.date (Req 13.4)"
