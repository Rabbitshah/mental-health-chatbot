"""
Pytest configuration and fixtures for testing.
"""
import pytest
from sqlalchemy import create_engine, MetaData, event
from sqlalchemy.orm import sessionmaker, Session
from database import Base
from models import User, ChatSession, ChatMessage
import os

# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def test_engine():
    """Create a test database engine."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    
    # Enable foreign key support in SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    # Only create tables that are compatible with SQLite
    # Exclude tables with ARRAY types (CrisisEvent, Notification)
    tables_to_create = [
        Base.metadata.tables['users'],
        Base.metadata.tables['chat_sessions'],
        Base.metadata.tables['chat_messages'],
        Base.metadata.tables['mood_entries'],
        Base.metadata.tables['refresh_tokens'],
    ]
    
    for table in tables_to_create:
        table.create(bind=engine, checkfirst=True)
    
    yield engine
    
    for table in reversed(tables_to_create):
        table.drop(bind=engine, checkfirst=True)
    
    engine.dispose()


@pytest.fixture(scope="function")
def test_db(test_engine):
    """Create a test database session."""
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine
    )
    db = TestingSessionLocal()
    
    try:
        yield db
    finally:
        db.rollback()  # Rollback any uncommitted changes
        db.close()


@pytest.fixture
def sample_user(test_db: Session):
    """Create a sample user for testing."""
    user = User(
        email="test@example.com",
        name="Test User",
        username="testuser",
        password="hashed_password"
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def sample_session(test_db: Session, sample_user: User):
    """Create a sample chat session for testing."""
    session = ChatSession(
        user_id=sample_user.id,
        title="Test Session",
        tag="General"
    )
    test_db.add(session)
    test_db.commit()
    test_db.refresh(session)
    return session
