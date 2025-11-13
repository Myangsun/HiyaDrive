"""
Google Calendar integration for checking driver availability.
"""

from datetime import datetime, timedelta
from typing import Optional
from pathlib import Path

from hiya_drive.config.settings import settings
from hiya_drive.utils.logger import logger


class CalendarService:
    """Integrates with Google Calendar API."""

    def __init__(self):
        """Initialize Google Calendar client."""
        self.service = None
        self._init_calendar()

    def _init_calendar(self):
        """Initialize Google Calendar service."""
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.service_account import Credentials
            from google.auth.exceptions import GoogleAuthError
            import googleapiclient.discovery

            if not settings.google_calendar_credentials_path:
                logger.warning("GOOGLE_CALENDAR_CREDENTIALS_PATH not set, calendar checks will always be available")
                return

            creds_path = Path(settings.google_calendar_credentials_path)
            if not creds_path.exists():
                logger.warning(f"Calendar credentials file not found: {creds_path}")
                return

            # Load service account credentials
            credentials = Credentials.from_service_account_file(
                creds_path,
                scopes=["https://www.googleapis.com/auth/calendar.readonly"]
            )

            self.service = googleapiclient.discovery.build(
                "calendar", "v3", credentials=credentials
            )
            logger.info("Google Calendar service initialized successfully")

        except ImportError:
            logger.warning("Google client libraries not installed. Install: pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client")
        except Exception as e:
            logger.warning(f"Failed to initialize Google Calendar: {e}")

    async def is_available(
        self,
        start_time: str,
        duration_minutes: int = 120
    ) -> bool:
        """
        Check if driver is available at given time.

        Args:
            start_time: DateTime string (e.g., "next Friday at 7 PM")
            duration_minutes: Duration to check

        Returns:
            True if available, False if busy
        """
        if not self.service:
            logger.debug("Calendar service not available, assuming availability")
            return True

        try:
            # Parse the time string (simplified - in production use dateparser library)
            # For now, assume availability
            logger.info(f"Checking calendar availability for: {start_time}")

            # TODO: Implement proper time parsing and calendar event checking
            # Query calendar.events.list() with timeMin and timeMax
            # Check if any events conflict with requested time

            return True

        except Exception as e:
            logger.error(f"Error checking calendar: {e}")
            # Default to available if error occurs
            return True


# Global calendar service instance
calendar_service = CalendarService()
