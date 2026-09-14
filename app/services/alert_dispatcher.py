"""Decides whether a risk score warrants an alert, builds the message, 
sends via Twilio SMS / FCM push, and logs the result to the alerts table."""

import logging
from twilio.rest import Client as TwilioClient
from twilio.base.exceptions import TwilioRestException

from app.config import settings

logger = logging.getLogger(__name__)

ALERTABLE_LEVELS = {"high", "critical"}


def should_alert(risk_level: str) -> bool:
    """Returns True only for 'high' or 'critical' risk levels."""
    return risk_level in ALERTABLE_LEVELS


def build_alert_message(risk_level: str, contributing_factors: dict) -> str:
    """Builds a short, SMS-friendly wellness alert (never diagnostic language)."""
    factor_bits = []
    for key, value in contributing_factors.items():
        label = key.replace("_", " ")
        factor_bits.append(f"{label}: {value}")
    factors_str = ", ".join(factor_bits) if factor_bits else "multiple indicators"

    message = (
        f"PRAHARI Alert: {risk_level.upper()} risk detected. "
        f"{factors_str}. Please check on this person."
    )

    if len(message) > 160:
        message = message[:157] + "..."

    return message


def send_sms_alert(phone_number: str, message: str) -> bool:
    """Sends an SMS via Twilio. Never raises — logs and returns False on failure."""
    if not settings.twilio_account_sid or not settings.twilio_auth_token:
        logger.warning("Twilio credentials not configured; skipping SMS alert.")
        return False

    try:
        client = TwilioClient(settings.twilio_account_sid, settings.twilio_auth_token)
        client.messages.create(
            body=message,
            from_=settings.twilio_from_number,
            to=phone_number,
        )
        return True
    except TwilioRestException as e:
        logger.error(f"Twilio SMS send failed for {phone_number}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending SMS to {phone_number}: {e}")
        return False


def send_push_alert(user_id: str, message: str) -> bool:
    """Placeholder for FCM push notifications.
    TODO: wire up real Firebase Cloud Messaging once FCM server key + 
    device tokens are available. For now, just logs what would be sent."""
    logger.info(f"[FCM STUB] Would send push to user {user_id}: {message}")
    return True


def dispatch_alert(
    user_id: str,
    phone_number: str,
    risk_score_id: int,
    risk_level: str,
    contributing_factors: dict,
    db,
) -> dict | None:
    """Orchestrates the full alert flow. Never raises — a dispatch failure 
    must not break the caller's (ingestion) response."""
    try:
        if not should_alert(risk_level):
            return None

        message = build_alert_message(risk_level, contributing_factors)

        sms_sent = send_sms_alert(phone_number, message) if phone_number else False
        push_sent = send_push_alert(user_id, message)

        if sms_sent and push_sent:
            channel = "both"
        elif sms_sent:
            channel = "sms"
        elif push_sent:
            channel = "push"
        else:
            channel = "push"

        result = (
            db.table("alerts")
            .insert(
                {
                    "user_id": user_id,
                    "risk_score_id": risk_score_id,
                    "alert_type": risk_level,
                    "channel": channel,
                    "message": message,
                    "acknowledged": False,
                }
            )
            .execute()
        )

        return result.data[0] if result.data else None

    except Exception as e:
        logger.error(f"Alert dispatch failed for user {user_id}: {e}")
        return None