from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field, validator
from typing import Optional
import os
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from database import get_db
from models import ChatSession, ChatMessage, User
from dependencies import get_current_user
from limiter import limiter

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

CRISIS_KEYWORDS = [
    "suicide",
    "kill myself",
    "end my life",
    "want to die",
    "don't want to live",
    "self harm",
    "self-harm",
    "hurt myself",
    "harm myself",
    "overdose",
    "cut myself",
    "kill someone",
    "hurt someone",
    "harm someone else",
]

CRISIS_RESPONSE = """- I'm really sorry you're going through this right now.
- If you might hurt yourself or someone else, call your local emergency number right now.
- If you're in the U.S. or Canada, call or text 988 immediately to reach the Suicide & Crisis Lifeline.
- If you can, move closer to another person or contact someone you trust and tell them you need immediate support.
- Put some distance between yourself and anything you could use to hurt yourself or someone else.

You deserve immediate human support right now."""

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    session_id: Optional[int] = Field(None, ge=1)

    @validator('message')
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
    lower_text = text.lower()
    for tag, keywords in TAG_RULES.items():
        if any(keyword in lower_text for keyword in keywords):
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

def is_auto_generated_title(title: str) -> bool:
    return title == "New Conversation" or title.endswith("...")

def is_crisis_message(text: str) -> bool:
    lower_text = text.lower()
    return any(keyword in lower_text for keyword in CRISIS_KEYWORDS)

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
        previous_messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == chat_session.id
        ).order_by(ChatMessage.created_at.asc()).all()

        history = []
        for msg in previous_messages:
            role = "user" if msg.sender == "user" else "model"
            history.append({"role": role, "parts": [msg.text]})

        # 3. Save User Message
        user_msg = ChatMessage(
            session_id=chat_session.id,
            sender="user",
            text=body.message
        )
        db.add(user_msg)
        db.commit()

        # 4. Use a deterministic safety response for crisis messages.
        if is_crisis_message(body.message):
            ai_text = CRISIS_RESPONSE
        else:
            chat = model.start_chat(history=history)
            response = chat.send_message(body.message)
            ai_text = response.text

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

        return {
            "response": ai_text,
            "session_id": chat_session.id
        }

    except HTTPException:
        raise
    except Exception as e:
        msg = str(e)
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
