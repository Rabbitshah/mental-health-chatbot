import logging
import time

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
import os
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from database import get_db
from models import ChatSession, ChatMessage, User
from dependencies import get_current_user
from limiter import limiter
from redis_client import cache_delete, CacheKeys, invalidate_user_caches
from crisis_service import detect_crisis, get_crisis_resources, log_crisis_event, EmergencyResource

logger = logging.getLogger(__name__)

import google.generativeai as genai

# Load environment variables from backend/.env
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is not set in environment variables")

# Configure Gemini client
genai.configure(api_key=GEMINI_API_KEY)

# ✅ Force Gemini 1.5 Flash
MODEL_NAME = "gemini-2.5-flash"
print("Using Gemini model:", MODEL_NAME)

MENTAL_HEALTH_SYSTEM_PROMPT = """
You are a warm, calming, and emotionally supportive mental-health chatbot. 
Your goal is to make users feel safe, understood, and comfortable sharing how they feel — 
while staying fully within safe boundaries, without diagnosing or giving medical advice.

Your core personality:
- Calm, gentle, friendly, empathetic.
- Speaks like a supportive companion who genuinely cares.
- Creates a sense of trust, emotional safety, and non-judgment.
- Encourages openness but never pressures the user.

Your response rules:
1. Keep answers short, clear, and easy to read.
2. Prefer bullet points over long paragraphs.
3. If the user is emotional, speak slowly, softly, and compassionately.
4. Maintain a professional tone while staying warm and human-friendly.
5. Do NOT diagnose, label conditions, or claim to provide therapy.
6. Encourage seeking professional help when needed.
7. Never dismiss, invalidate, or minimize emotions.
8. Adapt tone to the user:
   - If sad → be gentle, comforting.
   - If anxious → be grounding and reassuring.
   - If overwhelmed → provide step-by-step calming suggestions.
   - If confused → explain simply, clearly.
   - If angry → validate the feeling without escalation.

When responding:
- Keep responses to 4–6 concise bullet points unless the user asks for a long explanation.
- End with a brief reassuring line like: 
  “You’re not alone. I’m here with you.”
- For complex topics, break things into simple, clear steps.

Examples of how to respond:
If user expresses sadness:
- Acknowledge the emotion kindly.
- Normalize it.
- Offer 4–5 gentle coping ideas.
- Encourage reaching out to someone safe.
- Stay compassionate throughout.

If user asks for advice:
- Give small, actionable steps.
- Keep it supportive and non-directive.

If user asks about personal struggles:
- Validate their experience.
- Offer grounding or reflection prompts.
- Keep tone calm and understanding.

Boundaries:
- No diagnosis.
- No promises of improvement.
- No crisis handling beyond suggesting emergency help.
- If user mentions self-harm or severe distress:
  → Encourage contacting a local emergency line, trusted person, or mental health professional immediately.

Overall communication vibe:
- Soft, friendly, non-judgmental, human-like.
- Help users feel heard, safe, and supported.
- Speak in a way that builds trust and emotional comfort.
"""

# Include the system prompt using the system_instruction feature available in newer models
model = genai.GenerativeModel(
    model_name=MODEL_NAME,
    system_instruction=MENTAL_HEALTH_SYSTEM_PROMPT
)

def get_session_history(session_id: int, db: Session, limit: int = 50) -> list:
    """
    8.1: Retrieve the last `limit` messages for a session, ordered oldest-first.
    Requirements: 4.1, 4.4
    """
    from sqlalchemy import desc, select as sa_select
    # Fetch the IDs of the most recent `limit` messages, then return in chronological order.
    recent_ids = (
        sa_select(ChatMessage.id)
        .where(ChatMessage.session_id == session_id)
        .order_by(desc(ChatMessage.created_at))
        .limit(limit)
        .scalar_subquery()
    )
    return (
        db.query(ChatMessage)
        .filter(ChatMessage.id.in_(recent_ids))
        .order_by(ChatMessage.created_at.asc())
        .all()
    )


def format_history_for_gemini(messages: list) -> list:
    """
    8.2: Convert ChatMessage objects to the Gemini API history format.
    DB sender 'user' -> role 'user'; DB sender 'ai' -> role 'model'.
    Requirements: 4.2, 4.3
    """
    history = []
    for msg in messages:
        role = "user" if msg.sender == "user" else "model"
        history.append({"role": role, "parts": [{"text": msg.text}]})
    return history


router = APIRouter()

STOP_WORDS = {
    "about", "after", "again", "been", "being", "feel", "feeling", "from", "have",
    "just", "keep", "kind", "lately", "like", "more", "really", "that", "this", "with",
    "would", "could", "should", "there", "their", "them", "they", "what", "when",
    "where", "which", "while", "because", "into", "your", "want", "need", "help",
}

TAG_RULES = {
    "Anxiety": ["anxiety", "anxious", "panic", "worry", "worried", "nervous"],
    "Stress": ["stress", "stressed", "overwhelmed", "pressure", "burnout"],
    "Sleep": ["sleep", "insomnia", "tired", "rest", "restless"],
    "Relationships": ["relationship", "partner", "friend", "family", "parents", "breakup"],
    "Career": ["work", "job", "office", "manager", "career", "deadline"],
    "Reflection": ["reflect", "reflection", "journal", "thinking", "mindful"],
    "Goals": ["goal", "habit", "routine", "discipline", "focus", "motivation"],
    "Health": ["health", "exercise", "eat", "eating", "body", "wellness"],
}

CRISIS_RESPONSE = """- I'm really sorry you're going through this right now.
- If you might hurt yourself or someone else, call your local emergency number right now.
- If you're in the U.S. or Canada, call or text 988 immediately to reach the Suicide & Crisis Lifeline.
- If you can, move closer to another person or contact someone you trust and tell them you need immediate support.
- Put some distance between yourself and anything you could use to hurt yourself or someone else.

You deserve immediate human support right now."""

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    session_id: Optional[int] = Field(None, ge=1)

    @field_validator('message')
    @classmethod
    def message_not_whitespace(cls, v):
        if not v or v.strip() == '':
            raise ValueError('Message cannot be empty or whitespace only')
        return v.strip()

def extract_keywords(text: str) -> list[str]:
    words = []
    current_word = []

    for char in text.lower():
        if char.isalnum():
            current_word.append(char)
        elif current_word:
            words.append("".join(current_word))
            current_word = []

    if current_word:
        words.append("".join(current_word))

    keywords = []
    for word in words:
        if len(word) < 4 or word in STOP_WORDS:
            continue
        if word not in keywords:
            keywords.append(word)
    return keywords

def infer_session_tag(text: str) -> str:
    import re
    lower_text = text.lower()
    for tag, keywords in TAG_RULES.items():
        if any(re.search(r'\b' + re.escape(keyword) + r'\b', lower_text) for keyword in keywords):
            return tag
    return "General"

def build_session_title(text: str, inferred_tag: str) -> str:
    lower_text = text.lower()
    keywords = extract_keywords(text)

    if inferred_tag == "Anxiety":
        if any(keyword in lower_text for keyword in ["work", "job", "office", "career", "manager"]):
            return "Work Anxiety Support"
        return "Anxiety Check-In"
    if inferred_tag == "Stress":
        if any(keyword in lower_text for keyword in ["burnout", "deadline", "pressure"]):
            return "Burnout and Pressure"
        return "Stress Support"
    if inferred_tag == "Sleep":
        return "Sleep and Rest Support"
    if inferred_tag == "Relationships":
        if "family" in lower_text or "parents" in lower_text:
            return "Family Relationship Support"
        if "partner" in lower_text or "breakup" in lower_text:
            return "Relationship Support"
        return "Relationship Check-In"
    if inferred_tag == "Career":
        return "Career Support"
    if inferred_tag == "Reflection":
        return "Personal Reflection"
    if inferred_tag == "Goals":
        return "Goals and Motivation"
    if inferred_tag == "Health":
        return "Health and Wellness"

    if keywords:
        short_keywords = keywords[:3]
        return " ".join(word.capitalize() for word in short_keywords)

    compact_message = " ".join(text.strip().split())
    if not compact_message:
        return "New Conversation"

    return compact_message[:40].rstrip()

def generate_session_title(first_message: str) -> str:
    """Generate a session title from the first message, truncating to 50 chars."""
    text = first_message.strip()
    if len(text) <= 50:
        return text
    return text[:47] + "..."

def is_auto_generated_title(title: str) -> bool:
    return title == "New Conversation" or title.endswith("...")


def generate_summary(session_id: int, db: Session) -> Optional[str]:
    """
    15.2: Generate a concise summary for a chat session using the Gemini API.
    - Only generates if the session has more than 10 messages.
    - Limits summary to 200 characters.
    - Falls back to the first user message on error.
    Requirements: 19.1, 19.5, 19.6
    """
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )

    if len(messages) <= 10:
        return None

    # Fallback: first user message
    first_user_msg = next((m.text for m in messages if m.sender == "user"), None)
    fallback = (first_user_msg[:200] if first_user_msg else None)

    try:
        # Build a compact transcript for the summary prompt
        transcript_lines = []
        for m in messages:
            role = "User" if m.sender == "user" else "Assistant"
            transcript_lines.append(f"{role}: {m.text}")
        transcript = "\n".join(transcript_lines)

        summary_prompt = (
            "Summarize the following mental health support conversation in one concise sentence "
            "of no more than 200 characters. Focus on the main topic discussed.\n\n"
            f"{transcript}"
        )

        summary_model = genai.GenerativeModel(model_name=MODEL_NAME)
        response = summary_model.generate_content(summary_prompt)
        summary_text = response.text.strip()

        # Enforce 200-character limit
        if len(summary_text) > 200:
            summary_text = summary_text[:197] + "..."

        return summary_text

    except Exception as e:
        logger.warning(f"Summary generation failed for session {session_id}: {e}")
        return fallback

@router.post("/chat")
@limiter.limit("10/minute")
@limiter.limit("100/hour")
def chat(
    request: Request,
    body: ChatRequest, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    try:
        # 1. Resolve or create ChatSession
        if body.session_id:
            chat_session = db.query(ChatSession).filter(
                ChatSession.id == body.session_id,
                ChatSession.user_id == current_user.id
            ).first()
            if not chat_session:
                raise HTTPException(status_code=404, detail="Chat session not found")
        else:
            inferred_tag = infer_session_tag(body.message)
            title = build_session_title(body.message, inferred_tag)
            chat_session = ChatSession(
                user_id=current_user.id,
                title=title,
                tag=inferred_tag,
            )
            db.add(chat_session)
            db.commit()
            db.refresh(chat_session)

        # 2. Fetch history and build Gemini format
        # 8.1: Load last 50 messages ordered chronologically (oldest first) - Req 4.1, 4.4
        previous_messages = get_session_history(chat_session.id, db)

        # 8.2 & 8.3: Format for Gemini API and pass to start_chat() - Req 4.2, 4.3, 4.5
        history = format_history_for_gemini(previous_messages)

        # 3. Save User Message
        user_msg = ChatMessage(
            session_id=chat_session.id,
            sender="user",
            text=body.message
        )
        db.add(user_msg)
        db.commit()
        db.refresh(user_msg)

        # 14.1 & 14.3: Detect crisis keywords in user message
        crisis_result = detect_crisis(body.message)
        crisis_resources = None

        # 4. Use a deterministic safety response for crisis messages.
        if crisis_result.is_crisis:
            ai_text = CRISIS_RESPONSE
            # 14.2 & 14.3: Log the crisis event
            log_crisis_event(
                user_id=current_user.id,
                keywords=crisis_result.matched_keywords,
                db=db,
                message_id=user_msg.id,
                confidence=crisis_result.confidence,
                method=crisis_result.detection_method
            )
            # 14.4 & 14.3: Augment response with emergency resources
            crisis_resources = [
                {
                    "hotline": r.hotline,
                    "number": r.number,
                    "text": r.text,
                    "region": r.region,
                }
                for r in get_crisis_resources()
            ]
        else:
            # --- Task 18.4: Log AI service call ---
            ai_start = time.perf_counter()
            logger.info(
                "gemini api call started",
                extra={
                    "user_id": current_user.id,
                    "session_id": chat_session.id,
                },
            )
            try:
                chat_obj = model.start_chat(history=history)
                response = chat_obj.send_message(body.message)
                ai_text = response.text
                ai_elapsed_ms = round((time.perf_counter() - ai_start) * 1000, 2)

                # Log token usage if available in response metadata
                token_usage: dict = {}
                try:
                    if hasattr(response, "usage_metadata") and response.usage_metadata:
                        meta = response.usage_metadata
                        token_usage = {
                            "prompt_tokens": getattr(meta, "prompt_token_count", None),
                            "candidates_tokens": getattr(meta, "candidates_token_count", None),
                            "total_tokens": getattr(meta, "total_token_count", None),
                        }
                except Exception:
                    pass

                logger.info(
                    "gemini api call completed",
                    extra={
                        "user_id": current_user.id,
                        "session_id": chat_session.id,
                        "response_time_ms": ai_elapsed_ms,
                        **token_usage,
                    },
                )
            except Exception as ai_exc:
                ai_elapsed_ms = round((time.perf_counter() - ai_start) * 1000, 2)
                logger.error(
                    "gemini api call failed",
                    extra={
                        "user_id": current_user.id,
                        "session_id": chat_session.id,
                        "response_time_ms": ai_elapsed_ms,
                        "error": repr(ai_exc),
                    },
                    exc_info=True,
                )
                raise

        # 5. Save AI Message
        ai_msg = ChatMessage(
            session_id=chat_session.id,
            sender="ai",
            text=ai_text
        )
        db.add(ai_msg)

        # Update the session tag when a later message reveals a clearer topic.
        inferred_tag = infer_session_tag(body.message)
        if chat_session.tag == "General" and inferred_tag != "General":
            chat_session.tag = inferred_tag

        user_message_count = db.query(ChatMessage).filter(
            ChatMessage.session_id == chat_session.id,
            ChatMessage.sender == "user",
        ).count()
        refreshed_title = build_session_title(body.message, inferred_tag)
        if (
            refreshed_title
            and refreshed_title != chat_session.title
            and user_message_count <= 3
            and is_auto_generated_title(chat_session.title)
        ):
            chat_session.title = refreshed_title

        db.commit()

        # 15.3: Generate or regenerate conversation summary
        # Count total messages in the session after saving
        total_msg_count = db.query(ChatMessage).filter(
            ChatMessage.session_id == chat_session.id
        ).count()

        should_summarize = False
        if total_msg_count >= 10:
            if chat_session.summary is None:
                # First summary: session just reached 10 messages
                should_summarize = True
            else:
                # Regenerate every 20 new messages since the 10-message baseline
                messages_since_baseline = total_msg_count - 10
                if messages_since_baseline > 0 and messages_since_baseline % 20 == 0:
                    should_summarize = True

        if should_summarize:
            new_summary = generate_summary(chat_session.id, db)
            if new_summary:
                chat_session.summary = new_summary
                db.commit()

        # Invalidate caches so stale data is not served (Requirement 12.3)
        try:
            invalidate_user_caches(current_user.id, session_id=chat_session.id)
        except Exception as cache_err:
            logger.warning(f"Cache invalidation failed after chat message save: {cache_err}")

        return {
            "response": ai_text,
            "session_id": chat_session.id,
            "crisis_detected": crisis_result.is_crisis,
            "emergency_resources": crisis_resources,
        }

    except HTTPException:
        raise
    except Exception as e:
        msg = str(e)
        # --- Task 18.3: Log exception with context ---
        logger.error(
            "unhandled exception in /chat",
            extra={
                "user_id": getattr(current_user, "id", None),
                "session_id": getattr(body, "session_id", None),
                "error": repr(e),
            },
            exc_info=True,
        )
        print("Gemini Error in /chat:", repr(e))

        if "ResourceExhausted" in repr(e) or "quota" in msg.lower():
            raise HTTPException(
                status_code=503,
                detail=(
                    "Our mental health assistant has temporarily reached its usage "
                    "limit with the AI provider (quota exceeded). Please try again "
                    "later or contact the administrator to increase the Gemini API quota."
                ),
            )

        raise HTTPException(status_code=500, detail="Internal error in AI backend.")
