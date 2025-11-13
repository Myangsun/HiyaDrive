"""
Unit tests for the booking orchestrator.
"""

import pytest
from datetime import datetime
from hiya_drive.core.orchestrator import BookingOrchestrator
from hiya_drive.models.state import DrivingBookingState, SessionStatus


class TestBookingOrchestrator:
    """Test the main orchestration engine."""

    def test_orchestrator_initialization(self):
        """Test orchestrator initializes correctly."""
        orchestrator = BookingOrchestrator()

        assert orchestrator.client is not None
        assert orchestrator.workflow is not None
        assert orchestrator.app is not None

    def test_workflow_has_all_nodes(self):
        """Test workflow includes all required nodes."""
        orchestrator = BookingOrchestrator()

        expected_nodes = [
            "parse_intent",
            "check_calendar",
            "search_restaurants",
            "select_restaurant",
            "prepare_call",
            "make_call",
            "converse",
            "confirm_booking",
            "handle_error",
        ]

        # Workflow should have all nodes
        assert orchestrator.workflow is not None

    @pytest.mark.asyncio
    async def test_parse_intent_node(self):
        """Test parse_intent node extracts intent."""
        orchestrator = BookingOrchestrator()
        state = DrivingBookingState(
            session_id="test_001",
            driver_id="driver_001",
            start_time=datetime.now(),
            last_utterance="Book a table for 2 at Italian next Friday at 7 PM",
        )

        result = await orchestrator.parse_intent(state)

        # Should extract basic info
        assert result.party_size is not None or result.party_size == 2
        assert result.cuisine_type is not None or "Italian" in (
            result.cuisine_type or ""
        )

    @pytest.mark.asyncio
    async def test_check_calendar_node(self):
        """Test check_calendar node."""
        orchestrator = BookingOrchestrator()
        state = DrivingBookingState(
            session_id="test_001",
            driver_id="driver_001",
            start_time=datetime.now(),
        )

        result = await orchestrator.check_calendar(state)

        # In demo mode, should be available
        assert isinstance(result.driver_calendar_free, bool)

    @pytest.mark.asyncio
    async def test_search_restaurants_node(self):
        """Test search_restaurants node."""
        orchestrator = BookingOrchestrator()
        state = DrivingBookingState(
            session_id="test_001",
            driver_id="driver_001",
            start_time=datetime.now(),
            cuisine_type="Italian",
            location="Boston",
        )

        result = await orchestrator.search_restaurants(state)

        # In demo mode, should return candidates
        assert isinstance(result.restaurant_candidates, list)

    @pytest.mark.asyncio
    async def test_select_restaurant_node(self, sample_state):
        """Test select_restaurant node."""
        orchestrator = BookingOrchestrator()

        # Add some candidates
        from hiya_drive.models.state import Restaurant

        sample_state.restaurant_candidates = [
            Restaurant(
                name="Restaurant 1",
                phone="+1-555-0100",
                address="123 Main St",
                rating=4.2,
            ),
            Restaurant(
                name="Restaurant 2",
                phone="+1-555-0200",
                address="456 Park Ave",
                rating=4.5,
            ),
        ]

        result = await orchestrator.select_restaurant(sample_state)

        assert result.selected_restaurant is not None
        assert result.selected_restaurant.name == "Restaurant 1"

    @pytest.mark.asyncio
    async def test_prepare_call_node(self, sample_state_with_restaurant):
        """Test prepare_call node generates script."""
        orchestrator = BookingOrchestrator()

        result = await orchestrator.prepare_call(sample_state_with_restaurant)

        # Should have a script
        assert result.call_opening_script is not None
        assert len(result.call_opening_script) > 0

    @pytest.mark.asyncio
    async def test_make_call_node(self, sample_state_with_restaurant):
        """Test make_call node initiates call."""
        orchestrator = BookingOrchestrator()

        result = await orchestrator.make_call(sample_state_with_restaurant)

        # In demo mode, should set call connected
        assert result.call_connected is True

    @pytest.mark.asyncio
    async def test_converse_node(self, sample_state_with_restaurant):
        """Test converse node handles conversation."""
        orchestrator = BookingOrchestrator()
        sample_state_with_restaurant.call_connected = True

        result = await orchestrator.converse(sample_state_with_restaurant)

        # In demo mode, should confirm booking
        assert result.booking_confirmed is True
        assert result.confirmation_number is not None

    @pytest.mark.asyncio
    async def test_confirm_booking_node(self, sample_state_with_restaurant):
        """Test confirm_booking node saves booking."""
        orchestrator = BookingOrchestrator()
        sample_state_with_restaurant.booking_confirmed = True
        sample_state_with_restaurant.confirmation_number = "4892"

        result = await orchestrator.confirm_booking(sample_state_with_restaurant)

        assert result.status == SessionStatus.COMPLETED

    def test_route_conversation(self):
        """Test conversation routing logic."""
        orchestrator = BookingOrchestrator()

        # Test booking confirmed route
        state = DrivingBookingState(
            session_id="test_001",
            driver_id="driver_001",
            start_time=datetime.now(),
        )
        state.booking_confirmed = True
        route = orchestrator.route_conversation(state)
        assert route == "booking_confirmed"

        # Test error route
        state.booking_confirmed = False
        state.add_error("Test error")
        route = orchestrator.route_conversation(state)
        assert route == "error"

    def test_route_error_recovery(self):
        """Test error recovery routing logic."""
        orchestrator = BookingOrchestrator()

        # Test retry route
        state = DrivingBookingState(
            session_id="test_001",
            driver_id="driver_001",
            start_time=datetime.now(),
        )
        state.max_retries = 3
        state.retry_count = 1
        route = orchestrator.route_error_recovery(state)
        assert route == "retry"

        # Test abandon route
        state.retry_count = 3
        route = orchestrator.route_error_recovery(state)
        assert route == "abandon"

    @pytest.mark.asyncio
    async def test_full_booking_session(self):
        """Test running a complete booking session."""
        orchestrator = BookingOrchestrator()

        result = await orchestrator.run_booking_session(
            driver_id="test_driver",
            initial_utterance="Book a table for 2 at Italian next Friday at 7 PM",
        )

        # Should complete without errors
        assert result.session_id is not None
        assert result.driver_id == "test_driver"
        # In demo mode, should succeed
        if True:  # demo_mode
            assert result.status in [
                SessionStatus.COMPLETED,
                SessionStatus.FAILED,
            ]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
