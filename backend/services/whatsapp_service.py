"""
WhatsApp notification service for admission deadline alerts
Uses Twilio WhatsApp API
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from twilio.rest import Client
from backend.config import settings

logger = logging.getLogger(__name__)


class WhatsAppNotificationService:
    def __init__(self):
        """Initialize Twilio WhatsApp client"""
        try:
            self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            self.from_number = settings.TWILIO_WHATSAPP_NUMBER
            self.enabled = True
        except Exception as e:
            logger.error(f"Failed to initialize WhatsApp service: {e}")
            self.enabled = False

    def send_notification(self, to_phone: str, message: str) -> bool:
        """
        Send WhatsApp message
        Args:
            to_phone: Recipient phone number (format: +1234567890)
            message: Message content
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            logger.warning("WhatsApp service not enabled")
            return False

        try:
            msg = self.client.messages.create(
                from_=f"whatsapp:{self.from_number}",
                to=f"whatsapp:{to_phone}",
                body=message
            )
            logger.info(f"WhatsApp message sent to {to_phone}: {msg.sid}")
            return True
        except Exception as e:
            logger.error(f"Failed to send WhatsApp message to {to_phone}: {e}")
            return False

    def send_deadline_alert(self, to_phone: str, program: str, days_remaining: int, deadline_date: str) -> bool:
        """Send admission deadline alert"""
        if days_remaining == 1:
            urgency = "TOMORROW"
        elif days_remaining <= 3:
            urgency = "IN THE NEXT FEW DAYS"
        else:
            urgency = f"IN {days_remaining} DAYS"

        message = f"""🎓 *Admission Deadline Alert*

Program: {program}
Closing: {deadline_date}
Time: {urgency}

Don't miss this opportunity! 
Complete your application now.

Visit: https://vu-chatbot.com/apply
Questions? Ask our chatbot! 🤖"""

        return self.send_notification(to_phone, message)

    def send_batch_notifications(self, recipients: List[dict]) -> dict:
        """
        Send notifications to multiple users
        Args:
            recipients: List of dicts with 'phone', 'program', 'days_remaining', 'deadline_date'
        Returns:
            Dict with success/failure counts
        """
        results = {"sent": 0, "failed": 0}
        
        for recipient in recipients:
            success = self.send_deadline_alert(
                recipient["phone"],
                recipient["program"],
                recipient["days_remaining"],
                recipient["deadline_date"]
            )
            if success:
                results["sent"] += 1
            else:
                results["failed"] += 1
        
        return results

    def send_welcome_message(self, to_phone: str, user_name: str) -> bool:
        """Send welcome message when user subscribes"""
        message = f"""👋 Hello {user_name}!

You're subscribed to admission deadline alerts for Vishwakarma University.

We'll notify you when:
✓ Admission dates are closing soon
✓ New programs are available
✓ Important updates

Need help? Ask our chatbot anytime! 🤖

Start chatting: https://vu-chatbot.com"""

        return self.send_notification(to_phone, message)


# Global instance
whatsapp_service = WhatsAppNotificationService()
