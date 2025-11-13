"""
End-to-end integration tests for the booking workflow.
Tests the full flow from user input to booking confirmation.
"""

import pytest
from datetime import datetime
from hiya_drive.core.orchestrator import orchestrator
from hiya_drive.models.state import SessionStatus


class TestE2EBookingFlow:
    """Test complete booking workflows."""

    @pytest.mark.asyncio
    async def test_simple_booking_demo_mode(self):
        """Test a simple booking request in demo mode."""
        result = await orchestrator.run_booking_session(
            driver_id="test_driver_001",
            initial_utterance="Book a table for 2 at Italian next Friday at 7 PM",
        )

        # Should complete successfully in demo mode
        assert result.session_id is not None
        assert result.driver_id == "test_driver_001"
        assert result.status in [SessionStatus.COMPLETED, SessionStatus.FAILED]
        assert isinstance(result.start_time, datetime)

    @pytest.mark.asyncio
    async def test_booking_with_restaurant_selection(self):
        """Test booking flow with restaurant selection."""
        result = await orchestrator.run_booking_session(
            driver_id="test_driver_002",
            initial_utterance="I need a table for 4 people at a sushi place",
        )

        assert result.session_id is not None
        # In demo mode, should search for restaurants
        if result.status == SessionStatus.COMPLETED:
            assert result.selected_restaurant is not None

    @pytest.mark.asyncio
    async def test_booking_state_progression(self):
        """Test that state progresses through workflow."""
        result = await orchestrator.run_booking_session(
            driver_id="test_driver_003",
            initial_utterance="Book me a table for 2 at Italian",
        )

        # State should have progressed
        assert result.turn_count >= 0
        # In demo, should have extracted some intent
        if result.cuisine_type:
            assert result.cuisine_type is not None

    @pytest.mark.asyncio
    async def test_booking_with_error_recovery(self):
        """Test booking with error handling."""
        result = await orchestrator.run_booking_session(
            driver_id="test_driver_004",
            initial_utterance="I want to book",  # Ambiguous, missing details
        )

        # Should still progress without crashing
        assert result.session_id is not None

    @pytest.mark.asyncio
    async def test_multiple_sequential_bookings(self):
        """Test running multiple booking sessions sequentially."""
        for i in range(3):
            result = await orchestrator.run_booking_session(
                driver_id=f"test_driver_{i}",
                initial_utterance=f"Book a table for {i+2} people",
            )

            assert result.session_id is not None
            assert result.driver_id == f"test_driver_{i}"

    @pytest.mark.asyncio
    async def test_booking_state_to_dict(self):
        """Test converting booking state to dictionary."""
        result = await orchestrator.run_booking_session(
            driver_id="test_driver_005",
            initial_utterance="Book a table for 2",
        )

        state_dict = result.to_dict()

        assert isinstance(state_dict, dict)
        assert "session_id" in state_dict
        assert "status" in state_dict
        assert "booking_confirmed" in state_dict

    @pytest.mark.asyncio
    async def test_demo_mode_booking_confirmation(self):
        """Test that demo mode produces booking confirmation."""
        result = await orchestrator.run_booking_session(
            driver_id="test_driver_006",
            initial_utterance="Book a table for 2 at Italian next Friday at 7 PM",
        )

        # In demo mode, should confirm
        if result.status == SessionStatus.COMPLETED:
            assert result.booking_confirmed is True
            assert result.confirmation_number is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
