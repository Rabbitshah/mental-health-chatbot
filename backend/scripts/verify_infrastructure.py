import sys
import os
from sqlalchemy import text, inspect

# Add parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import engine
from redis_client import get_redis_client

def verify_database():
    """Verify database tables and columns exist"""
    print("\n=== Database Verification ===")
    
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    required_tables = [
        'users', 'chat_sessions', 'chat_messages', 'mood_entries',
        'refresh_tokens', 'crisis_events', 'notifications'
    ]
    
    print("\nChecking tables:")
    for table in required_tables:
        if table in tables:
            print(f"  ✓ {table}")
        else:
            print(f"  ✗ {table} - MISSING")
    
    # Check specific columns
    print("\nChecking new columns:")
    
    # Check chat_sessions.summary
    chat_session_columns = [col['name'] for col in inspector.get_columns('chat_sessions')]
    if 'summary' in chat_session_columns:
        print("  ✓ chat_sessions.summary")
    else:
        print("  ✗ chat_sessions.summary - MISSING")
    
    if 'tag' in chat_session_columns:
        print("  ✓ chat_sessions.tag")
    else:
        print("  ✗ chat_sessions.tag - MISSING")
    
    # Check indexes
    print("\nChecking key indexes:")
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT indexname FROM pg_indexes WHERE tablename IN "
            "('chat_sessions', 'chat_messages', 'mood_entries', 'refresh_tokens', 'crisis_events', 'notifications')"
        ))
        indexes = [row[0] for row in result]
        
        key_indexes = [
            'ix_chat_sessions_user_id',
            'ix_chat_sessions_tag',
            'ix_chat_messages_session_created',
            'ix_mood_entries_user_id',
            'ix_refresh_tokens_token',
            'ix_crisis_events_user_id',
            'ix_notifications_user_id'
        ]
        
        for idx in key_indexes:
            if idx in indexes:
                print(f"  ✓ {idx}")
            else:
                print(f"  ✗ {idx} - MISSING")

def verify_redis():
    """Verify Redis connection"""
    print("\n=== Redis Verification ===")
    
    client = get_redis_client()
    if client:
        try:
            client.ping()
            print("  ✓ Redis connection successful")
            
            # Test basic operations
            client.set("test_key", "test_value", ex=10)
            value = client.get("test_key")
            if value == "test_value":
                print("  ✓ Redis read/write operations working")
            client.delete("test_key")
        except Exception as e:
            print(f"  ✗ Redis operations failed: {e}")
    else:
        print("  ⚠ Redis not available (graceful degradation enabled)")

def verify_models():
    """Verify all models can be imported"""
    print("\n=== Models Verification ===")
    
    try:
        from models import User, ChatSession, ChatMessage, MoodEntry, RefreshToken, CrisisEvent, Notification
        print("  ✓ All models imported successfully")
        
        # Check relationships
        print("\nChecking model relationships:")
        print(f"  ✓ User has {len(User.__mapper__.relationships)} relationships")
        print(f"  ✓ ChatSession has {len(ChatSession.__mapper__.relationships)} relationships")
        print(f"  ✓ RefreshToken model exists")
        print(f"  ✓ CrisisEvent model exists")
        print(f"  ✓ Notification model exists")
    except Exception as e:
        print(f"  ✗ Model import failed: {e}")

def main():
    print("=" * 50)
    print("Infrastructure Verification Script")
    print("=" * 50)
    
    try:
        verify_database()
        verify_redis()
        verify_models()
        
        print("\n" + "=" * 50)
        print("✅ Infrastructure verification complete!")
        print("=" * 50)
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
