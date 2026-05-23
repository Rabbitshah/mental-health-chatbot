import sys
import os
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv

# Add parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import engine

def column_exists(conn, table_name, column_name):
    """Check if a column exists in a table"""
    result = conn.execute(text(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name=:table AND column_name=:column"
    ), {"table": table_name, "column": column_name})
    return result.fetchone() is not None

def table_exists(conn, table_name):
    """Check if a table exists"""
    result = conn.execute(text(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_name=:table"
    ), {"table": table_name})
    return result.fetchone() is not None

def index_exists(conn, index_name):
    """Check if an index exists"""
    result = conn.execute(text(
        "SELECT indexname FROM pg_indexes "
        "WHERE indexname=:index"
    ), {"index": index_name})
    return result.fetchone() is not None

def migrate():
    print("Starting database migration for mental health chatbot enhancements...")
    
    with engine.connect() as conn:
        # Start a transaction
        trans = conn.begin()
        
        try:
            # 1. Add summary column to chat_sessions table
            print("\n1. Checking chat_sessions.summary column...")
            if not column_exists(conn, 'chat_sessions', 'summary'):
                print("   Adding summary column to chat_sessions table...")
                conn.execute(text("ALTER TABLE chat_sessions ADD COLUMN summary TEXT"))
                print("    Added summary column")
            else:
                print("    Summary column already exists")
            
            # 2. Ensure tag column exists and has default value
            print("\n2. Checking chat_sessions.tag column...")
            if not column_exists(conn, 'chat_sessions', 'tag'):
                print("   Adding tag column to chat_sessions table...")
                conn.execute(text("ALTER TABLE chat_sessions ADD COLUMN tag VARCHAR DEFAULT 'General'"))
                print("    Added tag column")
            else:
                print("    Tag column already exists")
            
            # 3. Create refresh_tokens table
            print("\n3. Checking refresh_tokens table...")
            if not table_exists(conn, 'refresh_tokens'):
                print("   Creating refresh_tokens table...")
                conn.execute(text("""
                    CREATE TABLE refresh_tokens (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        token VARCHAR(500) UNIQUE NOT NULL,
                        expires_at TIMESTAMP NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        revoked BOOLEAN DEFAULT FALSE
                    )
                """))
                print("    Created refresh_tokens table")
            else:
                print("    refresh_tokens table already exists")
            
            # 4. Create crisis_events table
            print("\n4. Checking crisis_events table...")
            if not table_exists(conn, 'crisis_events'):
                print("   Creating crisis_events table...")
                conn.execute(text("""
                    CREATE TABLE crisis_events (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        message_id INTEGER REFERENCES chat_messages(id) ON DELETE SET NULL,
                        keywords TEXT[],
                        confidence FLOAT,
                        detection_method VARCHAR,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                print("    Created crisis_events table")
            else:
                print("    crisis_events table already exists")
                # Add columns if they don't exist
                if not column_exists(conn, 'crisis_events', 'confidence'):
                    print("   Adding confidence column to crisis_events...")
                    conn.execute(text("ALTER TABLE crisis_events ADD COLUMN confidence FLOAT"))
                if not column_exists(conn, 'crisis_events', 'detection_method'):
                    print("   Adding detection_method column to crisis_events...")
                    conn.execute(text("ALTER TABLE crisis_events ADD COLUMN detection_method VARCHAR"))
            
            # 5. Create notifications table
            print("\n5. Checking notifications table...")
            if not table_exists(conn, 'notifications'):
                print("   Creating notifications table...")
                conn.execute(text("""
                    CREATE TABLE notifications (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        type VARCHAR(50) NOT NULL,
                        message TEXT NOT NULL,
                        read BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                print("    Created notifications table")
            else:
                print("    notifications table already exists")
            
            # 6. Create indexes for performance optimization
            print("\n6. Creating database indexes...")
            
            # Index on users.email (should already exist, but verify)
            if not index_exists(conn, 'ix_users_email'):
                print("   Creating index on users.email...")
                conn.execute(text("CREATE INDEX ix_users_email ON users(email)"))
                print("    Created index on users.email")
            else:
                print("    Index on users.email already exists")
            
            # Index on chat_sessions.user_id
            if not index_exists(conn, 'ix_chat_sessions_user_id'):
                print("   Creating index on chat_sessions.user_id...")
                conn.execute(text("CREATE INDEX ix_chat_sessions_user_id ON chat_sessions(user_id)"))
                print("    Created index on chat_sessions.user_id")
            else:
                print("    Index on chat_sessions.user_id already exists")
            
            # Index on chat_sessions.tag
            if not index_exists(conn, 'ix_chat_sessions_tag'):
                print("   Creating index on chat_sessions.tag...")
                conn.execute(text("CREATE INDEX ix_chat_sessions_tag ON chat_sessions(tag)"))
                print("    Created index on chat_sessions.tag")
            else:
                print("    Index on chat_sessions.tag already exists")
            
            # Index on chat_sessions.updated_at
            if not index_exists(conn, 'ix_chat_sessions_updated_at'):
                print("   Creating index on chat_sessions.updated_at...")
                conn.execute(text("CREATE INDEX ix_chat_sessions_updated_at ON chat_sessions(updated_at)"))
                print("    Created index on chat_sessions.updated_at")
            else:
                print("    Index on chat_sessions.updated_at already exists")
            
            # Composite index on chat_messages (session_id, created_at)
            if not index_exists(conn, 'ix_chat_messages_session_created'):
                print("   Creating composite index on chat_messages(session_id, created_at)...")
                conn.execute(text("CREATE INDEX ix_chat_messages_session_created ON chat_messages(session_id, created_at)"))
                print("    Created composite index on chat_messages")
            else:
                print("    Composite index on chat_messages already exists")
            
            # Index on chat_messages.session_id
            if not index_exists(conn, 'ix_chat_messages_session_id'):
                print("   Creating index on chat_messages.session_id...")
                conn.execute(text("CREATE INDEX ix_chat_messages_session_id ON chat_messages(session_id)"))
                print("    Created index on chat_messages.session_id")
            else:
                print("    Index on chat_messages.session_id already exists")
            
            # Index on chat_messages.created_at
            if not index_exists(conn, 'ix_chat_messages_created_at'):
                print("   Creating index on chat_messages.created_at...")
                conn.execute(text("CREATE INDEX ix_chat_messages_created_at ON chat_messages(created_at)"))
                print("    Created index on chat_messages.created_at")
            else:
                print("    Index on chat_messages.created_at already exists")
            
            # Index on mood_entries.user_id
            if not index_exists(conn, 'ix_mood_entries_user_id'):
                print("   Creating index on mood_entries.user_id...")
                conn.execute(text("CREATE INDEX ix_mood_entries_user_id ON mood_entries(user_id)"))
                print("    Created index on mood_entries.user_id")
            else:
                print("    Index on mood_entries.user_id already exists")
            
            # Index on mood_entries.date
            if not index_exists(conn, 'ix_mood_entries_date'):
                print("   Creating index on mood_entries.date...")
                conn.execute(text("CREATE INDEX ix_mood_entries_date ON mood_entries(date)"))
                print("    Created index on mood_entries.date")
            else:
                print("    Index on mood_entries.date already exists")
            
            # Index on refresh_tokens.token
            if not index_exists(conn, 'ix_refresh_tokens_token'):
                print("   Creating index on refresh_tokens.token...")
                conn.execute(text("CREATE INDEX ix_refresh_tokens_token ON refresh_tokens(token)"))
                print("    Created index on refresh_tokens.token")
            else:
                print("    Index on refresh_tokens.token already exists")
            
            # Index on refresh_tokens.user_id
            if not index_exists(conn, 'ix_refresh_tokens_user_id'):
                print("   Creating index on refresh_tokens.user_id...")
                conn.execute(text("CREATE INDEX ix_refresh_tokens_user_id ON refresh_tokens(user_id)"))
                print("    Created index on refresh_tokens.user_id")
            else:
                print("    Index on refresh_tokens.user_id already exists")
            
            # Index on crisis_events.user_id
            if not index_exists(conn, 'ix_crisis_events_user_id'):
                print("   Creating index on crisis_events.user_id...")
                conn.execute(text("CREATE INDEX ix_crisis_events_user_id ON crisis_events(user_id)"))
                print("    Created index on crisis_events.user_id")
            else:
                print("    Index on crisis_events.user_id already exists")
            
            # Index on crisis_events.created_at
            if not index_exists(conn, 'ix_crisis_events_created_at'):
                print("   Creating index on crisis_events.created_at...")
                conn.execute(text("CREATE INDEX ix_crisis_events_created_at ON crisis_events(created_at)"))
                print("    Created index on crisis_events.created_at")
            else:
                print("    Index on crisis_events.created_at already exists")
            
            # Index on notifications.user_id
            if not index_exists(conn, 'ix_notifications_user_id'):
                print("   Creating index on notifications.user_id...")
                conn.execute(text("CREATE INDEX ix_notifications_user_id ON notifications(user_id)"))
                print("    Created index on notifications.user_id")
            else:
                print("    Index on notifications.user_id already exists")
            
            # Index on notifications.read
            if not index_exists(conn, 'ix_notifications_read'):
                print("   Creating index on notifications.read...")
                conn.execute(text("CREATE INDEX ix_notifications_read ON notifications(read)"))
                print("    Created index on notifications.read")
            else:
                print("    Index on notifications.read already exists")
            
            # Index on notifications.created_at
            if not index_exists(conn, 'ix_notifications_created_at'):
                print("   Creating index on notifications.created_at...")
                conn.execute(text("CREATE INDEX ix_notifications_created_at ON notifications(created_at)"))
                print("    Created index on notifications.created_at")
            else:
                print("    Index on notifications.created_at already exists")
            
            # Commit the transaction
            trans.commit()
            print("\n Migration completed successfully!")
            
        except Exception as e:
            trans.rollback()
            print(f"\n Migration failed: {e}")
            raise

if __name__ == "__main__":
    migrate()
