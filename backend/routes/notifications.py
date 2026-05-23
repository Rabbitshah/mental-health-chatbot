from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from datetime import datetime

from database import get_db
from models import Notification, User
from dependencies import get_current_user

router = APIRouter(prefix="/notifications")


class NotificationResponse(BaseModel):
    id: int
    type: str
    message: str
    read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationsListResponse(BaseModel):
    notifications: List[NotificationResponse]
    unread_count: int


class MarkReadResponse(BaseModel):
    id: int
    read: bool


@router.get("", response_model=NotificationsListResponse)
def get_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return all notifications for the authenticated user, ordered by created_at desc."""
    notifications = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .all()
    )
    unread_count = sum(1 for n in notifications if not n.read)
    return NotificationsListResponse(
        notifications=notifications,
        unread_count=unread_count,
    )


@router.put("/{notification_id}/read", response_model=MarkReadResponse)
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark a specific notification as read."""
    notification = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
        .first()
    )
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.read = True
    db.commit()
    db.refresh(notification)

    return MarkReadResponse(id=notification.id, read=notification.read)
