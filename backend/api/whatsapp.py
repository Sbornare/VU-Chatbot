"""
WhatsApp notification API endpoints
Users are auto-subscribed during email registration
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.auth.models import User
from backend.auth.dependencies import get_current_user
from backend.services.deadline_notifier import check_and_send_deadline_alerts
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


class NotificationSettingsUpdate(BaseModel):
    whatsapp_notifications_enabled: bool


@router.get("/whatsapp/status")
def get_whatsapp_status(
    current_user: User = Depends(get_current_user)
):
    """Get user's WhatsApp notification settings"""
    return {
        "phone_number": current_user.phone_number,
        "notifications_enabled": current_user.whatsapp_notifications_enabled,
        "interested_programs": current_user.interested_programs
    }


@router.put("/whatsapp/settings")
def update_whatsapp_settings(
    settings: NotificationSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Enable/disable WhatsApp notifications"""
    try:
        current_user.whatsapp_notifications_enabled = settings.whatsapp_notifications_enabled
        db.commit()
        
        status = "enabled" if settings.whatsapp_notifications_enabled else "disabled"
        return {
            "status": status,
            "message": f"WhatsApp notifications {status}",
            "phone_number": current_user.phone_number
        }
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to update settings")


@router.get("/whatsapp/registered-users")
def get_registered_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all registered users with WhatsApp enabled (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    users = db.query(User).filter(
        User.phone_number.isnot(None),
        User.whatsapp_notifications_enabled == True
    ).all()
    
    return {
        "total": len(users),
        "users": [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "phone_number": u.phone_number,
                "interested_programs": u.interested_programs
            }
            for u in users
        ]
    }


@router.post("/whatsapp/send-deadline-alerts")
def send_deadline_alerts_manual(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Manually trigger deadline alert checking (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        check_and_send_deadline_alerts()
        return {
            "status": "success",
            "message": "Deadline alerts check triggered"
        }
    except Exception as e:
        logger.error(f"Error sending alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to send alerts")

