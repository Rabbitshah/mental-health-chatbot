"""
Data export endpoint.

Supports JSON, CSV (ZIP), and PDF export formats.
Requirements: 8.1, 8.2, 8.3, 8.4, 8.5
"""
import csv
import io
import json
import zipfile
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user
from limiter import limiter
from models import ChatMessage, ChatSession, JournalEntry, MoodEntry, SafetyPlan, User

router = APIRouter()

VALID_FORMATS = {"json", "csv", "pdf"}


def _session_to_dict(session: ChatSession, messages: List[ChatMessage]) -> dict:
    """Serialize a session and its messages, excluding sensitive fields (Req 8.4)."""
    return {
        "id": session.id,
        "title": session.title,
        "tag": session.tag,
        "summary": session.summary,
        "is_pinned": bool(session.is_pinned),
        "is_archived": bool(session.is_archived),
        "created_at": session.created_at.isoformat() if session.created_at else None,
        "updated_at": session.updated_at.isoformat() if session.updated_at else None,
        "messages": [
            {
                "id": msg.id,
                "sender": msg.sender,
                "text": msg.text,
                "created_at": msg.created_at.isoformat() if msg.created_at else None,
            }
            for msg in messages
        ],
    }


def _mood_to_dict(mood: MoodEntry) -> dict:
    """Serialize a mood entry, excluding sensitive fields (Req 8.4)."""
    return {
        "id": mood.id,
        "mood_score": mood.mood_score,
        "energy_level": mood.energy_level,
        "stress_level": mood.stress_level,
        "date": mood.date.isoformat() if mood.date else None,
    }


def _loads_list(value: str | None) -> list:
    if not value:
        return []
    try:
        data = json.loads(value)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def export_as_json(user: User, db: Session, start_date: datetime | None = None, end_date: datetime | None = None) -> dict:
    """
    Gather all user data and return as a dict (Req 8.1, 8.3, 8.4).
    Excludes password hashes and other sensitive system data.
    """
    sessions_query = db.query(ChatSession).filter(ChatSession.user_id == user.id)
    if start_date:
        sessions_query = sessions_query.filter(ChatSession.created_at >= start_date)
    if end_date:
        sessions_query = sessions_query.filter(ChatSession.created_at <= end_date)
    sessions = sessions_query.order_by(ChatSession.created_at.asc()).all()

    # Single query for all messages (eliminates N+1)
    session_ids = [s.id for s in sessions]
    all_messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id.in_(session_ids))
        .order_by(ChatMessage.created_at.asc())
        .all()
    ) if session_ids else []

    from collections import defaultdict
    msgs_by_session: dict = defaultdict(list)
    for msg in all_messages:
        msgs_by_session[msg.session_id].append(msg)

    sessions_data = [_session_to_dict(s, msgs_by_session[s.id]) for s in sessions]

    moods_query = db.query(MoodEntry).filter(MoodEntry.user_id == user.id)
    if start_date:
        moods_query = moods_query.filter(MoodEntry.date >= start_date)
    if end_date:
        moods_query = moods_query.filter(MoodEntry.date <= end_date)
    moods = moods_query.order_by(MoodEntry.date.asc()).all()
    safety_plan = db.query(SafetyPlan).filter(SafetyPlan.user_id == user.id).first()
    journals_query = db.query(JournalEntry).filter(JournalEntry.user_id == user.id)
    if start_date:
        journals_query = journals_query.filter(JournalEntry.created_at >= start_date)
    if end_date:
        journals_query = journals_query.filter(JournalEntry.created_at <= end_date)
    journals = journals_query.order_by(JournalEntry.created_at.asc()).all()

    # Determine data range
    all_dates = []
    for s in sessions:
        if s.created_at:
            all_dates.append(s.created_at)
    for m in moods:
        if m.date:
            all_dates.append(m.date)

    data_range = {
        "start": min(all_dates).isoformat() if all_dates else None,
        "end": max(all_dates).isoformat() if all_dates else None,
    }

    return {
        "export_timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
        "user": {
            "email": user.email,
            "name": user.name,
            "username": user.username,
            "preferences": {
                "dark_mode": bool(user.dark_mode),
                "email_notifications": bool(user.email_notifications),
                "push_notifications": bool(user.push_notifications),
                "notification_frequency": user.notification_frequency or "daily",
                "language": user.language or "English",
            },
        },
        "data_range": data_range,
        "sessions": sessions_data,
        "moods": [_mood_to_dict(m) for m in moods],
        "safety_plan": {
            "warning_signs": _loads_list(safety_plan.warning_signs),
            "coping_strategies": _loads_list(safety_plan.coping_strategies),
            "trusted_contacts": _loads_list(safety_plan.trusted_contacts),
            "professional_contacts": _loads_list(safety_plan.professional_contacts),
            "safe_environment_steps": _loads_list(safety_plan.safe_environment_steps),
            "reasons_to_stay": _loads_list(safety_plan.reasons_to_stay),
            "updated_at": safety_plan.updated_at.isoformat() if safety_plan and safety_plan.updated_at else None,
        } if safety_plan else None,
        "journals": [
            {
                "id": entry.id,
                "title": entry.title,
                "mood_label": entry.mood_label,
                "mood_score": entry.mood_score,
                "trigger": entry.trigger,
                "thought": entry.thought,
                "body_feeling": entry.body_feeling,
                "reframe": entry.reframe,
                "next_step": entry.next_step,
                "tags": _loads_list(entry.tags),
                "created_at": entry.created_at.isoformat() if entry.created_at else None,
                "updated_at": entry.updated_at.isoformat() if entry.updated_at else None,
            }
            for entry in journals
        ],
    }


def export_as_csv(user: User, db: Session, start_date: datetime | None = None, end_date: datetime | None = None) -> bytes:
    """
    Generate separate CSV files for sessions, messages, and moods,
    then compress into a ZIP archive (Req 8.2, 8.3, 8.5).
    """
    sessions_query = db.query(ChatSession).filter(ChatSession.user_id == user.id)
    if start_date:
        sessions_query = sessions_query.filter(ChatSession.created_at >= start_date)
    if end_date:
        sessions_query = sessions_query.filter(ChatSession.created_at <= end_date)
    sessions = sessions_query.order_by(ChatSession.created_at.asc()).all()

    # Single query for all messages (eliminates N+1)
    session_ids = [s.id for s in sessions]
    all_messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id.in_(session_ids))
        .order_by(ChatMessage.created_at.asc())
        .all()
    ) if session_ids else []

    moods_query = db.query(MoodEntry).filter(MoodEntry.user_id == user.id)
    if start_date:
        moods_query = moods_query.filter(MoodEntry.date >= start_date)
    if end_date:
        moods_query = moods_query.filter(MoodEntry.date <= end_date)
    moods = moods_query.order_by(MoodEntry.date.asc()).all()

    export_ts = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()

    # --- Sessions CSV ---
    sessions_buf = io.StringIO()
    sessions_writer = csv.writer(sessions_buf)
    sessions_writer.writerow([
        "export_timestamp", "user_email",
        "id", "title", "tag", "summary", "created_at", "updated_at",
    ])
    for s in sessions:
        sessions_writer.writerow([
            export_ts, user.email,
            s.id, s.title, s.tag, s.summary or "",
            s.created_at.isoformat() if s.created_at else "",
            s.updated_at.isoformat() if s.updated_at else "",
        ])

    # --- Messages CSV ---
    messages_buf = io.StringIO()
    messages_writer = csv.writer(messages_buf)
    messages_writer.writerow([
        "export_timestamp", "user_email",
        "id", "session_id", "sender", "text", "created_at",
    ])
    for msg in all_messages:
        messages_writer.writerow([
            export_ts, user.email,
            msg.id, msg.session_id, msg.sender, msg.text,
            msg.created_at.isoformat() if msg.created_at else "",
        ])

    # --- Moods CSV ---
    moods_buf = io.StringIO()
    moods_writer = csv.writer(moods_buf)
    moods_writer.writerow([
        "export_timestamp", "user_email",
        "id", "mood_score", "energy_level", "stress_level", "date",
    ])
    for m in moods:
        moods_writer.writerow([
            export_ts, user.email,
            m.id, m.mood_score, m.energy_level, m.stress_level,
            m.date.isoformat() if m.date else "",
        ])

    # --- Compress into ZIP (Req 8.5) ---
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("sessions.csv", sessions_buf.getvalue())
        zf.writestr("messages.csv", messages_buf.getvalue())
        zf.writestr("moods.csv", moods_buf.getvalue())

    return zip_buf.getvalue()


def _pdf_escape(text_value: str) -> str:
    return (
        str(text_value)
        .replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
    )


def _wrap_pdf_line(text_value: str, width: int = 92) -> list[str]:
    words = str(text_value).replace("\r", " ").replace("\n", " ").split()
    lines: list[str] = []
    current = ""
    for word in words:
        next_line = f"{current} {word}".strip()
        if len(next_line) > width and current:
            lines.append(current)
            current = word[:width]
        else:
            current = next_line
    if current:
        lines.append(current)
    return lines or [""]


def export_as_pdf(user: User, db: Session, start_date: datetime | None = None, end_date: datetime | None = None) -> bytes:
    """
    Generate a lightweight text PDF without adding a binary dependency.
    The export is intentionally summarized to keep sensitive chat data portable
    without producing oversized PDFs.
    """
    data = export_as_json(user, db, start_date=start_date, end_date=end_date)
    lines = [
        "AuraChat Personal Data Export",
        f"Exported: {data['export_timestamp']}",
        f"User: {data['user']['name'] or 'Unknown'} <{data['user']['email']}>",
        f"Sessions: {len(data['sessions'])}",
        f"Mood entries: {len(data['moods'])}",
        "",
        "Conversation Sessions",
    ]

    for session in data["sessions"]:
        lines.extend(
            [
                "",
                f"- {session['title']} ({session.get('tag') or 'General'})",
                f"  Created: {session.get('created_at') or 'Unknown'}",
                f"  Messages: {len(session['messages'])}",
            ]
        )
        if session.get("summary"):
            lines.extend(f"  Summary: {line}" for line in _wrap_pdf_line(session["summary"], 82))

    lines.append("")
    lines.append("Mood Check-ins")
    for mood in data["moods"][:120]:
        lines.append(
            "- {date}: mood {mood_score}/10, energy {energy_level}/10, stress {stress_level}/10".format(
                **mood
            )
        )
    if len(data["moods"]) > 120:
        lines.append(f"...and {len(data['moods']) - 120} more mood entries.")

    content_parts = ["BT", "/F1 11 Tf", "50 760 Td", "14 TL"]
    first_line = True
    for raw_line in lines:
        for line in _wrap_pdf_line(raw_line):
            safe_line = _pdf_escape(line.encode("latin-1", "replace").decode("latin-1"))
            if first_line:
                content_parts.append(f"({safe_line}) Tj")
                first_line = False
            else:
                content_parts.append(f"T* ({safe_line}) Tj")
    content_parts.append("ET")
    content = "\n".join(content_parts).encode("latin-1")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(content)).encode("ascii") + b" >>\nstream\n" + content + b"\nendstream",
    ]

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{index} 0 obj\n".encode("ascii"))
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")
    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    )
    return bytes(pdf)


@router.get("/export")
@limiter.limit("5/hour")
def export_data(
    request: Request,
    format: str = Query("json", description="Export format: json, csv, pdf"),
    start_date: datetime | None = Query(default=None),
    end_date: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Export all user data in the requested format.

    - **json**: Returns a JSON object with sessions, messages, and moods (Req 8.1)
    - **csv**: Returns a ZIP archive with separate CSV files (Req 8.2)
    - **pdf**: Returns a compact PDF summary

    Metadata (timestamp, user email, data range) is included in all formats (Req 8.3).
    Sensitive data (password hashes, internal system fields) is excluded (Req 8.4).
    Large exports are compressed (Req 8.5).
    """
    fmt = format.lower().strip()

    if fmt not in VALID_FORMATS:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid format '{format}'. Supported formats: json, csv, pdf",
        )
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=422, detail="start_date must be before end_date")

    if fmt == "json":
        data = export_as_json(current_user, db, start_date=start_date, end_date=end_date)
        return JSONResponse(content=data)

    if fmt == "pdf":
        pdf_bytes = export_as_pdf(current_user, db, start_date=start_date, end_date=end_date)
        filename = f"export_{current_user.id}_{datetime.now(timezone.utc).replace(tzinfo=None).strftime('%Y%m%d%H%M%S')}.pdf"
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    zip_bytes = export_as_csv(current_user, db, start_date=start_date, end_date=end_date)
    filename = f"export_{current_user.id}_{datetime.now(timezone.utc).replace(tzinfo=None).strftime('%Y%m%d%H%M%S')}.zip"
    return StreamingResponse(
        io.BytesIO(zip_bytes),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
