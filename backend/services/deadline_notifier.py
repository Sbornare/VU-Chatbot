"""
Background task to send WhatsApp deadline alerts
Run periodically using APScheduler
"""
from datetime import datetime, timedelta
from backend.database import mongo_db
from backend.rag.retriever import retrieve_context
import logging

logger = logging.getLogger(__name__)


def get_closing_deadlines():
    """Extract admission closing dates from knowledge base"""
    # Query the vector store for admission closing dates
    result = retrieve_context("What are the admission closing dates?")
    context = result.get("context", "")
    
    # Parse dates from context (this is a simplified version)
    deadlines = []
    
    # Example format: Extract dates in format "MM/DD/YYYY"
    import re
    date_pattern = r'(\d{1,2})/(\d{1,2})/(\d{4})'
    dates = re.findall(date_pattern, context)
    
    for month, day, year in dates:
        try:
            deadline_date = datetime(int(year), int(month), int(day))
            deadlines.append({
                "date": deadline_date,
                "program": "Various Programs",  # You can enhance this
                "raw_date_str": f"{month}/{day}/{year}"
            })
        except ValueError:
            continue
    
    return deadlines


def check_and_send_deadline_alerts():
    """
    Check for upcoming deadlines and send WhatsApp alerts to ALL registered users
    Call this function periodically (e.g., every 6 hours)
    """
    try:
        # Get all users with WhatsApp notifications enabled
        users = list(
            mongo_db.users.find(
                {
                    "phone_number": {"$nin": [None, ""]},
                    "whatsapp_notifications_enabled": True,
                },
                {"_id": 0},
            )
        )
        
        if not users:
            logger.info("No users registered with WhatsApp notifications")
            return
        
        logger.info(f"Checking deadlines for {len(users)} users")
        
        # Get upcoming deadlines
        deadlines = get_closing_deadlines()
        today = datetime.now().date()
        
        alerts_sent = 0
        alerts_failed = 0
        
        # Check each deadline
        for deadline in deadlines:
            deadline_date = deadline["date"].date()
            days_remaining = (deadline_date - today).days
            
            # Send alert if deadline is approaching (within 30 days)
            if 0 < days_remaining <= 30:
                # Send to all users
                for user in users:
                    # Check if this program matches user's interests
                    programs = [
                        p.strip().lower()
                        for p in (user.get("interested_programs") or "").split(",")
                        if p.strip()
                    ]
                    
                    # Send to all users if no specific programs or program matches
                    should_notify = not programs or any(
                        prog in deadline["program"].lower() for prog in programs
                    )
                    
                    if should_notify:
                        try:
                            # WhatsApp service disabled
                            # success = whatsapp_service.send_deadline_alert(
                            #     user.get("phone_number"),
                            #     deadline["program"],
                            #     days_remaining,
                            #     deadline["raw_date_str"]
                            # )
                            # 
                            # if success:
                            #     alerts_sent += 1
                            #     logger.info(f"Alert sent to {user.get('phone_number')} for {deadline['program']}")
                            # else:
                            #     alerts_failed += 1
                            pass
                        except Exception as e:
                            logger.error(f"Failed to send alert to {user.get('phone_number')}: {e}")
                            alerts_failed += 1
        
        logger.info(f"Deadline alerts: {alerts_sent} sent, {alerts_failed} failed")
        
    except Exception as e:
        logger.error(f"Error checking deadlines: {e}")


def start_deadline_checker(scheduler):
    """Start background task scheduler"""
    try:
        # Run every 6 hours
        scheduler.add_job(
            check_and_send_deadline_alerts,
            'interval',
            hours=6,
            id='deadline_checker',
            name='Check and send deadline alerts to all users'
        )
        logger.info("Deadline checker started - will run every 6 hours")
    except Exception as e:
        logger.error(f"Failed to start deadline checker: {e}")

