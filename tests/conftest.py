"""
Pytest configuration and shared fixtures for service-agnostic booking tests.
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
def sample_service():
    """Create a sample service provider object (works with any service: salon, doctor, restaurant, etc.)."""
    return Restaurant(
        name="StyleCuts Hair Salon",
        phone="+1-555-0100",
        address="123 Main St, Boston, MA",
        rating=4.2,
    )


@pytest.fixture
def sample_state_with_service(sample_state, sample_service):
    """Create state with selected service provider."""
    sample_state.selected_restaurant = sample_service
    sample_state.party_size = 2
    sample_state.requested_date = "2024-11-22"
    sample_state.requested_time = "15:00"  # 3 PM - typical appointment time
    return sample_state


# Backward compatibility aliases (deprecated - use new names above)
@pytest.fixture
def sample_restaurant(sample_service):
    """Deprecated: Use sample_service instead."""
    return sample_service


@pytest.fixture
def sample_state_with_restaurant(sample_state_with_service):
    """Deprecated: Use sample_state_with_service instead."""
    return sample_state_with_service
