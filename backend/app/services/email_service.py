"""Sends OTP emails.

Default: Mailpit, a local mail catcher (http://localhost:8025) - no login needed.
Real inbox: set SMTP_HOST=smtp.gmail.com, SMTP_PORT=587, SMTP_USER and SMTP_PASSWORD
(a Gmail App Password) in backend/.env.
If sending fails for any reason, the code is written to the server log so the reset still works.
"""

import logging
import smtplib
from email.message import EmailMessage

from app.config import settings
from app.core.logging_config import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)


def send_otp(to_email: str, otp: str) -> None:
    msg = EmailMessage()
    msg["Subject"] = "StockSense password reset code"
    msg["From"] = settings.SMTP_USER or settings.SMTP_FROM
    msg["To"] = to_email
    msg.set_content(
        f"Your StockSense password reset code is {otp}.\n"
        "It expires in 10 minutes. If you didn't ask for this, ignore this email."
    )
    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as smtp:
            if settings.SMTP_USER:
                smtp.starttls()
                smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD.replace(" ", ""))
            smtp.send_message(msg)
        logger.info("OTP email sent to %s via %s", to_email, settings.SMTP_HOST)
    except (OSError, smtplib.SMTPException) as exc:
        # Never break the reset flow because email failed; the code goes to the server log instead.
        logger.warning(
            "Email not sent (%s: %s) - DEV ONLY OTP for %s is %s",
            type(exc).__name__, exc, to_email, otp,
        )
