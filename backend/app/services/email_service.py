"""Sends OTP emails to Mailpit (a local mail catcher - see http://localhost:8025)."""

import logging
import smtplib
from email.message import EmailMessage

from app.config import settings
from app.core.logging_config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)


def send_otp(to_email: str, otp: str) -> None:
    msg = EmailMessage()
    msg["Subject"] = "StockSense password reset code"
    msg["From"] = "no-reply@stocksense.com"
    msg["To"] = to_email
    msg.set_content(
        f"Your StockSense password reset code is {otp}.\n"
        "It expires in 10 minutes. If you didn't ask for this, ignore this email."
    )
    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=5) as smtp:
            smtp.send_message(msg)
        logger.info("OTP email sent to %s", to_email)
    except OSError:
        # Dev fallback so the demo still works when Mailpit isn't running.
        logger.warning("Mailpit not reachable - DEV ONLY OTP for %s is %s", to_email, otp)
