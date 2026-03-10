import sys
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Add parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import engine

def migrate():
    with engine.connect() as conn:
        print("Checking for created_at column in users table...")
        try:
            # Check if column exists (Postgres specific check)
            result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='users' AND column_name='created_at'"))
            if not result.fetchone():
                print("Adding created_at column to users table...")
                conn.execute(text("ALTER TABLE users ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
                conn.commit()
                print("Migration successful.")
            else:
                print("Column already exists.")
        except Exception as e:
            print(f"Migration failed: {e}")

if __name__ == "__main__":
    migrate()
