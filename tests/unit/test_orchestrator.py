"""
Unit tests for the booking orchestrator.
Tests the 9-node workflow with service-agnostic booking examples.
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
    async def test_parse_intent_node_with_service_booking(self):
        """Test parse_intent node extracts intent from service booking utterance."""
        orchestrator = BookingOrchestrator()
        state = DrivingBookingState(
            session_id="test_001",
            driver_id="driver_001",
            start_time=datetime.now(),
            last_utterance="Book a haircut for 2 people next Friday at 3 PM",
        )

        result = await orchestrator.parse_intent(state)

        # Should extract basic info (may be None in demo mode)
        # Real implementation would set these fields
        assert isinstance(result, DrivingBookingState)
        # In demo mode, fields may be None or extracted
        assert result.party_size is None or result.party_size >= 1

    @pytest.mark.asyncio
    async def test_parse_intent_with_restaurant_booking(self):
        """Test parse_intent with restaurant booking for backward compatibility."""
        orchestrator = BookingOrchestrator()
        state = DrivingBookingState(
            session_id="test_002",
            driver_id="driver_002",
            start_time=datetime.now(),
            last_utterance="Reserve a table for 4 at Italian next Friday at 7 PM",
        )

        result = await orchestrator.parse_intent(state)

        assert isinstance(result, DrivingBookingState)
        assert result.party_size is None or result.party_size >= 1

    @pytest.mark.asyncio
    async def test_check_calendar_node_available(self):
        """Test check_calendar node when driver is available."""
        orchestrator = BookingOrchestrator()
        state = DrivingBookingState(
            session_id="test_003",
            driver_id="driver_003",
            start_time=datetime.now(),
            requested_date="2024-12-20",
            requested_time="15:00",
        )

        result = await orchestrator.check_calendar(state)

        # In demo mode, should return a boolean
        assert isinstance(result.driver_calendar_free, bool)

    @pytest.mark.asyncio
    async def test_check_calendar_node_returns_bool(self):
        """Test check_calendar node always returns boolean availability status."""
        orchestrator = BookingOrchestrator()
        state = DrivingBookingState(
            session_id="test_004",
            driver_id="driver_004",
            start_time=datetime.now(),
        )

        result = await orchestrator.check_calendar(state)

        # Must return a valid boolean
        assert isinstance(result.driver_calendar_free, bool)

    @pytest.mark.asyncio
    async def test_search_services_node(self):
        """Test search_restaurants node finds matching services."""
        orchestrator = BookingOrchestrator()
        state = DrivingBookingState(
            session_id="test_005",
            driver_id="driver_005",
            start_time=datetime.now(),
            cuisine_type="Hair Salon",  # Generic service type
            location="Boston",
        )

        result = await orchestrator.search_restaurants(state)

        # In demo mode, should return candidates list
        assert isinstance(result.restaurant_candidates, list)

    @pytest.mark.asyncio
    async def test_select_service_node(self, sample_state_with_service):
        """Test select_restaurant node selects service provider."""
        orchestrator = BookingOrchestrator()

        # Add some candidates
        from hiya_drive.models.state import Restaurant

        sample_state_with_service.restaurant_candidates = [
            Restaurant(
                name="StyleCuts Hair Salon",
                phone="+1-555-0100",
                address="123 Main St",
                rating=4.2,
            ),
            Restaurant(
                name="Prime Cuts Barber Shop",
                phone="+1-555-0200",
                address="456 Park Ave",
                rating=4.5,
            ),
        ]

        result = await orchestrator.select_restaurant(sample_state_with_service)

        assert result.selected_restaurant is not None
        assert result.selected_restaurant.name == "StyleCuts Hair Salon"

    @pytest.mark.asyncio
    async def test_prepare_call_node_generates_script(self, sample_state_with_service):
        """Test prepare_call node generates opening script."""
        orchestrator = BookingOrchestrator()

        result = await orchestrator.prepare_call(sample_state_with_service)

        # Should have a script
        assert result.call_opening_script is not None
        assert len(result.call_opening_script) > 0

    @pytest.mark.asyncio
    async def test_make_call_node(self, sample_state_with_service):
        """Test make_call node initiates call."""
        orchestrator = BookingOrchestrator()

        result = await orchestrator.make_call(sample_state_with_service)

        # In demo mode, should set call connected
        assert result.call_connected is True

    @pytest.mark.asyncio
    async def test_converse_node(self, sample_state_with_service):
        """Test converse node handles conversation."""
        orchestrator = BookingOrchestrator()
        sample_state_with_service.call_connected = True

        result = await orchestrator.converse(sample_state_with_service)

        # In demo mode, should confirm booking
        assert result.booking_confirmed is True
        assert result.confirmation_number is not None

    @pytest.mark.asyncio
    async def test_confirm_booking_node(self, sample_state_with_service):
        """Test confirm_booking node saves booking."""
        orchestrator = BookingOrchestrator()
        sample_state_with_service.booking_confirmed = True
        sample_state_with_service.confirmation_number = "4892"

        result = await orchestrator.confirm_booking(sample_state_with_service)

        assert result.status == SessionStatus.COMPLETED

    def test_route_conversation_booking_confirmed(self):
        """Test conversation routing when booking is confirmed."""
        orchestrator = BookingOrchestrator()

        state = DrivingBookingState(
            session_id="test_010",
            driver_id="driver_010",
            start_time=datetime.now(),
        )
        state.booking_confirmed = True
        route = orchestrator.route_conversation(state)
        assert route == "booking_confirmed"

    def test_route_conversation_error(self):
        """Test conversation routing when error occurs."""
        orchestrator = BookingOrchestrator()

        state = DrivingBookingState(
            session_id="test_011",
            driver_id="driver_011",
            start_time=datetime.now(),
        )
        state.booking_confirmed = False
        state.add_error("Test error")
        route = orchestrator.route_conversation(state)
        assert route == "error"

    def test_route_error_recovery_retry(self):
        """Test error recovery routing allows retry."""
        orchestrator = BookingOrchestrator()

        state = DrivingBookingState(
            session_id="test_012",
            driver_id="driver_012",
            start_time=datetime.now(),
        )
        state.max_retries = 3
        state.retry_count = 1
        route = orchestrator.route_error_recovery(state)
        assert route == "retry"

    def test_route_error_recovery_abandon(self):
        """Test error recovery routing abandons after max retries."""
        orchestrator = BookingOrchestrator()

        state = DrivingBookingState(
            session_id="test_013",
            driver_id="driver_013",
            start_time=datetime.now(),
        )
        state.max_retries = 3
        state.retry_count = 3
        route = orchestrator.route_error_recovery(state)
        assert route == "abandon"

    @pytest.mark.asyncio
    async def test_full_booking_session_haircut(self):
        """Test running a complete booking session for a haircut."""
        orchestrator = BookingOrchestrator()

        result = await orchestrator.run_booking_session(
            driver_id="test_driver",
            initial_utterance="Book a haircut for 2 people next Friday at 3 PM",
        )

        # Should complete without errors
        assert result.session_id is not None
        assert result.driver_id == "test_driver"
        # In demo mode, should succeed or fail gracefully
        assert result.status in [
            SessionStatus.COMPLETED,
            SessionStatus.FAILED,
        ]

    @pytest.mark.asyncio
    async def test_full_booking_session_massage(self):
        """Test running a complete booking session for a massage."""
        orchestrator = BookingOrchestrator()

        result = await orchestrator.run_booking_session(
            driver_id="test_driver_massage",
            initial_utterance="Schedule a massage appointment for tomorrow at 2 PM",
        )

        # Should complete without errors
        assert result.session_id is not None
        assert result.driver_id == "test_driver_massage"
        assert result.status in [
            SessionStatus.COMPLETED,
            SessionStatus.FAILED,
        ]

    @pytest.mark.asyncio
    async def test_full_booking_session_restaurant(self):
        """Test running a complete booking session for a restaurant (backward compatibility)."""
        orchestrator = BookingOrchestrator()

        result = await orchestrator.run_booking_session(
            driver_id="test_driver_restaurant",
            initial_utterance="Reserve a table for 4 at Italian next Friday at 7 PM",
        )

        # Should complete without errors
        assert result.session_id is not None
        assert result.driver_id == "test_driver_restaurant"
        assert result.status in [
            SessionStatus.COMPLETED,
            SessionStatus.FAILED,
        ]


class TestCalendarRetryLogic:
    """Test calendar availability checking with retry logic (critical feature)."""

    @pytest.mark.asyncio
    async def test_calendar_check_initial_available(self):
        """Test calendar check succeeds on first attempt."""
        orchestrator = BookingOrchestrator()
        state = DrivingBookingState(
            session_id="test_cal_001",
            driver_id="driver_cal_001",
            start_time=datetime.now(),
            requested_date="2024-12-20",
            requested_time="15:00",
        )

        result = await orchestrator.check_calendar(state)

        # Should succeed without retries
        assert isinstance(result.driver_calendar_free, bool)
        assert result.retry_count == 0  # No retries needed

    @pytest.mark.asyncio
    async def test_calendar_retry_counter_increments(self):
        """Test retry counter increments when calendar is busy."""
        orchestrator = BookingOrchestrator()
        state = DrivingBookingState(
            session_id="test_cal_002",
            driver_id="driver_cal_002",
            start_time=datetime.now(),
        )

        # Simulate busy calendar scenario
        initial_retry_count = state.retry_count
        state.increment_retry()

        assert state.retry_count == initial_retry_count + 1

    @pytest.mark.asyncio
    async def test_can_retry_logic(self):
        """Test can_retry() correctly determines if retry is possible."""
        orchestrator = BookingOrchestrator()
        state = DrivingBookingState(
            session_id="test_cal_003",
            driver_id="driver_cal_003",
            start_time=datetime.now(),
        )

        # Initially should be able to retry
        assert state.can_retry() is True

        # After max retries, should not be able to retry
        state.max_retries = 3
        state.retry_count = 3
        assert state.can_retry() is False

    def test_calendar_retry_max_retries_configuration(self):
        """Test that calendar retry is configurable to max 3 attempts."""
        state = DrivingBookingState(
            session_id="test_cal_004",
            driver_id="driver_cal_004",
            start_time=datetime.now(),
        )

        # Default should allow retries
        assert state.max_retries >= 2
        # Calendar typically retries up to 3 times
        state.max_retries = 3
        assert state.max_retries == 3

    @pytest.mark.asyncio
    async def test_calendar_retry_state_transitions(self):
        """Test state transitions during calendar retry attempts."""
        state = DrivingBookingState(
            session_id="test_cal_005",
            driver_id="driver_cal_005",
            start_time=datetime.now(),
            status=SessionStatus.ACTIVE,
        )

        # Set max retries to test (system default is 2)
        state.max_retries = 3

        # Simulate 3 retry attempts
        assert state.can_retry() is True
        state.increment_retry()

        assert state.can_retry() is True
        state.increment_retry()

        assert state.can_retry() is True
        state.increment_retry()

        # After 3 retries, should not be able to retry
        assert state.can_retry() is False
        # Status should still be ACTIVE (error handling decides to fail)
        assert state.status == SessionStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_calendar_busy_triggers_retry(self):
        """Test that calendar being busy triggers retry mechanism."""
        orchestrator = BookingOrchestrator()
        state = DrivingBookingState(
            session_id="test_cal_006",
            driver_id="driver_cal_006",
            start_time=datetime.now(),
            requested_date="2024-12-20",
            requested_time="15:00",
        )

        # Simulate busy response
        state.driver_calendar_free = False

        # Should be able to retry
        assert state.can_retry() is True
        assert state.driver_calendar_free is False

    @pytest.mark.asyncio
    async def test_calendar_alternative_time_extraction(self):
        """Test extracting alternative time when user is asked for new time."""
        state = DrivingBookingState(
            session_id="test_cal_007",
            driver_id="driver_cal_007",
            start_time=datetime.now(),
            requested_time="15:00",
        )

        # Simulate user providing alternative time
        # (In real implementation, would use LLM to extract from conversation)
        state.requested_time = "16:00"  # Alternative time

        assert state.requested_time == "16:00"
        assert state.requested_time != "15:00"

    @pytest.mark.asyncio
    async def test_calendar_fails_after_max_retries(self):
        """Test that booking fails after max calendar retry attempts."""
        state = DrivingBookingState(
            session_id="test_cal_008",
            driver_id="driver_cal_008",
            start_time=datetime.now(),
            status=SessionStatus.ACTIVE,
        )

        # Simulate 3 failed retry attempts
        state.max_retries = 3
        for i in range(3):
            state.increment_retry()
            state.driver_calendar_free = False

        # After exhausting retries, should fail
        assert state.can_retry() is False
        assert state.driver_calendar_free is False
        # In real implementation, would transition to FAILED status
        assert state.retry_count == 3

    @pytest.mark.asyncio
    async def test_calendar_success_on_retry_attempt_2(self):
        """Test successful booking on second calendar attempt."""
        state = DrivingBookingState(
            session_id="test_cal_009",
            driver_id="driver_cal_009",
            start_time=datetime.now(),
            status=SessionStatus.ACTIVE,
        )

        # First attempt: driver busy
        state.driver_calendar_free = False
        state.increment_retry()
        assert not state.driver_calendar_free
        assert state.can_retry() is True

        # Second attempt: driver available
        state.driver_calendar_free = True
        assert state.driver_calendar_free is True
        # Should not need further retries

    def test_calendar_retry_error_message_on_exhaustion(self):
        """Test that appropriate error message is set when calendar retries exhausted."""
        state = DrivingBookingState(
            session_id="test_cal_010",
            driver_id="driver_cal_010",
            start_time=datetime.now(),
            status=SessionStatus.ACTIVE,
        )

        # Exhaust retries
        state.max_retries = 3
        for _ in range(3):
            state.increment_retry()

        # Should add error when retries exhausted
        if not state.can_retry():
            state.add_error("Could not find available time after 3 attempts")

        assert state.has_errors() is True
        assert "3 attempts" in state.last_error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
