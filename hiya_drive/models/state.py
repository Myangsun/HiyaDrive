"""
State management for driving booking sessions.
Defines the DrivingBookingState used by LangGraph orchestration.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class SessionStatus(str, Enum):
    """Session lifecycle status."""

    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class RoadComplexity(str, Enum):
    """Current road conditions."""

    STRAIGHT = "straight"
    CURVY = "curvy"
    INTERSECTION = "intersection"
    UNKNOWN = "unknown"


@dataclass
class Restaurant:
    """Restaurant information from Google Places."""

    name: str
    phone: str
    address: str
    rating: float = 0.0
    opening_hours: Optional[str] = None
    url: Optional[str] = None


@dataclass
class DrivingBookingState:
    """
    Complete state for a booking session.
    This is the state object passed through LangGraph nodes.
    """

    # =========================================================================
    # Session Metadata
    # =========================================================================

    session_id: str
    driver_id: str
    start_time: datetime
    status: SessionStatus = SessionStatus.ACTIVE

    # =========================================================================
    # User Input Extraction
    # =========================================================================

    party_size: Optional[int] = None
    requested_date: Optional[str] = None  # ISO format: "2024-11-15"
    requested_time: Optional[str] = None  # HH:MM format: "19:00"
    cuisine_type: Optional[str] = None
    location: Optional[str] = None

    # =========================================================================
    # Retrieved Data
    # =========================================================================

    driver_location: Optional[Dict[str, float]] = None  # {"lat": X, "lon": Y}
    driver_calendar_free: bool = False
    restaurant_candidates: List[Restaurant] = field(default_factory=list)
    selected_restaurant: Optional[Restaurant] = None

    # =========================================================================
    # Confirmation & Booking
    # =========================================================================

    confirmation_number: Optional[str] = None
    booking_confirmed: bool = False
    call_opening_script: Optional[str] = None

    # =========================================================================
    # Error Tracking
    # =========================================================================

    errors: List[str] = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 2
    last_error: Optional[str] = None

    # =========================================================================
    # Driving Context (from vehicle)
    # =========================================================================

    current_speed_kmh: Optional[float] = None
    road_complexity: RoadComplexity = RoadComplexity.UNKNOWN
    safe_to_speak: bool = True
    last_prompt_time: Optional[datetime] = None

    # =========================================================================
    # Conversation Tracking
    # =========================================================================

    turn_count: int = 0
    last_utterance: Optional[str] = None
    messages: List[Dict[str, str]] = field(default_factory=list)
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)

    # =========================================================================
    # Twilio Call State
    # =========================================================================

    twilio_call_sid: Optional[str] = None
    call_connected: bool = False
    call_duration_seconds: int = 0

    # =========================================================================
    # Metadata
    # =========================================================================

    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_error(self, error: str) -> None:
        """Add an error message to the state."""
        self.errors.append(error)
        self.last_error = error

    def add_message(self, role: str, content: str) -> None:
        """Add a message to conversation history."""
        self.messages.append({"role": role, "content": content})

    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0

    def can_retry(self) -> bool:
        """Check if we can retry the operation."""
        return self.retry_count < self.max_retries

    def increment_retry(self) -> None:
        """Increment retry counter."""
        self.retry_count += 1

    def increment_turn(self) -> None:
        """Increment conversation turn counter."""
        self.turn_count += 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "driver_id": self.driver_id,
            "start_time": self.start_time.isoformat(),
            "status": self.status.value,
            "party_size": self.party_size,
            "requested_date": self.requested_date,
            "requested_time": self.requested_time,
            "cuisine_type": self.cuisine_type,
            "location": self.location,
            "selected_restaurant": (
                {
                    "name": self.selected_restaurant.name,
                    "phone": self.selected_restaurant.phone,
                    "address": self.selected_restaurant.address,
                }
                if self.selected_restaurant
                else None
            ),
            "confirmation_number": self.confirmation_number,
            "booking_confirmed": self.booking_confirmed,
            "errors": self.errors,
            "turn_count": self.turn_count,
        }

    def __repr__(self) -> str:
        """String representation of state."""
        return (
            f"DrivingBookingState("
            f"session_id={self.session_id}, "
            f"status={self.status.value}, "
            f"party_size={self.party_size}, "
            f"date={self.requested_date}, "
            f"time={self.requested_time}, "
            f"booking_confirmed={self.booking_confirmed}"
            f")"
        )
