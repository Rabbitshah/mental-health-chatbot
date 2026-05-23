import json
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user
from models import JournalEntry, SafetyPlan, User

router = APIRouter(prefix="/wellness")


def _loads_list(value: str | None) -> list:
    if not value:
        return []
    try:
        data = json.loads(value)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def _dumps_list(values: list) -> str:
    cleaned = []
    for value in values:
        if isinstance(value, dict):
            cleaned.append(value)
        else:
            text = str(value).strip()
            if text:
                cleaned.append(text[:500])
    return json.dumps(cleaned)


class SafetyPlanPayload(BaseModel):
    warning_signs: List[str] = Field(default_factory=list, max_length=12)
    coping_strategies: List[str] = Field(default_factory=list, max_length=12)
    trusted_contacts: List[str] = Field(default_factory=list, max_length=12)
    professional_contacts: List[str] = Field(default_factory=list, max_length=12)
    safe_environment_steps: List[str] = Field(default_factory=list, max_length=12)
    reasons_to_stay: List[str] = Field(default_factory=list, max_length=12)

    @field_validator(
        "warning_signs",
        "coping_strategies",
        "trusted_contacts",
        "professional_contacts",
        "safe_environment_steps",
        "reasons_to_stay",
        mode="before",
    )
    @classmethod
    def normalize_lists(cls, value):
        if value is None:
            return []
        if not isinstance(value, list):
            raise ValueError("Must be a list")
        return [str(item).strip() for item in value if str(item).strip()]


class SafetyPlanResponse(SafetyPlanPayload):
    id: Optional[int] = None
    updated_at: Optional[datetime] = None


class JournalPayload(BaseModel):
    title: str = Field("Reflection", min_length=1, max_length=100)
    mood_label: Optional[str] = Field(None, max_length=40)
    mood_score: Optional[float] = Field(None, ge=1, le=10)
    trigger: Optional[str] = Field(None, max_length=2000)
    thought: Optional[str] = Field(None, max_length=4000)
    body_feeling: Optional[str] = Field(None, max_length=2000)
    reframe: Optional[str] = Field(None, max_length=4000)
    next_step: Optional[str] = Field(None, max_length=1000)
    tags: List[str] = Field(default_factory=list, max_length=10)

    @field_validator("title", "mood_label", "trigger", "thought", "body_feeling", "reframe", "next_step")
    @classmethod
    def strip_text(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("tags", mode="before")
    @classmethod
    def normalize_tags(cls, value):
        if value is None:
            return []
        if not isinstance(value, list):
            raise ValueError("tags must be a list")
        tags = []
        for item in value:
            tag = str(item).strip()[:40]
            if tag and tag not in tags:
                tags.append(tag)
        return tags


class JournalResponse(JournalPayload):
    id: int
    created_at: datetime
    updated_at: datetime


class JournalListResponse(BaseModel):
    total: int
    entries: List[JournalResponse]


def _safety_plan_to_response(plan: SafetyPlan | None) -> SafetyPlanResponse:
    if not plan:
        return SafetyPlanResponse()
    return SafetyPlanResponse(
        id=plan.id,
        warning_signs=_loads_list(plan.warning_signs),
        coping_strategies=_loads_list(plan.coping_strategies),
        trusted_contacts=_loads_list(plan.trusted_contacts),
        professional_contacts=_loads_list(plan.professional_contacts),
        safe_environment_steps=_loads_list(plan.safe_environment_steps),
        reasons_to_stay=_loads_list(plan.reasons_to_stay),
        updated_at=plan.updated_at,
    )


def _journal_to_response(entry: JournalEntry) -> JournalResponse:
    return JournalResponse(
        id=entry.id,
        title=entry.title,
        mood_label=entry.mood_label,
        mood_score=entry.mood_score,
        trigger=entry.trigger,
        thought=entry.thought,
        body_feeling=entry.body_feeling,
        reframe=entry.reframe,
        next_step=entry.next_step,
        tags=_loads_list(entry.tags),
        created_at=entry.created_at,
        updated_at=entry.updated_at,
    )


@router.get("/safety-plan", response_model=SafetyPlanResponse)
def get_safety_plan(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    plan = db.query(SafetyPlan).filter(SafetyPlan.user_id == current_user.id).first()
    return _safety_plan_to_response(plan)


@router.put("/safety-plan", response_model=SafetyPlanResponse)
def save_safety_plan(
    payload: SafetyPlanPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    plan = db.query(SafetyPlan).filter(SafetyPlan.user_id == current_user.id).first()
    if not plan:
        plan = SafetyPlan(user_id=current_user.id)
        db.add(plan)

    for field in SafetyPlanPayload.model_fields:
        setattr(plan, field, _dumps_list(getattr(payload, field)))

    db.commit()
    db.refresh(plan)
    return _safety_plan_to_response(plan)


@router.get("/journals", response_model=JournalListResponse)
def list_journals(
    q: Optional[str] = Query(default=None, max_length=100),
    limit: int = Query(default=30, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(JournalEntry).filter(JournalEntry.user_id == current_user.id)
    if q:
        like_query = f"%{q.strip()}%"
        query = query.filter(
            JournalEntry.title.ilike(like_query)
            | JournalEntry.thought.ilike(like_query)
            | JournalEntry.reframe.ilike(like_query)
            | JournalEntry.tags.ilike(like_query)
        )

    total = query.count()
    entries = query.order_by(JournalEntry.created_at.desc()).limit(limit).all()
    return JournalListResponse(
        total=total,
        entries=[_journal_to_response(entry) for entry in entries],
    )


@router.post("/journals", response_model=JournalResponse)
def create_journal(
    payload: JournalPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = JournalEntry(
        user_id=current_user.id,
        title=payload.title,
        mood_label=payload.mood_label,
        mood_score=payload.mood_score,
        trigger=payload.trigger,
        thought=payload.thought,
        body_feeling=payload.body_feeling,
        reframe=payload.reframe,
        next_step=payload.next_step,
        tags=_dumps_list(payload.tags),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return _journal_to_response(entry)


@router.put("/journals/{journal_id}", response_model=JournalResponse)
def update_journal(
    journal_id: int,
    payload: JournalPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = db.query(JournalEntry).filter(
        JournalEntry.id == journal_id,
        JournalEntry.user_id == current_user.id,
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")

    for field in ["title", "mood_label", "mood_score", "trigger", "thought", "body_feeling", "reframe", "next_step"]:
        setattr(entry, field, getattr(payload, field))
    entry.tags = _dumps_list(payload.tags)

    db.commit()
    db.refresh(entry)
    return _journal_to_response(entry)


@router.delete("/journals/{journal_id}")
def delete_journal(
    journal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = db.query(JournalEntry).filter(
        JournalEntry.id == journal_id,
        JournalEntry.user_id == current_user.id,
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")

    db.delete(entry)
    db.commit()
    return {"message": "Journal entry deleted"}
