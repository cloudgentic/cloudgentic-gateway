"""Notification manager — routes notifications to configured channels."""
import logging
from datetime import datetime, timezone

import httpx

from app.models.notification import NotificationSettings

logger = logging.getLogger(__name__)


class NotificationManager:
    """Dispatches notifications to configured channels (email, telegram, discord, webhook)."""

    async def send(
        self,
        settings: NotificationSettings,
        event_type: str,
        title: str,
        message: str,
        metadata: dict | None = None,
    ) -> dict[str, bool]:
        """Send a notification to all enabled channels that accept this event type.

        Returns a dict of channel -> success status.
        """
        # Check quiet hours
        if self._in_quiet_hours(settings):
            logger.info("Notification suppressed due to quiet hours for user %s", settings.user_id)
            return {}

        # Check event preferences
        prefs = settings.event_preferences or {}
        if not prefs.get(event_type, True):
            logger.info("Notification suppressed: event %s disabled for user %s", event_type, settings.user_id)
            return {}

        results: dict[str, bool] = {}

        if settings.email_enabled and settings.email_address:
            success, _ = await self._send_email(settings.email_address, title, message)
            results["email"] = success

        if settings.telegram_enabled and settings.telegram_chat_id:
            success, _ = await self._send_telegram(settings.telegram_chat_id, title, message)
            results["telegram"] = success

        if settings.discord_enabled and settings.discord_webhook_url:
            success, _ = await self._send_discord(settings.discord_webhook_url, title, message)
            results["discord"] = success

        if settings.webhook_enabled and settings.webhook_url:
            success, _ = await self._send_webhook(settings.webhook_url, event_type, title, message, metadata)
            results["webhook"] = success

        return results

    async def send_test(self, channel: str, settings: NotificationSettings) -> tuple[bool, str | None]:
        """Send a test notification to a specific channel."""
        title = "CloudGentic Gateway Test"
        message = "This is a test notification from CloudGentic Gateway. If you see this, notifications are working."

        if channel == "email":
            return await self._send_email(settings.email_address, title, message)
        elif channel == "telegram":
            return await self._send_telegram(settings.telegram_chat_id, title, message)
        elif channel == "discord":
            return await self._send_discord(settings.discord_webhook_url, title, message)
        elif channel == "webhook":
            return await self._send_webhook(settings.webhook_url, "test", title, message)

        return False, f"Unknown channel: {channel}"

    def _in_quiet_hours(self, settings: NotificationSettings) -> bool:
        """Check if the current time falls within configured quiet hours."""
        quiet = settings.quiet_hours or {}
        if not quiet.get("enabled", False):
            return False

        try:
            from zoneinfo import ZoneInfo
            tz_name = quiet.get("timezone", "UTC")
            try:
                tz = ZoneInfo(tz_name)
            except (KeyError, Exception):
                tz = timezone.utc

            now = datetime.now(tz)
            current_hour = now.hour
            start = quiet.get("start_hour", 22)
            end = quiet.get("end_hour", 8)

            if start > end:
                return current_hour >= start or current_hour < end
            else:
                return start <= current_hour < end
        except Exception:
            return False

    async def _send_email(self, address: str, title: str, message: str) -> tuple[bool, str | None]:
        """Send email notification. Placeholder — integrate with SMTP or email service."""
        # In production, this would use aiosmtplib or an email service API
        logger.info("Email notification to %s: %s", address, title)
        return True, "Email notification queued (SMTP integration pending)"

    async def _send_telegram(self, chat_id: str, title: str, message: str) -> tuple[bool, str | None]:
        """Send Telegram notification via Bot API."""
        # Requires TELEGRAM_BOT_TOKEN in settings for production use
        logger.info("Telegram notification to chat %s: %s", chat_id, title)
        return True, "Telegram notification queued (bot token integration pending)"

    async def _send_discord(self, webhook_url: str, title: str, message: str) -> tuple[bool, str | None]:
        """Send Discord notification via webhook."""
        try:
            payload = {
                "embeds": [
                    {
                        "title": title,
                        "description": message,
                        "color": 5814783,  # CloudGentic blue
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                ]
            }
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(webhook_url, json=payload)
                if response.status_code in (200, 204):
                    return True, None
                return False, f"Discord returned status {response.status_code}"
        except Exception as e:
            logger.error("Discord notification failed: %s", e)
            return False, str(e)

    async def _send_webhook(
        self, url: str, event_type: str, title: str, message: str, metadata: dict | None = None
    ) -> tuple[bool, str | None]:
        """Send generic webhook notification."""
        try:
            payload = {
                "event_type": event_type,
                "title": title,
                "message": message,
                "metadata": metadata or {},
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "cloudgentic-gateway",
            }
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(url, json=payload)
                if 200 <= response.status_code < 300:
                    return True, None
                return False, f"Webhook returned status {response.status_code}"
        except Exception as e:
            logger.error("Webhook notification failed: %s", e)
            return False, str(e)
