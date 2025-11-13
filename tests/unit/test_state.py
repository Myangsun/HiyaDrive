"""
Unit tests for state management and data models.
"""

import pytest
from datetime import datetime
from hiya_drive.models.state import (
    DrivingBookingState,
    SessionStatus,
    RoadComplexity,
    Restaurant,
)


class TestRestaurant:
    """Test Restaurant data model."""

    def test_restaurant_creation(self):
        """Test creating a restaurant object."""
        restaurant = Restaurant(
            name="Test Restaurant",
            phone="+1-555-0100",
            address="123 Main St",
            rating=4.5,
        )

        assert restaurant.name == "Test Restaurant"
        assert restaurant.phone == "+1-555-0100"
        assert restaurant.rating == 4.5


class TestDrivingBookingState:
    """Test DrivingBookingState."""

    def test_initial_state(self, sample_state):
        """Test state initialization."""
        assert sample_state.session_id == "test_session_001"
        assert sample_state.driver_id == "test_driver_001"
        assert sample_state.status == SessionStatus.ACTIVE
        assert sample_state.party_size is None
        assert sample_state.booking_confirmed is False
        assert sample_state.errors == []

    def test_add_error(self, sample_state):
        """Test adding errors to state."""
        sample_state.add_error("Test error")

        assert "Test error" in sample_state.errors
        assert sample_state.last_error == "Test error"
        assert sample_state.has_errors() is True

    def test_multiple_errors(self, sample_state):
        """Test adding multiple errors."""
        sample_state.add_error("Error 1")
        sample_state.add_error("Error 2")

        assert len(sample_state.errors) == 2
        assert sample_state.last_error == "Error 2"

    def test_add_message(self, sample_state):
        """Test adding messages to conversation history."""
        sample_state.add_message("user", "Hello")
        sample_state.add_message("assistant", "Hi there")

        assert len(sample_state.messages) == 2
        assert sample_state.messages[0] == {"role": "user", "content": "Hello"}
        assert sample_state.messages[1] == {"role": "assistant", "content": "Hi there"}

    def test_can_retry(self, sample_state):
        """Test retry logic."""
        assert sample_state.can_retry() is True

        sample_state.retry_count = 2
        sample_state.max_retries = 2
        assert sample_state.can_retry() is False

    def test_increment_retry(self, sample_state):
        """Test incrementing retry counter."""
        assert sample_state.retry_count == 0

        sample_state.increment_retry()
        assert sample_state.retry_count == 1

        sample_state.increment_retry()
        assert sample_state.retry_count == 2

    def test_increment_turn(self, sample_state):
        """Test incrementing conversation turn."""
        assert sample_state.turn_count == 0

        sample_state.increment_turn()
        assert sample_state.turn_count == 1

    def test_to_dict(self, sample_state):
        """Test converting state to dictionary."""
        sample_state.party_size = 2
        sample_state.cuisine_type = "Italian"
        sample_state.booking_confirmed = True

        state_dict = sample_state.to_dict()

        assert state_dict["session_id"] == sample_state.session_id
        assert state_dict["party_size"] == 2
        assert state_dict["cuisine_type"] == "Italian"
        assert state_dict["booking_confirmed"] is True

    def test_state_repr(self, sample_state):
        """Test string representation of state."""
        sample_state.party_size = 2
        sample_state.requested_date = "2024-11-22"

        repr_str = repr(sample_state)
        assert "test_session_001" in repr_str
        assert "party_size=2" in repr_str

    def test_with_restaurant(self, sample_state_with_restaurant):
        """Test state with restaurant selected."""
        assert sample_state_with_restaurant.selected_restaurant.name == "Olive Garden"
        assert sample_state_with_restaurant.party_size == 2
        assert sample_state_with_restaurant.requested_date == "2024-11-22"
        assert sample_state_with_restaurant.requested_time == "19:00"

    def test_status_transitions(self, sample_state):
        """Test status transitions."""
        assert sample_state.status == SessionStatus.ACTIVE

        sample_state.status = SessionStatus.COMPLETED
        assert sample_state.status == SessionStatus.COMPLETED

        sample_state.status = SessionStatus.FAILED
        assert sample_state.status == SessionStatus.FAILED

    def test_road_complexity_enum(self):
        """Test RoadComplexity enum."""
        assert RoadComplexity.STRAIGHT.value == "straight"
        assert RoadComplexity.CURVY.value == "curvy"
        assert RoadComplexity.INTERSECTION.value == "intersection"

    def test_session_status_enum(self):
        """Test SessionStatus enum."""
        assert SessionStatus.ACTIVE.value == "active"
        assert SessionStatus.COMPLETED.value == "completed"
        assert SessionStatus.FAILED.value == "failed"
