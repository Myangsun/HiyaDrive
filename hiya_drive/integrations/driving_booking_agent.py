"""
Driving Booking Agent – Demonstration

This module provides a minimal proof‑of‑concept (POC) implementation of the
voice assistant booking agent tailored for drivers.  It simulates the
conversation flow, integrates tool‑calling for date calculation, and
illustrates basic error handling for ambiguous input.  It does not depend on
external network services or API keys; instead, it uses simple Python
functions to represent external tool invocations (e.g., calculating the next
Friday).  The purpose is to demonstrate how the conversational agent would
process user requests, call tools, handle errors and confirm a reservation
without requiring the driver to look at or touch a device.

Key Features:
  • Parses user intent from a natural language request
  • Uses a tool function to compute the date for "next Friday" if not
    explicitly provided
  • Checks calendar availability (mocked)
  • Finds a business (mocked)
  • Simulates a concise conversation with a restaurant receptionist
  • Handles invalid time input by prompting the user for clarification
  • Demonstrates short prompts and summary suitable for in‑vehicle use
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional


def get_next_weekday(target_weekday: int) -> str:
    """Return the date of the next target_weekday (0=Monday..6=Sunday).

    If today is Friday and target_weekday is Friday, it returns a week ahead.
    The returned string is in ISO format (YYYY‑MM‑DD).
    """
    today = datetime.now().date()
    days_ahead = (target_weekday - today.weekday() + 7) % 7
    if days_ahead == 0:
        days_ahead = 7
    next_date = today + timedelta(days=days_ahead)
    return next_date.isoformat()


@dataclass
class DrivingBookingState:
    """State for the driving booking conversation."""
    user_name: str
    user_phone: str
    cuisine_type: str
    location: str
    party_size: int
    requested_date: Optional[str] = None
    requested_time: Optional[str] = None
    # Computed fields
    business_name: Optional[str] = None
    business_phone: Optional[str] = None
    confirmation_number: Optional[str] = None
    booking_confirmed: bool = False
    errors: List[str] = field(default_factory=list)


class DrivingBookingAgent:
    """A simple booking agent implementation for the driving scenario."""

    def parse_intent(self, state: DrivingBookingState, user_request: str) -> None:
        """Extract basic intent from the user request.

        This function does not perform full NLP parsing; it looks for
        keywords in the string.  If the date is not specified, it calls
        the get_next_weekday tool to compute next Friday.
        """
        tokens = user_request.lower().split()
        # Detect cuisine type
        if "italian" in tokens:
            state.cuisine_type = "Italian"
        if "sushi" in tokens:
            state.cuisine_type = "Sushi"
        # Detect number of people
        for token in tokens:
            if token.isdigit():
                state.party_size = int(token)
                break
        # Detect date keywords
        if any(word in tokens for word in ["friday", "next friday"]):
            # Use tool to compute next Friday
            state.requested_date = get_next_weekday(4)  # Friday = 4
        # Detect time (simple pattern like 7pm or 19:00)
        for token in tokens:
            if token.endswith("pm") or token.endswith("am"):
                time_str = token[:-2]
                # Append :00 if needed (e.g., 7pm -> 19:00)
                try:
                    hour = int(time_str)
                    if token.endswith("pm") and hour != 12:
                        hour += 12
                    state.requested_time = f"{hour:02d}:00"
                except ValueError:
                    pass
        # Fallback time if none found
        if state.requested_time is None:
            state.requested_time = "19:00"

    def check_calendar(self, state: DrivingBookingState) -> bool:
        """Mock calendar availability check.

        Always returns True for availability in this demonstration.
        """
        return True

    def find_business(self, state: DrivingBookingState) -> None:
        """Mock business search based on cuisine and location."""
        # In a real implementation this would call an API like Google Places.
        if state.cuisine_type == "Italian":
            state.business_name = "Olive Garden"
            state.business_phone = "+1-555-0100"
        elif state.cuisine_type == "Sushi":
            state.business_name = "Sushi House"
            state.business_phone = "+1-555-0200"
        else:
            state.business_name = "Local Eatery"
            state.business_phone = "+1-555-0300"

    def converse(self, state: DrivingBookingState) -> None:
        """Simulate a concise conversation with the restaurant receptionist."""
        print(f"\nAgent (to restaurant): Hello, I'd like to reserve a table for {state.party_size} "
              f"on {state.requested_date} at {state.requested_time}.")
        print("Receptionist: Let me check… Yes, we have availability. Can I have the name?")
        print(f"Agent: {state.user_name}.")
        print("Receptionist: And a contact number?")
        print(f"Agent: {state.user_phone}.")
        print("Receptionist: Great, your reservation is confirmed. Your confirmation number is 4892.")
        state.confirmation_number = "4892"
        state.booking_confirmed = True

    def handle_ambiguous_time(self, user_request: str) -> Optional[str]:
        """Detect invalid time formats and prompt for clarification."""
        tokens = user_request.lower().split()
        for token in tokens:
            if token.endswith("pm") or token.endswith("am"):
                time_str = token[:-2]
                try:
                    hour = int(time_str)
                    if hour < 1 or hour > 12:
                        return ("I'm sorry, I didn't catch the time. "
                                "Could you repeat the time in the format like '7 pm'?")
                except ValueError:
                    return ("I'm sorry, I didn't catch the time. "
                            "Could you repeat the time in the format like '7 pm'?")
        return None

    def run_demo(self) -> None:
        """Run a demonstration of the driving booking agent."""
        print("=== Driving Booking Agent Demo ===")
        # Sample user request with ambiguous time
        user_request = "Hey assistant, book a table for 3 at an Italian place next Friday at 25pm"
        state = DrivingBookingState(
            user_name="Alex",
            user_phone="555-0123",
            cuisine_type="Italian",
            location="Boston",
            party_size=3
        )
        # Handle ambiguous time
        error_msg = self.handle_ambiguous_time(user_request)
        if error_msg:
            print(f"Agent: {error_msg}")
            # Driver repeats a correct time
            user_request = "Book a table for 3 at an Italian place next Friday at 7pm"
        # Parse intent
        self.parse_intent(state, user_request)
        # Check calendar
        available = self.check_calendar(state)
        if not available:
            print("Agent: It looks like you have a conflict at that time. Would you like to try another time?")
            return
        # Find business
        self.find_business(state)
        print(f"Agent: I'll call {state.business_name} now.")
        # Simulate conversation
        self.converse(state)
        # Confirm booking
        if state.booking_confirmed:
            print(f"\nAgent (to driver): Your reservation at {state.business_name} "
                  f"for {state.party_size} on {state.requested_date} at {state.requested_time} "
                  f"is confirmed. Your confirmation number is {state.confirmation_number}. Have a safe drive!")
        print("=== Demo complete ===")


if __name__ == "__main__":
    agent = DrivingBookingAgent()
    agent.run_demo()