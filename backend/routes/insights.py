from collections import Counter

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timedelta, timezone
import json
import logging

from database import get_db
from models import MoodEntry, User, ChatSession, ChatMessage
from dependencies import get_current_user
from limiter import limiter
from redis_client import cache_get, cache_set, cache_delete_pattern, CacheKeys, CacheTTL

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/insights")

def average(values):
    return sum(values) / len(values) if values else 0

def calculate_streaks(moods: list[MoodEntry]) -> tuple[int, int]:
    if not moods:
        return 0, 0

    unique_dates = sorted({mood.date.date() for mood in moods}, reverse=True)
    longest_streak = 1
    current_streak = 0

    today = datetime.now(timezone.utc).date()
    if unique_dates and (unique_dates[0] == today or unique_dates[0] == today - timedelta(days=1)):
        current_streak = 1
        for i in range(len(unique_dates) - 1):
            diff = unique_dates[i] - unique_dates[i + 1]
            if diff.days == 1:
                current_streak += 1
            else:
                break

    running_streak = 1
    for i in range(len(unique_dates) - 1):
        diff = unique_dates[i] - unique_dates[i + 1]
        if diff.days == 1:
            running_streak += 1
            longest_streak = max(longest_streak, running_streak)
        else:
            running_streak = 1

    return current_streak, longest_streak

def pearson_correlation(values_a: list[float], values_b: list[float]) -> float:
    if len(values_a) != len(values_b) or len(values_a) < 2:
        return 0.0

    mean_a = average(values_a)
    mean_b = average(values_b)

    numerator = sum((a - mean_a) * (b - mean_b) for a, b in zip(values_a, values_b))
    denominator_a = sum((a - mean_a) ** 2 for a in values_a) ** 0.5
    denominator_b = sum((b - mean_b) ** 2 for b in values_b) ** 0.5

    if denominator_a == 0 or denominator_b == 0:
        return 0.0

    return numerator / (denominator_a * denominator_b)

class MoodRequest(BaseModel):
    mood_score: float = Field(..., ge=1, le=10)
    energy_level: float = Field(..., ge=1, le=10)
    stress_level: float = Field(..., ge=1, le=10)

class MoodResponse(BaseModel):
    id: int
    mood_score: float
    energy_level: float
    stress_level: float
    date: datetime

    model_config = {"from_attributes": True}

@router.post("/mood", response_model=MoodResponse)
@limiter.limit("20/minute")
def add_mood_entry(request: Request, mood_request: MoodRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_entry = MoodEntry(
        user_id=current_user.id,
        mood_score=mood_request.mood_score,
        energy_level=mood_request.energy_level,
        stress_level=mood_request.stress_level
    )
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)

    try:
        pattern = CacheKeys.MOOD_ANALYTICS.format(user_id=current_user.id, days="*")
        cache_delete_pattern(pattern)
    except Exception as e:
        logger.warning(f"Cache invalidation failed for mood analytics (user {current_user.id}): {e}")

    return new_entry

@router.get("/mood", response_model=List[MoodResponse])
def get_mood_trend(days: int = Query(default=7, ge=1, le=365), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    cache_key = CacheKeys.MOOD_ANALYTICS.format(user_id=current_user.id, days=days)
    try:
        cached = cache_get(cache_key)
        if cached:
            return json.loads(cached)
    except Exception as e:
        logger.warning(f"Cache GET failed for mood analytics (user {current_user.id}, days={days}): {e}")

    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
    entries = db.query(MoodEntry).filter(
        MoodEntry.user_id == current_user.id,
        MoodEntry.date >= cutoff_date
    ).order_by(MoodEntry.date.asc()).all()

    result = [
        {
            "id": e.id,
            "mood_score": e.mood_score,
            "energy_level": e.energy_level,
            "stress_level": e.stress_level,
            "date": e.date.isoformat(),
        }
        for e in entries
    ]

    try:
        cache_set(cache_key, json.dumps(result), CacheTTL.MOOD_ANALYTICS)
    except Exception as e:
        logger.warning(f"Cache SET failed for mood analytics (user {current_user.id}, days={days}): {e}")

    return result

@router.delete("/mood/{mood_id}")
def delete_mood_entry(
    mood_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = db.query(MoodEntry).filter(
        MoodEntry.id == mood_id,
        MoodEntry.user_id == current_user.id,
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Mood entry not found")

    db.delete(entry)
    db.commit()
    try:
        pattern = CacheKeys.MOOD_ANALYTICS.format(user_id=current_user.id, days="*")
        cache_delete_pattern(pattern)
    except Exception as e:
        logger.warning(f"Cache invalidation failed after mood delete (user {current_user.id}): {e}")
    return {"message": "Mood entry deleted"}

@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Calculates a few simple aggregated statistics for the dashboard
    from models import ChatSession
    total_sessions = db.query(ChatSession).filter(ChatSession.user_id == current_user.id).count()
    
    # Check if there are any mood entries
    recent_entry = db.query(MoodEntry).filter(MoodEntry.user_id == current_user.id).order_by(MoodEntry.date.desc()).first()
    mood_score = recent_entry.mood_score * 10 if recent_entry else 0

    # Calculate real day streak
    all_moods = db.query(MoodEntry).filter(MoodEntry.user_id == current_user.id).order_by(MoodEntry.date.desc()).all()
    streak, _ = calculate_streaks(all_moods)
    
    return {
        "total_sessions": total_sessions,
        "mood_score_percent": round(mood_score, 1),
        "journals": total_sessions, # Using sessions as a proxy for journal activity
        "day_streak": streak
    }

_ANALYTICS_MAX_DAYS = 730  # 2-year cap — prevents full-table scans

@router.get("/analytics")
def get_mood_analytics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    now = datetime.now(timezone.utc)
    if start_date is None:
        start_date = now - timedelta(days=30)
    if end_date is None:
        end_date = now

    # Cap date range to prevent full-table scans
    if (end_date - start_date).days > _ANALYTICS_MAX_DAYS:
        start_date = end_date - timedelta(days=_ANALYTICS_MAX_DAYS)

    cache_key = f"user:{current_user.id}:mood:analytics:{start_date.isoformat()}:{end_date.isoformat()}"
    try:
        cached = cache_get(cache_key)
        if cached:
            return json.loads(cached)
    except Exception as e:
        logger.warning(f"Cache GET failed for mood analytics (user {current_user.id}): {e}")

    entries = db.query(MoodEntry).filter(
        MoodEntry.user_id == current_user.id,
        MoodEntry.date >= start_date,
        MoodEntry.date <= end_date,
    ).order_by(MoodEntry.date.asc()).all()

    if not entries:
        result = {
            "avg_mood": 0.0,
            "avg_energy": 0.0,
            "avg_stress": 0.0,
            "min_mood": 0.0,
            "max_mood": 0.0,
            "min_energy": 0.0,
            "max_energy": 0.0,
            "min_stress": 0.0,
            "max_stress": 0.0,
            "trend": "stable",
            "weekly_averages": [],
        }
        return result

    moods = [e.mood_score for e in entries]
    energies = [e.energy_level for e in entries]
    stresses = [e.stress_level for e in entries]

    # Trend: compare first half vs second half by avg mood
    mid = len(entries) // 2
    first_half_avg = average(moods[:mid]) if mid > 0 else average(moods)
    second_half_avg = average(moods[mid:]) if mid < len(moods) else average(moods)
    diff = second_half_avg - first_half_avg
    if diff > 0.5:
        trend = "improving"
    elif diff < -0.5:
        trend = "declining"
    else:
        trend = "stable"

    # Weekly averages grouped by ISO year-week
    week_buckets: dict[str, dict[str, list[float]]] = {}
    for e in entries:
        iso_year, iso_week, _ = e.date.isocalendar()
        week_key = f"{iso_year}-W{iso_week:02d}"
        bucket = week_buckets.setdefault(week_key, {"mood": [], "energy": [], "stress": []})
        bucket["mood"].append(e.mood_score)
        bucket["energy"].append(e.energy_level)
        bucket["stress"].append(e.stress_level)

    weekly_averages = [
        {
            "week": week,
            "avg_mood": round(average(data["mood"]), 2),
            "avg_energy": round(average(data["energy"]), 2),
            "avg_stress": round(average(data["stress"]), 2),
        }
        for week, data in sorted(week_buckets.items())
    ]

    result = {
        "avg_mood": round(average(moods), 2),
        "avg_energy": round(average(energies), 2),
        "avg_stress": round(average(stresses), 2),
        "min_mood": min(moods),
        "max_mood": max(moods),
        "min_energy": min(energies),
        "max_energy": max(energies),
        "min_stress": min(stresses),
        "max_stress": max(stresses),
        "trend": trend,
        "weekly_averages": weekly_averages,
    }

    try:
        cache_set(cache_key, json.dumps(result), CacheTTL.MOOD_ANALYTICS)
    except Exception as e:
        logger.warning(f"Cache SET failed for mood analytics (user {current_user.id}): {e}")

    return result


@router.get("/recommendations")
def get_recommendations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    recent_moods = db.query(MoodEntry).filter(
        MoodEntry.user_id == current_user.id
    ).order_by(MoodEntry.date.desc()).limit(7).all()
    recent_sessions = db.query(ChatSession).filter(
        ChatSession.user_id == current_user.id,
        ChatSession.is_archived == False,
    ).order_by(ChatSession.updated_at.desc()).limit(10).all()

    avg_stress = average([entry.stress_level for entry in recent_moods])
    avg_energy = average([entry.energy_level for entry in recent_moods])
    avg_mood = average([entry.mood_score for entry in recent_moods])
    tags = Counter(session.tag or "General" for session in recent_sessions)
    top_tag = tags.most_common(1)[0][0] if tags else "General"

    if avg_stress >= 7:
        featured = {
            "category": "Grounding",
            "title": "3-Minute Nervous System Reset",
            "description": "A short breathing and sensory exercise for high-stress moments.",
        }
    elif avg_energy and avg_energy <= 4:
        featured = {
            "category": "Recovery",
            "title": "Low-Energy Reset Plan",
            "description": "Pick one gentle task, one hydration break, and one rest cue.",
        }
    elif avg_mood and avg_mood <= 4:
        featured = {
            "category": "Support",
            "title": "Reach-Out Script",
            "description": "A simple way to tell someone you trust that today feels hard.",
        }
    elif top_tag == "Sleep":
        featured = {
            "category": "Sleep",
            "title": "Wind-Down Routine",
            "description": "A calmer 20-minute transition for nights when your mind stays busy.",
        }
    elif top_tag == "Relationships":
        featured = {
            "category": "Reflection",
            "title": "Boundary Check-In",
            "description": "Clarify what you feel, what you need, and what is yours to carry.",
        }
    else:
        featured = {
            "category": "Meditation",
            "title": "5-Minute Breathing Reset",
            "description": "Quick guided breathing practice for moments of stress or mental overload.",
        }

    return {
        "featured": featured,
        "items": [
            {
                "type": "exercise",
                "title": f"{top_tag} Reflection Prompt" if top_tag != "General" else "Daily Reflection Prompt",
                "meta": "2 min practice",
            },
            {
                "type": "journal",
                "title": "Capture One Thought Pattern",
                "meta": "Structured journal",
            },
            {
                "type": "safety",
                "title": "Review Your Safety Plan",
                "meta": "Private checklist",
            },
        ],
    }

@router.get("/summary")
def get_insights_summary(
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entries = db.query(MoodEntry).filter(
        MoodEntry.user_id == current_user.id
    ).order_by(MoodEntry.date.asc()).all()

    if not entries:
        return {
            "insights": [
                {
                    "title": "No Mood Data Yet",
                    "description": "Start completing daily check-ins to unlock personalized wellness insights.",
                    "percentage": "0%",
                    "direction": "neutral",
                    "metric": "mood",
                },
                {
                    "title": "Energy Trends Unavailable",
                    "description": "We need a few check-ins before we can identify your energy patterns.",
                    "percentage": "0%",
                    "direction": "neutral",
                    "metric": "energy",
                },
                {
                    "title": "Stress Trends Unavailable",
                    "description": "Track stress for a few days and this card will begin showing real changes.",
                    "percentage": "0%",
                    "direction": "neutral",
                    "metric": "stress",
                },
                {
                    "title": "Consistency Building",
                    "description": "Keep checking in regularly so we can identify meaningful patterns over time.",
                    "percentage": "0%",
                    "direction": "neutral",
                    "metric": "consistency",
                },
            ]
        }

    recent_entries = entries[-days:]
    previous_entries = entries[-(days * 2):-days] if len(entries) > days else []

    avg_recent_mood = average([entry.mood_score for entry in recent_entries])
    avg_recent_energy = average([entry.energy_level for entry in recent_entries])
    avg_recent_stress = average([entry.stress_level for entry in recent_entries])

    avg_previous_mood = average([entry.mood_score for entry in previous_entries])
    avg_previous_energy = average([entry.energy_level for entry in previous_entries])
    avg_previous_stress = average([entry.stress_level for entry in previous_entries])

    def percent_change(current, previous):
        if previous == 0:
            return 0
        return round(((current - previous) / previous) * 100)

    mood_change = percent_change(avg_recent_mood, avg_previous_mood)
    energy_change = percent_change(avg_recent_energy, avg_previous_energy)
    stress_change = percent_change(avg_recent_stress, avg_previous_stress)

    def signed_percentage(value):
        return f"{value:+d}%"

    unique_recent_days = len({entry.date.date().isoformat() for entry in recent_entries})
    consistency_percent = round((unique_recent_days / max(days, 1)) * 100)

    mood_description = (
        "Your average mood is improving compared with the previous period."
        if mood_change > 0
        else "Your average mood is lower than the previous period. A gentle check-in may help spot what changed."
        if mood_change < 0
        else "Your average mood has remained steady over the recent period."
    )

    energy_description = (
        "Your energy levels are trending upward recently."
        if energy_change > 0
        else "Your energy levels have dipped recently. Rest and recovery habits may be worth revisiting."
        if energy_change < 0
        else "Your energy levels have stayed fairly consistent lately."
    )

    stress_description = (
        "Your stress levels have come down compared with the previous period."
        if stress_change < 0
        else "Your stress levels have increased recently. It may help to add a short reset or grounding routine."
        if stress_change > 0
        else "Your stress levels have been relatively stable over the recent period."
    )

    consistency_description = (
        f"You completed check-ins on {unique_recent_days} of the last {days} days."
        if unique_recent_days
        else "You have not completed any recent check-ins yet."
    )

    return {
        "insights": [
            {
                "title": "Mood Trend",
                "description": mood_description,
                "percentage": signed_percentage(mood_change),
                "direction": "up" if mood_change > 0 else "down" if mood_change < 0 else "neutral",
                "metric": "mood",
            },
            {
                "title": "Energy Levels",
                "description": energy_description,
                "percentage": signed_percentage(energy_change),
                "direction": "up" if energy_change > 0 else "down" if energy_change < 0 else "neutral",
                "metric": "energy",
            },
            {
                "title": "Stress Levels",
                "description": stress_description,
                "percentage": signed_percentage(-stress_change if stress_change < 0 else stress_change),
                "direction": "up" if stress_change < 0 else "down" if stress_change > 0 else "neutral",
                "metric": "stress",
            },
            {
                "title": "Check-in Consistency",
                "description": consistency_description,
                "percentage": f"{consistency_percent}%",
                "direction": "up" if consistency_percent >= 60 else "neutral",
                "metric": "consistency",
            },
        ]
    }

@router.get("/topics")
def get_top_topics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sessions = db.query(ChatSession).filter(
        ChatSession.user_id == current_user.id
    ).all()

    topic_keywords = {
        "Anxiety": ["anxiety", "anxious", "panic", "worry", "worried", "nervous"],
        "Stress": ["stress", "stressed", "overwhelmed", "pressure", "burnout"],
        "Sleep": ["sleep", "insomnia", "tired", "rest", "restless"],
        "Work": ["work", "job", "office", "manager", "career", "deadline"],
        "Relationships": ["relationship", "partner", "friend", "family", "parents", "breakup"],
        "Mood": ["sad", "down", "lonely", "happy", "mood", "emotion"],
        "Self-Esteem": ["confidence", "self-esteem", "insecure", "worth", "myself"],
        "Goals": ["goal", "habit", "routine", "discipline", "focus", "motivation"],
    }

    topic_counts = Counter()

    if sessions:
        session_ids = [s.id for s in sessions]
        # Single query for all messages across all sessions (eliminates N+1)
        all_messages = (
            db.query(ChatMessage.session_id, ChatMessage.text)
            .filter(ChatMessage.session_id.in_(session_ids))
            .all()
        )
        # Group message texts by session
        from collections import defaultdict
        texts_by_session = defaultdict(list)
        for msg in all_messages:
            texts_by_session[msg.session_id].append(msg.text)

        for session in sessions:
            text_parts = [session.title or ""] + texts_by_session.get(session.id, [])
            combined_text = " ".join(text_parts).lower()
            for topic, keywords in topic_keywords.items():
                if any(keyword in combined_text for keyword in keywords):
                    topic_counts[topic] += 1

    if not topic_counts:
        topic_counts["General"] = len(sessions) if sessions else 1

    colors = {
        "Anxiety": "#7EC8A4",
        "Stress": "#E07C6B",
        "Sleep": "#2C5F8A",
        "Work": "#4A90D9",
        "Relationships": "#F5A962",
        "Mood": "#7EC8A4",
        "Self-Esteem": "#E07C6B",
        "Goals": "#4A90D9",
        "General": "#9BAABB",
    }

    top_topics = [
        {
            "topic": topic,
            "count": count,
            "color": colors.get(topic, "#4A90D9"),
        }
        for topic, count in topic_counts.most_common(5)
    ]

    return {"topics": top_topics}

@router.get("/achievements")
def get_achievements(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sessions = db.query(ChatSession).filter(
        ChatSession.user_id == current_user.id
    ).all()
    moods = db.query(MoodEntry).filter(
        MoodEntry.user_id == current_user.id
    ).order_by(MoodEntry.date.desc()).all()

    total_sessions = len(sessions)
    total_moods = len(moods)

    streak, _ = calculate_streaks(moods)

    morning_checkins = sum(1 for mood in moods if mood.date.hour < 12)

    achievements = [
        {
            "title": "7-Day Streak",
            "description": "Checked in daily for a full week",
            "key": "streak_7",
            "earned": streak >= 7,
            "progress": min(streak, 7),
            "target": 7,
            "color": "#F5A962",
        },
        {
            "title": "Mood Master",
            "description": "Tracked mood 30 times",
            "key": "mood_30",
            "earned": total_moods >= 30,
            "progress": min(total_moods, 30),
            "target": 30,
            "color": "#7EC8A4",
        },
        {
            "title": "Early Bird",
            "description": "Completed 5 morning check-ins",
            "key": "morning_5",
            "earned": morning_checkins >= 5,
            "progress": min(morning_checkins, 5),
            "target": 5,
            "color": "#4A90D9",
        },
        {
            "title": "Conversation Starter",
            "description": "Started 10 support sessions",
            "key": "sessions_10",
            "earned": total_sessions >= 10,
            "progress": min(total_sessions, 10),
            "target": 10,
            "color": "#E07C6B",
        },
    ]

    return {"achievements": achievements}

@router.get("/patterns")
def get_patterns(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
    moods = db.query(MoodEntry).filter(
        MoodEntry.user_id == current_user.id,
        MoodEntry.date >= cutoff_date,
    ).order_by(MoodEntry.date.asc()).all()

    if not moods:
        return {
            "current_streak": 0,
            "longest_streak": 0,
            "best_day": "No data yet",
            "correlations": [],
        }

    current_streak, longest_streak = calculate_streaks(moods)

    weekday_scores: dict[int, list[float]] = {}
    for mood in moods:
        weekday_scores.setdefault(mood.date.weekday(), []).append(mood.mood_score)

    best_day_index = max(
        weekday_scores.items(),
        key=lambda item: average(item[1]),
    )[0]
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    mood_values = [entry.mood_score for entry in moods]
    energy_values = [entry.energy_level for entry in moods]
    stress_values = [entry.stress_level for entry in moods]

    raw_correlations = [
        {
            "label": "Mood vs Energy",
            "value": pearson_correlation(mood_values, energy_values),
            "description": "Higher energy tends to line up with stronger mood scores."
        },
        {
            "label": "Mood vs Stress",
            "value": pearson_correlation(mood_values, stress_values) * -1,
            "description": "Lower stress tends to line up with stronger mood scores."
        },
    ]

    correlations = []
    for item in raw_correlations:
        strength = abs(item["value"])
        if strength >= 0.6:
            summary = "Strong pattern"
        elif strength >= 0.3:
            summary = "Moderate pattern"
        else:
            summary = "Light pattern"

        correlations.append(
            {
                "label": item["label"],
                "summary": summary,
                "score": round(max(min(item["value"], 1), -1) * 100),
                "description": item["description"],
            }
        )

    return {
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "best_day": day_names[best_day_index],
        "correlations": correlations,
    }
