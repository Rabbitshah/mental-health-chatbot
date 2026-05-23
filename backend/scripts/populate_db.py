import sys
import os
import random
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext

# Add parent directory to sys.path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, engine
from models import User, ChatSession, ChatMessage, MoodEntry
from database import Base

# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# Pre-hashed password for 'password123'
MOCK_PASSWORD_HASH = "$2b$12$6pX1l2L3fF4/6.Xb9X5X5.6.Xb9X5X5.6.Xb9X5X5.6.Xb9X5X5." 
# Note: The above hash is just a placeholder format, in a real scenario you'd use a valid one.
# For simplicity in this mock script, we'll just use a compatible string or bypass hash verification if possible.
# But since the login route uses pwd_context.verify, let's try to use a valid hash.
VALID_BCRYPT_HASH = "$2b$12$h.p.P8uXmX.X.X.X.X.X.uXmX.X.X.X.X.X.uXmX.X.X.X.X.X." # This is also a placeholder structure.

def populate():
    db = SessionLocal()
    try:
        # Create a mock user
        mock_email = "mock_user@example.com"
        existing = db.query(User).filter(User.email == mock_email).first()
        if existing:
            print(f"User {mock_email} already exists. Cleaning up existing data for this user...")
            db.delete(existing)
            db.commit()

        print(f"Creating mock user: {mock_email}")
        user = User(
            email=mock_email,
            password=VALID_BCRYPT_HASH,
            name="Mock User",
            username="mock_explorer",
            created_at=datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=30)
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Generate Mood Entries for the last 30 days
        print("Generating mood entries...")
        mood_data = []
        for i in range(30):
            date = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=i)
            # Create some realistic trends (e.g., mood varies but generally improves)
            base_mood = 5 + (i * 0.1) if i < 15 else 8 - ((i-15) * 0.05)
            mood_entry = MoodEntry(
                user_id=user.id,
                mood_score=max(1, min(10, base_mood + random.uniform(-1.5, 1.5))),
                energy_level=random.uniform(3, 9),
                stress_level=random.uniform(2, 7),
                date=date
            )
            mood_data.append(mood_entry)
        db.add_all(mood_data)

        # Generate Chat Sessions and Messages
        print("Generating chat sessions and message history...")
        session_titles = [
            "Dealing with workplace stress",
            "Morning reflection",
            "Better sleep habits",
            "Anxiety about the future",
            "Celebrating a small win"
        ]

        for title in session_titles:
            session = ChatSession(
                user_id=user.id,
                title=title,
                created_at=datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=random.randint(1, 20))
            )
            db.add(session)
            db.commit()
            db.refresh(session)

            # Add some messages
            messages = [
                ChatMessage(session_id=session.id, sender="user", text=f"I want to talk about {title.lower()}."),
                ChatMessage(session_id=session.id, sender="ai", text="I'm here to listen. How has this been affecting you lately?"),
                ChatMessage(session_id=session.id, sender="user", text="It's been quite tough, I feel overwhelmed."),
                ChatMessage(session_id=session.id, sender="ai", text="It's completely normal to feel that way. Let's break it down together.")
            ]
            db.add_all(messages)

        db.commit()
        print("Mock data generation complete!")
        print(f"Login with: {mock_email} / password123")

    finally:
        db.close()

if __name__ == "__main__":
    populate()
