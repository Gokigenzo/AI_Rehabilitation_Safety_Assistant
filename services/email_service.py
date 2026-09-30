"""
Email Alert Service for AI Rehabilitation & Safety Assistant.
Sends emergency notifications with snapshot evidence to the registered Caregiver Gmail.
Fault-tolerant: Network/SMTP failures log warnings and update status without crashing the app.
"""

from __future__ import annotations

import logging
import smtplib
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional

from config import (
    EMAIL_ENABLED,
    EMAIL_HOST,
    EMAIL_PASSWORD,
    EMAIL_PORT,
    EMAIL_USERNAME,
)
from services.user_service import UserService

logger = logging.getLogger("EmailService")


class EmailService:
    """Manages emergency SMTP Gmail notifications with snapshot attachments."""

    def __init__(
        self,
        enabled: Optional[bool] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> None:
        self.enabled = EMAIL_ENABLED if enabled is None else enabled
        self.host = host or EMAIL_HOST
        self.port = port or EMAIL_PORT
        self.username = username if username is not None else EMAIL_USERNAME
        self.password = password if password is not None else EMAIL_PASSWORD

    def send_fall_alert(
        self,
        recipient_email: str,
        user_name: str,
        timestamp: str,
        confidence: float = 0.90,
        snapshot_path: Optional[str] = None,
    ) -> bool:
        """
        Send emergency fall alert to caregiver Gmail.
        Returns True if sent successfully, False otherwise.
        Guaranteed to never raise an unhandled exception or crash the caller.
        """
        clean_recipient = (recipient_email or "").strip()

        # 1. Validate recipient email format
        if not clean_recipient or not UserService.validate_email(clean_recipient):
            logger.warning("Cannot send fall alert: Invalid or missing caregiver email '%s'", clean_recipient)
            return False

        # 2. Check if email service is enabled & configured
        if not self.enabled:
            logger.info("Email service is disabled in config (EMAIL_ENABLED=false). Alert email skipped.")
            return False

        if not self.username or not self.password:
            logger.warning(
                "System Gmail credentials not configured in .env (EMAIL_USERNAME or EMAIL_PASSWORD empty). Alert email skipped."
            )
            return False

        logger.info(
            "Preparing emergency alert email for user '%s' to caregiver '%s'...",
            user_name,
            clean_recipient,
        )

        try:
            # Construct Email Message
            msg = MIMEMultipart()
            msg["Subject"] = f"[CẢNH BÁO] Phát hiện dấu hiệu ngã — {user_name}"
            msg["From"] = f"Hệ Thống AI Giám Sát An Toàn <{self.username}>"
            msg["To"] = clean_recipient

            # HTML & Plain Text Body
            body_text = f"""
Kính gửi Người chăm sóc / Người thân,

Hệ thống AI Phục hồi Chức năng & Giám sát An toàn (AI Rehabilitation & Safety Assistant) phát hiện một sự kiện có dấu hiệu ngã đối với người dùng:

• Người dùng: {user_name}
• Thời gian ghi nhận: {timestamp}
• Mức độ cảnh báo: KHẨN CẤP (Độ tin cậy: {confidence*100:.1f}%)

Vui lòng kiểm tra ngay tình trạng sức khỏe của người dùng hoặc liên hệ trực tiếp để bảo đảm an toàn.

---
Email tự động gửi từ Trợ lý AI Phục hồi & Giám sát An toàn.
            """.strip()

            msg.attach(MIMEText(body_text, "plain", "utf-8"))

            # Attach Snapshot Evidence if available
            if snapshot_path:
                snap_file = Path(snapshot_path)
                if snap_file.exists():
                    try:
                        with open(snap_file, "rb") as f:
                            img_data = f.read()
                        mime_img = MIMEImage(img_data, name=snap_file.name)
                        mime_img.add_header("Content-Disposition", "attachment", filename=snap_file.name)
                        msg.attach(mime_img)
                        logger.info("Attached evidence snapshot: %s", snap_file.name)
                    except Exception as e:
                        logger.warning("Could not attach snapshot image %s: %s", snap_file, e)

            # Send via SMTP with STARTTLS
            with smtplib.SMTP(self.host, self.port, timeout=10) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(self.username, self.password)
                server.send_message(msg)

            logger.info("Email alert successfully sent to caregiver: %s", clean_recipient)
            return True

        except smtplib.SMTPAuthenticationError:
            logger.error("Gmail SMTP authentication failed. Please verify EMAIL_USERNAME and Google App Password.")
            return False
        except smtplib.SMTPConnectError:
            logger.error("Failed to connect to SMTP server %s:%s. Check internet connection.", self.host, self.port)
            return False
        except Exception as e:
            logger.error("Unexpected error delivering alert email to %s: %s", clean_recipient, e)
            return False
