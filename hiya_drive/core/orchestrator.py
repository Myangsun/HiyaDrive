"""
LangGraph-based orchestration engine for the booking agent.
Defines the state machine workflow for restaurant booking.
"""

from typing import Literal, Optional
from datetime import datetime
import uuid
import json

from langgraph.graph import StateGraph, END
from anthropic import Anthropic

from hiya_drive.models.state import DrivingBookingState, SessionStatus, Restaurant
from hiya_drive.utils.logger import logger
from hiya_drive.config.settings import settings


class BookingOrchestrator:
    """Main orchestration engine using LangGraph."""

    def __init__(self):
        """Initialize the orchestrator with Claude client."""
        self.client = Anthropic()
        self.workflow = self._build_workflow()
        self.app = self.workflow.compile()

    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(DrivingBookingState)

        # Define all nodes
        workflow.add_node("parse_intent", self.parse_intent)
        workflow.add_node("check_calendar", self.check_calendar)
        workflow.add_node("search_restaurants", self.search_restaurants)
        workflow.add_node("select_restaurant", self.select_restaurant)
        workflow.add_node("prepare_call", self.prepare_call)
        workflow.add_node("make_call", self.make_call)
        workflow.add_node("converse", self.converse)
        workflow.add_node("confirm_booking", self.confirm_booking)
        workflow.add_node("handle_error", self.handle_error)

        # Set entry point
        workflow.set_entry_point("parse_intent")

        # Define edges (main happy path)
        workflow.add_edge("parse_intent", "check_calendar")
        workflow.add_edge("check_calendar", "search_restaurants")
        workflow.add_edge("search_restaurants", "select_restaurant")
        workflow.add_edge("select_restaurant", "prepare_call")
        workflow.add_edge("prepare_call", "make_call")
        workflow.add_edge("make_call", "converse")

        # Conditional edges from converse
        workflow.add_conditional_edges(
            "converse",
            self.route_conversation,
            {
                "booking_confirmed": "confirm_booking",
                "need_alternatives": "search_restaurants",
                "error": "handle_error",
                "timeout": "handle_error",
            },
        )

        # Termination edges
        workflow.add_edge("confirm_booking", END)
        workflow.add_conditional_edges(
            "handle_error",
            self.route_error_recovery,
            {
                "retry": "make_call",
                "fallback": "confirm_booking",
                "abandon": END,
            },
        )

        return workflow

    # =========================================================================
    # Workflow Nodes
    # =========================================================================

    async def parse_intent(self, state: DrivingBookingState) -> DrivingBookingState:
        """Extract booking parameters from user utterance."""
        logger.info(f"[{state.session_id}] Parsing intent from: {state.last_utterance}")

        # In demo mode, use simple mock parsing
        if settings.demo_mode:
            # Simple keyword-based parsing for demo
            utterance = (state.last_utterance or "").lower()

            # Extract party size
            import re
            party_match = re.search(r'(\d+)\s+(?:people|person|for)', utterance)
            if party_match:
                state.party_size = int(party_match.group(1))
            else:
                state.party_size = 2

            # Extract cuisine
            for cuisine in ["italian", "sushi", "french", "mexican", "thai", "indian"]:
                if cuisine in utterance:
                    state.cuisine_type = cuisine.capitalize()
                    break
            if not state.cuisine_type:
                state.cuisine_type = "Italian"

            # Extract location
            if "near" in utterance:
                import re
                loc_match = re.search(r'near\s+(\w+)', utterance)
                state.location = loc_match.group(1) if loc_match else "Boston"
            else:
                state.location = "Boston"

            # Extract date
            if "friday" in utterance:
                state.requested_date = "next Friday"
            elif "tomorrow" in utterance:
                state.requested_date = "tomorrow"
            else:
                state.requested_date = "2024-11-22"

            # Extract time
            time_match = re.search(r'(\d{1,2})\s*(?:pm|am|:00)', utterance)
            if time_match:
                hour = int(time_match.group(1))
                if "pm" in utterance and hour < 12:
                    hour += 12
                state.requested_time = f"{hour:02d}:00"
            else:
                state.requested_time = "19:00"

            logger.info(
                f"[{state.session_id}] Parsed intent (demo): "
                f"party_size={state.party_size}, "
                f"cuisine={state.cuisine_type}, "
                f"location={state.location}, "
                f"date={state.requested_date}, "
                f"time={state.requested_time}"
            )
            return state

        # Real API parsing (when not in demo mode)
        system_prompt = """Extract booking intent from user speech.
        Return JSON with: party_size (int), cuisine_type (str), location (str), date (str), time (str).
        If value is not mentioned, set to null.
        Keep response concise."""

        try:
            response = self.client.messages.create(
                model=settings.llm_model,
                max_tokens=300,
                system=system_prompt,
                messages=[{"role": "user", "content": state.last_utterance or ""}],
            )

            intent_text = response.content[0].text
            # Extract JSON from response
            try:
                intent = json.loads(intent_text)
            except json.JSONDecodeError:
                # Try to find JSON in the response
                import re

                json_match = re.search(r"\{.*\}", intent_text, re.DOTALL)
                intent = json.loads(json_match.group()) if json_match else {}

            state.party_size = intent.get("party_size")
            state.cuisine_type = intent.get("cuisine_type")
            state.location = intent.get("location")
            state.requested_date = intent.get("date")
            state.requested_time = intent.get("time")

            # Default time if not provided
            if not state.requested_time:
                state.requested_time = "19:00"

            logger.info(
                f"[{state.session_id}] Parsed intent: "
                f"party_size={state.party_size}, "
                f"cuisine={state.cuisine_type}, "
                f"date={state.requested_date}, "
                f"time={state.requested_time}"
            )

        except Exception as e:
            logger.error(f"[{state.session_id}] Error parsing intent: {e}")
            state.add_error(f"Intent parsing failed: {str(e)}")

        return state

    async def check_calendar(self, state: DrivingBookingState) -> DrivingBookingState:
        """Check driver's calendar availability."""
        logger.info(f"[{state.session_id}] Checking calendar availability")

        # For MVP: mock calendar check
        if settings.use_mock_calendar or settings.demo_mode:
            # Always available in demo mode
            state.driver_calendar_free = True
            logger.info(f"[{state.session_id}] Calendar: Available (mocked)")
        else:
            # Real implementation would call Google Calendar API
            state.driver_calendar_free = True

        return state

    async def search_restaurants(self, state: DrivingBookingState) -> DrivingBookingState:
        """Search for restaurants matching criteria."""
        logger.info(
            f"[{state.session_id}] Searching for {state.cuisine_type} restaurants in {state.location}"
        )

        # For MVP: mock restaurant search
        if settings.use_mock_places or settings.demo_mode:
            # Return mock restaurants
            mock_restaurants = [
                Restaurant(
                    name="Olive Garden",
                    phone="+1-555-0100",
                    address="123 Main St, Boston, MA",
                    rating=4.2,
                ),
                Restaurant(
                    name="Restaurant 2",
                    phone="+1-555-0200",
                    address="456 Park Ave, Boston, MA",
                    rating=4.5,
                ),
                Restaurant(
                    name="Restaurant 3",
                    phone="+1-555-0300",
                    address="789 Broadway, Boston, MA",
                    rating=4.1,
                ),
            ]
            state.restaurant_candidates = mock_restaurants
            logger.info(f"[{state.session_id}] Found {len(mock_restaurants)} restaurants (mocked)")
        else:
            # Real implementation would call Google Places API
            state.restaurant_candidates = []

        return state

    async def select_restaurant(
        self, state: DrivingBookingState
    ) -> DrivingBookingState:
        """Select a restaurant from candidates."""
        logger.info(f"[{state.session_id}] Selecting restaurant")

        if not state.restaurant_candidates:
            state.add_error("No restaurants found")
            return state

        # Auto-select first restaurant for MVP
        state.selected_restaurant = state.restaurant_candidates[0]
        logger.info(f"[{state.session_id}] Selected: {state.selected_restaurant.name}")

        return state

    async def prepare_call(self, state: DrivingBookingState) -> DrivingBookingState:
        """Generate opening script for the call."""
        logger.info(f"[{state.session_id}] Preparing call strategy")

        if not state.selected_restaurant:
            state.add_error("No restaurant selected")
            return state

        # In demo mode, use a simple script
        if settings.demo_mode:
            state.call_opening_script = (
                f"Hello, I'd like to make a reservation for {state.party_size} "
                f"on {state.requested_date} at {state.requested_time}."
            )
            logger.info(f"[{state.session_id}] Call script (demo): {state.call_opening_script}")
            return state

        # Real API call when not in demo mode
        try:
            prompt = f"""You're calling {state.selected_restaurant.name} to make a reservation.

Details:
- Party size: {state.party_size}
- Date: {state.requested_date}
- Time: {state.requested_time}

Generate a SHORT (1 sentence) opening statement for the receptionist.
Be natural and friendly. Format: [SCRIPT] your script here [END]"""

            response = self.client.messages.create(
                model=settings.llm_model,
                max_tokens=150,
                messages=[{"role": "user", "content": prompt}],
            )

            script_text = response.content[0].text
            # Extract script
            import re

            script_match = re.search(r"\[SCRIPT\](.*?)\[END\]", script_text, re.DOTALL)
            state.call_opening_script = (
                script_match.group(1).strip() if script_match else script_text.strip()
            )

            logger.info(
                f"[{state.session_id}] Call script: {state.call_opening_script}"
            )

        except Exception as e:
            logger.error(f"[{state.session_id}] Error preparing call: {e}")
            state.call_opening_script = f"Hello, I'd like to make a reservation for {state.party_size} on {state.requested_date} at {state.requested_time}."

        return state

    async def make_call(self, state: DrivingBookingState) -> DrivingBookingState:
        """Initiate the call to the restaurant."""
        logger.info(
            f"[{state.session_id}] Making call to {state.selected_restaurant.name}"
        )

        if not state.selected_restaurant:
            state.add_error("No restaurant to call")
            return state

        # For MVP: mock Twilio call
        if settings.use_mock_twilio or settings.demo_mode:
            state.twilio_call_sid = f"mock_call_{uuid.uuid4().hex[:8]}"
            state.call_connected = True
            logger.info(f"[{state.session_id}] Call initiated (mocked): {state.twilio_call_sid}")
        else:
            # Real implementation would call Twilio API
            state.call_connected = True

        return state

    async def converse(self, state: DrivingBookingState) -> DrivingBookingState:
        """Handle multi-turn conversation with restaurant."""
        logger.info(f"[{state.session_id}] Starting conversation")

        if not state.call_connected:
            state.add_error("Call not connected")
            return state

        # Simulate a simple conversation for MVP
        state.add_message("assistant", state.call_opening_script or "Hello")

        # For demo: simulate restaurant response and booking confirmation
        if settings.demo_mode:
            state.add_message("restaurant", "Hello! How many people?")
            state.add_message("assistant", f"{state.party_size} people please.")
            state.add_message("restaurant", "Sure! What name for the reservation?")
            state.add_message("assistant", "Alex")
            state.add_message("restaurant", "Perfect! Your confirmation number is 4892.")

            state.confirmation_number = "4892"
            state.booking_confirmed = True
            logger.info(f"[{state.session_id}] Booking confirmed in demo mode")
        else:
            # Real STT/LLM/TTS conversation loop would go here
            state.booking_confirmed = False

        state.increment_turn()
        return state

    async def confirm_booking(self, state: DrivingBookingState) -> DrivingBookingState:
        """Save booking and create calendar event."""
        logger.info(f"[{state.session_id}] Confirming booking")

        if not state.booking_confirmed or not state.selected_restaurant:
            state.add_error("Cannot confirm incomplete booking")
            state.status = SessionStatus.FAILED
            return state

        # For MVP: just log the booking
        booking_info = {
            "session_id": state.session_id,
            "restaurant": state.selected_restaurant.name,
            "party_size": state.party_size,
            "date": state.requested_date,
            "time": state.requested_time,
            "confirmation_number": state.confirmation_number,
        }

        logger.info(f"[{state.session_id}] Booking confirmed: {booking_info}")

        state.status = SessionStatus.COMPLETED

        return state

    async def handle_error(self, state: DrivingBookingState) -> DrivingBookingState:
        """Handle errors with retry or fallback."""
        logger.error(f"[{state.session_id}] Error handler called. Errors: {state.errors}")

        if state.can_retry():
            state.increment_retry()
            logger.info(f"[{state.session_id}] Retrying (attempt {state.retry_count})")
        else:
            state.status = SessionStatus.FAILED
            logger.error(f"[{state.session_id}] Max retries exceeded, marking as failed")

        return state

    # =========================================================================
    # Conditional Routing Functions
    # =========================================================================

    def route_conversation(self, state: DrivingBookingState) -> Literal[
        "booking_confirmed", "need_alternatives", "error", "timeout"
    ]:
        """Route based on conversation outcome."""
        if state.booking_confirmed:
            return "booking_confirmed"
        elif state.has_errors():
            return "error"
        elif state.turn_count >= settings.max_conversation_turns:
            return "timeout"
        else:
            return "need_alternatives"

    def route_error_recovery(
        self, state: DrivingBookingState
    ) -> Literal["retry", "fallback", "abandon"]:
        """Route error recovery strategy."""
        if state.can_retry():
            return "retry"
        elif state.booking_confirmed:
            return "fallback"
        else:
            return "abandon"

    # =========================================================================
    # Public Interface
    # =========================================================================

    async def run_booking_session(
        self,
        driver_id: str,
        initial_utterance: str,
    ) -> DrivingBookingState:
        """Run a complete booking session."""

        # Create initial state
        state = DrivingBookingState(
            session_id=str(uuid.uuid4()),
            driver_id=driver_id,
            start_time=datetime.now(),
            last_utterance=initial_utterance,
        )

        logger.info(
            f"[{state.session_id}] Starting booking session for driver {driver_id}"
        )
        logger.info(f"[{state.session_id}] User utterance: {initial_utterance}")

        # Run the workflow
        try:
            final_state_dict = await self.app.ainvoke(state)

            # LangGraph returns a dict, convert back to DrivingBookingState
            if isinstance(final_state_dict, dict):
                # Reconstruct the state object from the returned dict
                state_obj = DrivingBookingState(
                    session_id=final_state_dict.get("session_id", state.session_id),
                    driver_id=final_state_dict.get("driver_id", state.driver_id),
                    start_time=final_state_dict.get("start_time", state.start_time),
                    status=final_state_dict.get("status", state.status),
                    party_size=final_state_dict.get("party_size"),
                    requested_date=final_state_dict.get("requested_date"),
                    requested_time=final_state_dict.get("requested_time"),
                    cuisine_type=final_state_dict.get("cuisine_type"),
                    location=final_state_dict.get("location"),
                    driver_location=final_state_dict.get("driver_location"),
                    driver_calendar_free=final_state_dict.get("driver_calendar_free", False),
                    restaurant_candidates=final_state_dict.get("restaurant_candidates", []),
                    selected_restaurant=final_state_dict.get("selected_restaurant"),
                    confirmation_number=final_state_dict.get("confirmation_number"),
                    booking_confirmed=final_state_dict.get("booking_confirmed", False),
                    errors=final_state_dict.get("errors", []),
                    retry_count=final_state_dict.get("retry_count", 0),
                    max_retries=final_state_dict.get("max_retries", 2),
                    current_speed_kmh=final_state_dict.get("current_speed_kmh"),
                    road_complexity=final_state_dict.get("road_complexity", "unknown"),
                    safe_to_speak=final_state_dict.get("safe_to_speak", True),
                    turn_count=final_state_dict.get("turn_count", 0),
                    last_utterance=final_state_dict.get("last_utterance"),
                    messages=final_state_dict.get("messages", []),
                    conversation_history=final_state_dict.get("conversation_history", []),
                    twilio_call_sid=final_state_dict.get("twilio_call_sid"),
                    call_connected=final_state_dict.get("call_connected", False),
                    call_duration_seconds=final_state_dict.get("call_duration_seconds", 0),
                    metadata=final_state_dict.get("metadata", {}),
                )
                logger.info(f"[{state.session_id}] Booking session completed")
                return state_obj
            else:
                logger.info(f"[{state.session_id}] Booking session completed")
                return final_state_dict
        except Exception as e:
            logger.error(f"[{state.session_id}] Workflow execution failed: {e}")
            state.add_error(f"Workflow error: {str(e)}")
            state.status = SessionStatus.FAILED
            return state


# Global orchestrator instance
orchestrator = BookingOrchestrator()
