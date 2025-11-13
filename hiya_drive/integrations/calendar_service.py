"""
Google Calendar integration for checking driver availability.
"""

from datetime import datetime, timedelta
from typing import Optional
from pathlib import Path

import dateparser
import pytz

from hiya_drive.config.settings import settings
from hiya_drive.utils.logger import logger


class CalendarService:
    """Integrates with Google Calendar API."""

    def __init__(self):
        """Initialize Google Calendar client."""
        self.service = None
        self.init_error = None
        # Use calendar ID from settings (default: "primary")
        self.calendar_id = settings.google_calendar_id
        self._init_calendar()

    def _init_calendar(self):
        """Initialize Google Calendar service."""
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.service_account import Credentials
            from google.auth.exceptions import GoogleAuthError
            import googleapiclient.discovery

            if not settings.google_calendar_credentials_path:
                logger.error(
                    "GOOGLE_CALENDAR_CREDENTIALS_PATH not set! Please configure your Google Calendar credentials to use calendar availability checks."
                )
                self.init_error = "Calendar credentials not configured (GOOGLE_CALENDAR_CREDENTIALS_PATH not set)"
                return

            creds_path = Path(settings.google_calendar_credentials_path)
            if not creds_path.exists():
                logger.error(f"Calendar credentials file not found: {creds_path}")
                self.init_error = f"Calendar credentials file not found: {creds_path}"
                return

            # Load service account credentials with write access to create events
            credentials = Credentials.from_service_account_file(
                creds_path, scopes=["https://www.googleapis.com/auth/calendar"]
            )

            self.service = googleapiclient.discovery.build(
                "calendar", "v3", credentials=credentials
            )
            logger.info("Google Calendar service initialized successfully")
            self.init_error = None

        except ImportError:
            logger.error(
                "Google client libraries not installed. Install: pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client"
            )
            self.init_error = "Google client libraries not installed"
        except Exception as e:
            logger.error(f"Failed to initialize Google Calendar: {e}")
            self.init_error = f"Failed to initialize Google Calendar: {str(e)}"

    async def is_available(self, start_time: str, duration_minutes: int = 120) -> bool:
        """
        Check if driver is available at given time.

        Args:
            start_time: DateTime string (e.g., "next Friday at 7 PM")
            duration_minutes: Duration to check

        Returns:
            True if available, False if busy/error
        """
        if not self.service:
            error_msg = self.init_error or "Calendar service not initialized"
            logger.error(f"Cannot check calendar: {error_msg}")
            raise Exception(error_msg)

        try:
            logger.info(f"Checking calendar availability for: {start_time}")

            # Parse the natural language time string with proper settings
            now_utc = datetime.now(pytz.utc)
            parse_settings = {
                "PREFER_DATES_FROM": "current_period",
                "RELATIVE_BASE": now_utc,
                "RETURN_AS_TIMEZONE_AWARE": True,
                "TIMEZONE": "UTC",
            }

            # Try parsing the original string first
            parsed_datetime = dateparser.parse(start_time, settings=parse_settings)

            # If that fails, try preprocessing to remove "next" prefix which dateparser struggles with
            if not parsed_datetime:
                preprocessed = start_time.lower().replace("next ", "").strip()
                if preprocessed != start_time.lower():
                    logger.debug(
                        f"Retrying parse with preprocessed string: {preprocessed}"
                    )
                    parsed_datetime = dateparser.parse(
                        preprocessed, settings=parse_settings
                    )

            if not parsed_datetime:
                logger.error(f"Could not parse time string: {start_time}")
                raise ValueError(f"Invalid time format: {start_time}")

            # Ensure timezone-aware (should already be from dateparser)
            if parsed_datetime.tzinfo is None:
                parsed_datetime = pytz.utc.localize(parsed_datetime)

            # If the original string contained "next" and parsed time is in the past, advance by 7 days
            if "next" in start_time.lower():
                while parsed_datetime <= now_utc:
                    parsed_datetime = parsed_datetime + timedelta(days=7)
                    logger.debug(
                        f"Advancing date by 7 days due to 'next' keyword: {parsed_datetime}"
                    )

            # Convert to RFC 3339 format for API call
            start_dt = parsed_datetime.isoformat()
            end_dt = (parsed_datetime + timedelta(minutes=duration_minutes)).isoformat()

            logger.debug(f"Querying calendar events from {start_dt} to {end_dt}")

            # Query calendar events for the specified time range
            events_result = (
                self.service.events()
                .list(
                    calendarId=self.calendar_id,
                    timeMin=start_dt,
                    timeMax=end_dt,
                    singleEvents=True,
                    orderBy="startTime",
                    showDeleted=False,
                )
                .execute()
            )

            events = events_result.get("items", [])

            if events:
                # If there are any events, driver is not available
                logger.info(
                    f"Found {len(events)} conflicting event(s) during requested time"
                )
                for event in events:
                    event_title = event.get("summary", "Untitled")
                    event_start = event.get("start", {}).get(
                        "dateTime", event.get("start", {}).get("date")
                    )
                    logger.debug(f"  - {event_title} at {event_start}")
                return False
            else:
                logger.info("No conflicting events found - driver is available")
                return True

        except ValueError as e:
            logger.error(f"Invalid input to calendar check: {e}")
            raise
        except Exception as e:
            logger.error(f"Error checking calendar: {e}")
            raise

    async def add_reservation_event(
        self,
        restaurant_name: str,
        reservation_time: str,
        party_size: int,
        duration_minutes: int = 120,
        confirmation_number: str = None,
    ) -> bool:
        """
        Add a restaurant reservation to Google Calendar.

        Args:
            restaurant_name: Name of the restaurant
            reservation_time: DateTime string (e.g., "next Friday at 7 PM")
            party_size: Number of people
            duration_minutes: Duration of reservation
            confirmation_number: Optional confirmation number

        Returns:
            True if event was created, False if failed
        """
        if not self.service:
            error_msg = self.init_error or "Calendar service not initialized"
            logger.error(f"Cannot add to calendar: {error_msg}")
            raise Exception(error_msg)

        try:
            logger.info(
                f"Adding reservation to calendar: {restaurant_name} at {reservation_time}"
            )

            # Parse the reservation time
            now_utc = datetime.now(pytz.utc)
            parse_settings = {
                "PREFER_DATES_FROM": "current_period",
                "RELATIVE_BASE": now_utc,
                "RETURN_AS_TIMEZONE_AWARE": True,
                "TIMEZONE": "UTC",
            }

            parsed_datetime = dateparser.parse(
                reservation_time, settings=parse_settings
            )

            # If that fails, try preprocessing
            if not parsed_datetime:
                preprocessed = reservation_time.lower().replace("next ", "").strip()
                if preprocessed != reservation_time.lower():
                    logger.debug(f"Retrying parse with preprocessed: {preprocessed}")
                    parsed_datetime = dateparser.parse(
                        preprocessed, settings=parse_settings
                    )

            if not parsed_datetime:
                logger.error(f"Could not parse reservation time: {reservation_time}")
                raise ValueError(f"Invalid time format: {reservation_time}")

            # Ensure timezone-aware
            if parsed_datetime.tzinfo is None:
                parsed_datetime = pytz.utc.localize(parsed_datetime)

            # Handle "next" keyword
            if "next" in reservation_time.lower():
                while parsed_datetime <= now_utc:
                    parsed_datetime = parsed_datetime + timedelta(days=7)

            start_time = parsed_datetime
            end_time = parsed_datetime + timedelta(minutes=duration_minutes)

            # Create the calendar event
            event = {
                "summary": f"Dinner at {restaurant_name}",
                "description": f"Restaurant reservation for {party_size} people"
                + (
                    f"\nConfirmation #: {confirmation_number}"
                    if confirmation_number
                    else ""
                ),
                "start": {
                    "dateTime": start_time.isoformat(),
                    "timeZone": "UTC",
                },
                "end": {
                    "dateTime": end_time.isoformat(),
                    "timeZone": "UTC",
                },
                "location": restaurant_name,
            }

            # Insert the event into the calendar
            created_event = (
                self.service.events()
                .insert(calendarId=self.calendar_id, body=event)
                .execute()
            )

            event_id = created_event.get("id")
            event_link = created_event.get("htmlLink")

            logger.info(f"✓ Reservation added to calendar! Event ID: {event_id}")
            logger.info(f"  Calendar link: {event_link}")

            return True

        except ValueError as e:
            logger.error(f"Invalid reservation details: {e}")
            return False
        except Exception as e:
            logger.error(f"Error adding reservation to calendar: {e}")
            return False


# Global calendar service instance
calendar_service = CalendarService()
