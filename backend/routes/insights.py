from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta

from database import get_db
from models import MoodEntry, User
from dependencies import get_current_user

router = APIRouter(prefix="/insights")

class MoodRequest(BaseModel):
    mood_score: float
    energy_level: float
    stress_level: float

class MoodResponse(BaseModel):
    id: int
    mood_score: float
    energy_level: float
    stress_level: float
    date: datetime

    class Config:
        from_attributes = True

@router.post("/mood", response_model=MoodResponse)
def add_mood_entry(request: MoodRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_entry = MoodEntry(
        user_id=current_user.id,
        mood_score=request.mood_score,
        energy_level=request.energy_level,
        stress_level=request.stress_level
    )
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)
    return new_entry

@router.get("/mood", response_model=List[MoodResponse])
def get_mood_trend(days: int = 7, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    entries = db.query(MoodEntry).filter(
        MoodEntry.user_id == current_user.id,
        MoodEntry.date >= cutoff_date
    ).order_by(MoodEntry.date.asc()).all()
    return entries

@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Calculates a few simple aggregated statistics for the dashboard
    from models import ChatSession
    total_sessions = db.query(ChatSession).filter(ChatSession.user_id == current_user.id).count()
    
    # Check if there are any mood entries
    recent_entry = db.query(MoodEntry).filter(MoodEntry.user_id == current_user.id).order_by(MoodEntry.date.desc()).first()
    mood_score = recent_entry.mood_score * 10 if recent_entry else 0

    # Calculate real day streak
    streak = 0
    all_moods = db.query(MoodEntry).filter(MoodEntry.user_id == current_user.id).order_by(MoodEntry.date.desc()).all()
    if all_moods:
        # Normalize today's date
        current_date = datetime.utcnow().date()
        # Check if the most recent entry is from today or yesterday
        last_entry_date = all_moods[0].date.date()
        
        if last_entry_date == current_date or last_entry_date == current_date - timedelta(days=1):
            streak = 1
            for i in range(len(all_moods) - 1):
                diff = all_moods[i].date.date() - all_moods[i+1].date.date()
                if diff.days == 1:
                    streak += 1
                elif diff.days == 0:
                    continue # Multiple entries in one day
                else:
                    break
    
    return {
        "total_sessions": total_sessions,
        "mood_score_percent": round(mood_score, 1),
        "journals": total_sessions, # Using sessions as a proxy for journal activity
        "day_streak": streak
    }
