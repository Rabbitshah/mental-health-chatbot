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

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    session_id: Optional[int] = Field(None, ge=1)

    @validator('message')
    def message_not_whitespace(cls, v):
        if not v or v.strip() == '':
            raise ValueError('Message cannot be empty or whitespace only')
        return v.strip()

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
            # Generate a simple title from the first message
            title = body.message[:30] + "..." if len(body.message) > 30 else body.message
            chat_session = ChatSession(user_id=current_user.id, title=title)
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

        # 4. Generate AI response
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
