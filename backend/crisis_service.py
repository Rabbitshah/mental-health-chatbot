"""
Crisis Detection Service
Requirements: 9.1, 9.2, 9.3, 9.5, 9.6
"""
import os
import logging
import re
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 14.1 & 14.4: Configurable crisis keywords and emergency resources
# These can be overridden via environment variables without code changes.
# ---------------------------------------------------------------------------

def _load_crisis_keywords() -> List[str]:
    """Load crisis keywords from environment or use defaults."""
    env_keywords = os.getenv("CRISIS_KEYWORDS")
    if env_keywords:
        return [kw.strip() for kw in env_keywords.split(",") if kw.strip()]
    return [
        "suicide",
        "suicidal",
        "kill myself",
        "kill me",
        "end my life",
        "self-harm",
        "self harm",
        "hurt myself",
        "harm myself",
        "want to die",
        "wanna die",
        "wish i was dead",
        "wish i were dead",
        "no reason to live",
        "don't want to live",
        "dont want to live",
        "can't go on",
        "cant go on",
        "overdose",
        "cut myself",
        "hurt someone",
        "kill someone",
    ]


def _load_emergency_resources() -> dict:
    """Load emergency resources from environment or use defaults."""
    return {
        "US": {
            "hotline": os.getenv("CRISIS_HOTLINE_NAME", "988 Suicide & Crisis Lifeline"),
            "number": os.getenv("CRISIS_HOTLINE_NUMBER", "988"),
            "text": os.getenv("CRISIS_HOTLINE_TEXT", "Call or text 988, or chat at 988lifeline.org"),
        },
        "Crisis Text Line": {
            "hotline": os.getenv("CRISIS_TEXT_LINE_NAME", "Crisis Text Line"),
            "number": os.getenv("CRISIS_TEXT_LINE_NUMBER", "741741"),
            "text": os.getenv("CRISIS_TEXT_LINE_TEXT", "Text HOME to 741741"),
        },
    }


# Module-level configuration (loaded once, can be reloaded via reload_config())
CRISIS_KEYWORDS: List[str] = _load_crisis_keywords()
EMERGENCY_RESOURCES: dict = _load_emergency_resources()


def reload_config() -> None:
    """Reload configuration from environment variables (useful for testing)."""
    global CRISIS_KEYWORDS, EMERGENCY_RESOURCES
    CRISIS_KEYWORDS = _load_crisis_keywords()
    EMERGENCY_RESOURCES = _load_emergency_resources()


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class EmergencyResource:
    hotline: str
    number: str
    text: str
    region: str = "US"


@dataclass
class CrisisDetection:
    is_crisis: bool
    matched_keywords: List[str] = field(default_factory=list)
    confidence: float = 0.0
    detection_method: str = "keyword" # "keyword", "semantic", or "hybrid"


# ---------------------------------------------------------------------------
# 14.1: detect_crisis() — Hybrid Detection
# ---------------------------------------------------------------------------

def _semantic_safety_scan(message: str) -> float:
    """
    A lightweight semantic scan looking for intent markers and urgent phrases
    that might miss direct keyword matches but indicate high risk.
    Returns a confidence score between 0.0 and 1.0.
    """
    msg = message.lower()
    score = 0.0
    
    # Intent markers: "i will", "i'm going to", "i plan to"
    intent_markers = [r"i'?m (?:going to|gonna) (?:end|kill)", r"i will (?:end|kill)", r"i (?:plan|decided) to (?:end|kill)"]
    for pattern in intent_markers:
        if re.search(pattern, msg):
            score += 0.5
            
    # Hopelessness markers
    hopelessness = [r"no (?:hope|point|reason)", r"never get better", r"done with (?:everything|life)"]
    for pattern in hopelessness:
        if re.search(pattern, msg):
            score += 0.3
            
    # Urgency markers
    urgency = [r"tonight", r"right now", r"goodbye", r"final message"]
    for pattern in urgency:
        if re.search(pattern, msg):
            score += 0.2
            
    return min(score, 1.0)

def detect_crisis(message: str) -> CrisisDetection:
    """
    Scan message text using a hybrid strategy:
    1. Direct Keyword matching (High precision, low recall)
    2. Intent-based heuristic scanning (Moderate precision, higher recall)
    """
    lower_message = " ".join(message.lower().split())
    matched_keywords = []
    
    # 1. Keyword Scan
    for keyword in CRISIS_KEYWORDS:
        normalized_keyword = " ".join(keyword.lower().split())
        pattern = r"(?<![a-z0-9])" + re.escape(normalized_keyword) + r"(?![a-z0-9])"
        if re.search(pattern, lower_message):
            matched_keywords.append(keyword)
            
    # 2. Semantic/Heuristic Scan
    semantic_score = _semantic_safety_scan(message)
    
    is_crisis = bool(matched_keywords) or semantic_score >= 0.5
    
    method = "hybrid" if (matched_keywords and semantic_score > 0) else ("keyword" if matched_keywords else "semantic")
    confidence = 1.0 if matched_keywords else semantic_score
    
    return CrisisDetection(
        is_crisis=is_crisis,
        matched_keywords=matched_keywords,
        confidence=confidence,
        detection_method=method
    )


# ---------------------------------------------------------------------------
# 14.4: get_crisis_resources() — returns configured emergency resources
# ---------------------------------------------------------------------------

def get_crisis_resources() -> List[EmergencyResource]:
    """Return the list of configured emergency resources."""
    resources = []
    for region, info in EMERGENCY_RESOURCES.items():
        resources.append(
            EmergencyResource(
                hotline=info.get("hotline", ""),
                number=info.get("number", ""),
                text=info.get("text", ""),
                region=region,
            )
        )
    return resources


# ---------------------------------------------------------------------------
# 14.2: log_crisis_event() — persist a CrisisEvent record
# ---------------------------------------------------------------------------

def log_crisis_event(
    user_id: int,
    keywords: List[str],
    db,
    message_id: Optional[int] = None,
    confidence: float = 0.0,
    method: str = "keyword"
) -> None:
    """
    Log a crisis event to the database.
    """
    from models import CrisisEvent

    try:
        event = CrisisEvent(
            user_id=user_id,
            message_id=message_id,
            keywords=keywords,
            confidence=confidence,
            detection_method=method,
            created_at=datetime.now(timezone.utc),
        )
        db.add(event)
        db.commit()
        logger.info(
            "Crisis event logged: user_id=%s, method=%s, confidence=%s, keywords=%s",
            user_id,
            method,
            confidence,
            keywords,
        )
    except Exception as exc:
        logger.error("Failed to log crisis event: %s", exc, exc_info=True)
        db.rollback()
