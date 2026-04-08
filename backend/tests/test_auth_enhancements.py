"""
Unit tests for authentication enhancements (refresh tokens).
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from jwt_handler import (
    create_access_token,
    create_refresh_token,
    validate_refresh_token,
    revoke_refresh_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS
)
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Create a minimal Base for testing (avoid ARRAY type issues with SQLite)
TestBase = declarative_base()

class TestUser(TestBase):
    """Minimal User model for testing."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String)
    username = Column(String, unique=True, index=True, nullable=True)
    password = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    refresh_tokens = relationship("TestRefreshToken", back_populates="user", cascade="all, delete-orphan")

class TestRefreshToken(TestBase):
    """Minimal RefreshToken model for testing."""
    __tablename__ = "refresh_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token = Column(String, unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    revoked = Column(Boolean, default=False)
    
    user = relationship("TestUser", back_populates="refresh_tokens")

# Test database setup
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    """Create a fresh database for each test."""
    TestBase.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        TestBase.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(db):
    """Create a test user."""
    user = TestUser(
        email="test@example.com",
        name="Test User",
        username="testuser",
        password="hashed_password_placeholder"  # Skip actual hashing for tests
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


class TestAccessToken:
    """Tests for access token functionality."""
    
    def test_create_access_token(self):
        """Test that access tokens are created with correct expiry."""
        token = create_access_token({"email": "test@example.com"})
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_access_token_expiry_is_15_minutes(self):
        """Test that access token expiry is set to 15 minutes."""
        assert ACCESS_TOKEN_EXPIRE_MINUTES == 15


class TestRefreshToken:
    """Tests for refresh token functionality."""
    
    def test_create_refresh_token(self, db, test_user):
        """Test creating a refresh token stores it in database."""
        token = create_refresh_token(test_user.id, db)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Verify it's stored in database
        db_token = db.query(TestRefreshToken).filter(
            TestRefreshToken.token == token
        ).first()
        
        assert db_token is not None
        assert db_token.user_id == test_user.id
        assert db_token.revoked is False
        assert db_token.expires_at > datetime.utcnow()
    
    def test_refresh_token_expiry_is_7_days(self, db, test_user):
        """Test that refresh tokens expire in 7 days."""
        token = create_refresh_token(test_user.id, db)
        
        db_token = db.query(TestRefreshToken).filter(
            TestRefreshToken.token == token
        ).first()
        
        expected_expiry = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        time_diff = abs((db_token.expires_at - expected_expiry).total_seconds())
        
        # Allow 5 seconds tolerance for test execution time
        assert time_diff < 5
        assert REFRESH_TOKEN_EXPIRE_DAYS == 7
    
    def test_validate_refresh_token_success(self, db, test_user):
        """Test validating a valid refresh token returns the user."""
        token = create_refresh_token(test_user.id, db)
        
        user = validate_refresh_token(token, db)
        
        assert user is not None
        assert user.id == test_user.id
        assert user.email == test_user.email
    
    def test_validate_refresh_token_invalid(self, db):
        """Test validating an invalid token raises ValueError."""
        with pytest.raises(ValueError, match="Invalid refresh token"):
            validate_refresh_token("invalid_token_12345", db)
    
    def test_validate_refresh_token_revoked(self, db, test_user):
        """Test validating a revoked token raises ValueError."""
        token = create_refresh_token(test_user.id, db)
        
        # Revoke the token
        revoke_refresh_token(token, db)
        
        # Try to validate it
        with pytest.raises(ValueError, match="Refresh token has been revoked"):
            validate_refresh_token(token, db)
    
    def test_validate_refresh_token_expired(self, db, test_user):
        """Test validating an expired token raises ValueError."""
        token = create_refresh_token(test_user.id, db)
        
        # Manually expire the token
        db_token = db.query(TestRefreshToken).filter(
            TestRefreshToken.token == token
        ).first()
        db_token.expires_at = datetime.utcnow() - timedelta(days=1)
        db.commit()
        
        # Try to validate it
        with pytest.raises(ValueError, match="Refresh token has expired"):
            validate_refresh_token(token, db)
    
    def test_revoke_refresh_token(self, db, test_user):
        """Test revoking a refresh token marks it as revoked."""
        token = create_refresh_token(test_user.id, db)
        
        # Revoke the token
        revoke_refresh_token(token, db)
        
        # Verify it's marked as revoked
        db_token = db.query(TestRefreshToken).filter(
            TestRefreshToken.token == token
        ).first()
        
        assert db_token.revoked is True
    
    def test_revoke_nonexistent_token(self, db):
        """Test revoking a non-existent token raises ValueError."""
        with pytest.raises(ValueError, match="Refresh token not found"):
            revoke_refresh_token("nonexistent_token", db)
    
    def test_multiple_refresh_tokens_per_user(self, db, test_user):
        """Test that a user can have multiple refresh tokens."""
        token1 = create_refresh_token(test_user.id, db)
        token2 = create_refresh_token(test_user.id, db)
        
        assert token1 != token2
        
        # Both should be valid
        user1 = validate_refresh_token(token1, db)
        user2 = validate_refresh_token(token2, db)
        
        assert user1.id == test_user.id
        assert user2.id == test_user.id
        
        # Revoking one shouldn't affect the other
        revoke_refresh_token(token1, db)
        
        with pytest.raises(ValueError):
            validate_refresh_token(token1, db)
        
        # token2 should still be valid
        user2 = validate_refresh_token(token2, db)
        assert user2.id == test_user.id

