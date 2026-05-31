from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base, Session
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL is None:
    raise ValueError("DATABASE_URL is not set in the environment variables")

engine_kwargs = {
    "pool_pre_ping": True,
    "pool_recycle": 1800,
}

if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # Tune pool for production Postgres workloads
    engine_kwargs["pool_size"] = int(os.getenv("DB_POOL_SIZE", "10"))
    engine_kwargs["max_overflow"] = int(os.getenv("DB_MAX_OVERFLOW", "20"))

# Keep pooled DB connections healthy for managed Postgres providers (e.g., Neon)
# that may close idle SSL sessions.
engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base = declarative_base()

def _boolean_default_sql(value: bool) -> str:
    return "TRUE" if value else "FALSE"

def ensure_chat_session_status_columns():
    inspector = inspect(engine)
    existing_columns = {column["name"] for column in inspector.get_columns("chat_sessions")}

    with engine.begin() as connection:
        if "is_pinned" not in existing_columns:
            connection.execute(
                text(
                    f"ALTER TABLE chat_sessions ADD COLUMN is_pinned BOOLEAN NOT NULL DEFAULT {_boolean_default_sql(False)}"
                )
            )
        if "is_archived" not in existing_columns:
            connection.execute(
                text(
                    f"ALTER TABLE chat_sessions ADD COLUMN is_archived BOOLEAN NOT NULL DEFAULT {_boolean_default_sql(False)}"
                )
            )
        if "title_is_auto" not in existing_columns:
            # Default TRUE so existing sessions are treated as auto-titled.
            connection.execute(
                text(
                    f"ALTER TABLE chat_sessions ADD COLUMN title_is_auto BOOLEAN NOT NULL DEFAULT {_boolean_default_sql(True)}"
                )
            )

def ensure_user_preference_columns():
    inspector = inspect(engine)
    existing_columns = {column["name"] for column in inspector.get_columns("users")}

    with engine.begin() as connection:
        if "dark_mode" not in existing_columns:
            connection.execute(
                text(
                    f"ALTER TABLE users ADD COLUMN dark_mode BOOLEAN NOT NULL DEFAULT {_boolean_default_sql(False)}"
                )
            )
        if "email_notifications" not in existing_columns:
            connection.execute(
                text(
                    f"ALTER TABLE users ADD COLUMN email_notifications BOOLEAN NOT NULL DEFAULT {_boolean_default_sql(True)}"
                )
            )
        if "push_notifications" not in existing_columns:
            connection.execute(
                text(
                    f"ALTER TABLE users ADD COLUMN push_notifications BOOLEAN NOT NULL DEFAULT {_boolean_default_sql(True)}"
                )
            )
        if "language" not in existing_columns:
            connection.execute(
                text("ALTER TABLE users ADD COLUMN language VARCHAR NOT NULL DEFAULT 'English'")
            )
        if "notification_frequency" not in existing_columns:
            connection.execute(
                text("ALTER TABLE users ADD COLUMN notification_frequency VARCHAR NOT NULL DEFAULT 'daily'")
            )

def ensure_crisis_event_columns():
    inspector = inspect(engine)
    existing_columns = {column["name"] for column in inspector.get_columns("crisis_events")}

    with engine.begin() as connection:
        if "confidence" not in existing_columns:
            connection.execute(
                text("ALTER TABLE crisis_events ADD COLUMN confidence FLOAT")
            )
        if "detection_method" not in existing_columns:
            connection.execute(
                text("ALTER TABLE crisis_events ADD COLUMN detection_method VARCHAR")
            )

def ensure_refresh_token_index():
    """
    Create the composite index on refresh_tokens(revoked, expires_at) if it does
    not already exist.  This speeds up token-cleanup queries that scan for
    non-revoked or expired rows without going through the unique token column.
    SQLite does not support CREATE INDEX IF NOT EXISTS with the same syntax, so
    we detect the dialect and skip silently for test environments.
    """
    if engine.dialect.name == "sqlite":
        return
    with engine.begin() as connection:
        connection.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_refresh_tokens_revoked_expires_at "
            "ON refresh_tokens (revoked, expires_at)"
        ))

def ensure_wellness_feature_tables():
    from models import JournalEntry, SafetyPlan

    SafetyPlan.__table__.create(bind=engine, checkfirst=True)
    JournalEntry.__table__.create(bind=engine, checkfirst=True)

def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

