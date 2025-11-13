"""
Pytest configuration and shared fixtures.
"""

import pytest
import asyncio
from datetime import datetime
from hiya_drive.models.state import DrivingBookingState, SessionStatus, Restaurant


@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_state():
    """Create a sample booking state for testing."""
    return DrivingBookingState(
        session_id="test_session_001",
        driver_id="test_driver_001",
        start_time=datetime.now(),
        status=SessionStatus.ACTIVE,
        last_utterance="Book a table for 2 at Italian next Friday at 7 PM",
    )


@pytest.fixture
def sample_restaurant():
    """Create a sample restaurant object."""
    return Restaurant(
        name="Olive Garden",
        phone="+1-555-0100",
        address="123 Main St, Boston, MA",
        rating=4.2,
    )


@pytest.fixture
def sample_state_with_restaurant(sample_state, sample_restaurant):
    """Create state with selected restaurant."""
    sample_state.selected_restaurant = sample_restaurant
    sample_state.party_size = 2
    sample_state.requested_date = "2024-11-22"
    sample_state.requested_time = "19:00"
    return sample_state
