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

def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

