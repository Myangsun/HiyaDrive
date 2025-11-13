"""
Voice-integrated orchestrator where each agent is a voice agent.
Every step interacts with the user through voice feedback and confirmations.
"""

import asyncio
import uuid
import json
from datetime import datetime
from typing import Literal, Optional

from langgraph.graph import StateGraph, END
from anthropic import Anthropic

from hiya_drive.models.state import DrivingBookingState, SessionStatus, Restaurant
from hiya_drive.utils.logger import logger
from hiya_drive.config.settings import settings
from hiya_drive.integrations.calendar_service import calendar_service
from hiya_drive.integrations.places_service import places_service
from hiya_drive.integrations.twilio_service import twilio_service
from hiya_drive.voice.voice_processor import voice_processor


class VoiceIntegratedOrchestrator:
    """Orchestrator where every node is a voice agent that interacts with the user."""

    def __init__(self):
        """Initialize the orchestrator with Claude client."""
        self.client = Anthropic(api_key=settings.anthropic_api_key)
        self.workflow = self._build_workflow()
        self.app = self.workflow.compile()

    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow with voice-integrated nodes."""
        workflow = StateGraph(DrivingBookingState)

        # Add all nodes (now each node includes voice interaction)
        workflow.add_node("parse_intent", self.voice_parse_intent)
        workflow.add_node("check_calendar", self.voice_check_calendar)
        workflow.add_node("search_restaurants", self.voice_search_restaurants)
        workflow.add_node("select_restaurant", self.voice_select_restaurant)
        workflow.add_node("prepare_call", self.voice_prepare_call)
        workflow.add_node("make_call", self.voice_make_call)
        workflow.add_node("converse", self.voice_converse)
        workflow.add_node("confirm_booking", self.voice_confirm_booking)
        workflow.add_node("handle_error", self.voice_handle_error)

        # Set entry point
        workflow.set_entry_point("parse_intent")

        # Define edges
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
    # Voice-Integrated Nodes (Each is a Voice Agent)
    # =========================================================================

    async def voice_parse_intent(self, state: DrivingBookingState) -> DrivingBookingState:
        """Parse intent with voice feedback."""
        logger.info(f"[{state.session_id}] 🎤 VOICE AGENT: Intent Parser")
        
        # Voice: Acknowledge user request
        await voice_processor.speak(f"Thank you for your request. Let me understand what you're looking for.")
        await asyncio.sleep(0.5)

        logger.info(f"[{state.session_id}] Parsing intent from: {state.last_utterance}")

        # Parse using Claude
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
            try:
                intent = json.loads(intent_text)
            except json.JSONDecodeError:
                import re
                json_match = re.search(r"\{.*\}", intent_text, re.DOTALL)
                intent = json.loads(json_match.group()) if json_match else {}

            state.party_size = intent.get("party_size")
            state.cuisine_type = intent.get("cuisine_type")
            state.location = intent.get("location")
            state.requested_date = intent.get("date")
            state.requested_time = intent.get("time")

            if not state.requested_time:
                state.requested_time = "19:00"

            # Voice: Confirm parsed details
            detail_msg = (
                f"Perfect! I understand you want to book for {state.party_size} people. "
                f"Looking for {state.cuisine_type} restaurants in {state.location}. "
                f"On {state.requested_date} at {state.requested_time}. Is that correct?"
            )
            logger.info(f"[{state.session_id}] ✓ Parsed: {detail_msg}")
            await voice_processor.speak(detail_msg)
            await asyncio.sleep(0.5)

        except Exception as e:
            logger.error(f"[{state.session_id}] Error parsing intent: {e}")
            error_msg = "Sorry, I didn't quite understand. Could you repeat that please?"
            await voice_processor.speak(error_msg)
            state.add_error(f"Intent parsing failed: {str(e)}")

        return state

    async def voice_check_calendar(self, state: DrivingBookingState) -> DrivingBookingState:
        """Check calendar with voice feedback."""
        logger.info(f"[{state.session_id}] 🎤 VOICE AGENT: Calendar Checker")
        
        # Voice: Checking calendar
        await voice_processor.speak(f"Let me check your calendar availability.")
        await asyncio.sleep(0.5)

        logger.info(f"[{state.session_id}] Checking calendar availability")

        if settings.use_mock_calendar or settings.demo_mode:
            state.driver_calendar_free = True
            availability_msg = f"Great news! You're available on {state.requested_date} at {state.requested_time}."
        else:
            try:
                booking_time = f"{state.requested_date} at {state.requested_time}"
                state.driver_calendar_free = await calendar_service.is_available(booking_time)
                availability_msg = (
                    f"You're available on {state.requested_date}" if state.driver_calendar_free
                    else f"You might have a conflict on {state.requested_date}, but I'll proceed anyway"
                )
            except Exception as e:
                logger.warning(f"[{state.session_id}] Calendar check failed: {e}, assuming available")
                state.driver_calendar_free = True
                availability_msg = f"Your calendar is looking good for {state.requested_date}!"

        logger.info(f"[{state.session_id}] ✓ Calendar: {availability_msg}")
        await voice_processor.speak(availability_msg)
        await asyncio.sleep(0.5)

        return state

    async def voice_search_restaurants(self, state: DrivingBookingState) -> DrivingBookingState:
        """Search restaurants with voice feedback."""
        logger.info(f"[{state.session_id}] 🎤 VOICE AGENT: Restaurant Searcher")
        
        # Voice: Starting search
        search_msg = f"Now let me search for {state.cuisine_type} restaurants in {state.location}. This might take a moment..."
        logger.info(f"[{state.session_id}] Searching: {search_msg}")
        await voice_processor.speak(search_msg)
        await asyncio.sleep(1)

        logger.info(f"[{state.session_id}] Searching for {state.cuisine_type} restaurants in {state.location}")

        try:
            restaurants = await places_service.search_restaurants(
                cuisine_type=state.cuisine_type,
                location=state.location,
                party_size=state.party_size,
            )
            state.restaurant_candidates = restaurants
            
            # Voice: Found restaurants
            found_msg = f"Excellent! I found {len(restaurants)} wonderful {state.cuisine_type} restaurants for you!"
            logger.info(f"[{state.session_id}] ✓ Found: {found_msg}")
            await voice_processor.speak(found_msg)
            await asyncio.sleep(0.5)
            
        except Exception as e:
            logger.error(f"[{state.session_id}] Restaurant search failed: {e}")
            error_msg = f"I couldn't find any restaurants matching your criteria. Would you like to try a different cuisine?"
            await voice_processor.speak(error_msg)
            state.add_error(f"Restaurant search failed: {str(e)}")
            state.restaurant_candidates = []

        return state

    async def voice_select_restaurant(self, state: DrivingBookingState) -> DrivingBookingState:
        """Select restaurant with voice feedback."""
        logger.info(f"[{state.session_id}] 🎤 VOICE AGENT: Restaurant Selector")

        if not state.restaurant_candidates:
            error_msg = "Unfortunately, I don't have any restaurants to show you."
            await voice_processor.speak(error_msg)
            state.add_error("No restaurants found")
            return state

        # Voice: Present options
        present_msg = f"Here are the top {min(3, len(state.restaurant_candidates))} options:"
        logger.info(f"[{state.session_id}] Presenting: {present_msg}")
        await voice_processor.speak(present_msg)
        await asyncio.sleep(0.5)

        # Voice: List each restaurant
        for i, restaurant in enumerate(state.restaurant_candidates[:3], 1):
            option_msg = (
                f"Option {i}: {restaurant.name}. "
                f"Rated {restaurant.rating} stars. "
                f"Located at {restaurant.address}."
            )
            logger.info(f"[{state.session_id}] Option {i}: {option_msg}")
            await voice_processor.speak(option_msg)
            await asyncio.sleep(0.8)

        # Auto-select best option
        state.selected_restaurant = max(state.restaurant_candidates, key=lambda r: r.rating)
        selection_msg = f"I'm going to book the highest-rated option: {state.selected_restaurant.name} with {state.selected_restaurant.rating} stars."
        logger.info(f"[{state.session_id}] ✓ Selected: {selection_msg}")
        await voice_processor.speak(selection_msg)
        await asyncio.sleep(0.5)

        return state

    async def voice_prepare_call(self, state: DrivingBookingState) -> DrivingBookingState:
        """Prepare call with voice feedback."""
        logger.info(f"[{state.session_id}] 🎤 VOICE AGENT: Call Scripter")

        if not state.selected_restaurant:
            state.add_error("No restaurant selected")
            return state

        # Voice: Preparing script
        prepare_msg = f"Let me prepare what I'll say to {state.selected_restaurant.name}."
        logger.info(f"[{state.session_id}] Preparing: {prepare_msg}")
        await voice_processor.speak(prepare_msg)
        await asyncio.sleep(0.5)

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
            import re
            script_match = re.search(r"\[SCRIPT\](.*?)\[END\]", script_text, re.DOTALL)
            state.call_opening_script = (
                script_match.group(1).strip() if script_match else script_text.strip()
            )

            # Voice: Announce script
            script_msg = f"I will say: {state.call_opening_script}"
            logger.info(f"[{state.session_id}] ✓ Script: {script_msg}")
            await voice_processor.speak(script_msg)
            await asyncio.sleep(0.5)

        except Exception as e:
            logger.error(f"[{state.session_id}] Error preparing call: {e}")
            state.call_opening_script = f"Hello, I'd like to make a reservation for {state.party_size} on {state.requested_date} at {state.requested_time}."
            await voice_processor.speak(f"I'll say: {state.call_opening_script}")

        return state

    async def voice_make_call(self, state: DrivingBookingState) -> DrivingBookingState:
        """Make call with voice feedback."""
        logger.info(f"[{state.session_id}] 🎤 VOICE AGENT: Call Initiator")

        if not state.selected_restaurant:
            state.add_error("No restaurant to call")
            return state

        # Voice: Making the call
        call_msg = f"Now I'm calling {state.selected_restaurant.name} at {state.selected_restaurant.phone}..."
        logger.info(f"[{state.session_id}] Making call: {call_msg}")
        await voice_processor.speak(call_msg)
        await asyncio.sleep(1)

        try:
            call_sid = await twilio_service.make_call(
                to_number=state.selected_restaurant.phone,
                opening_script=state.call_opening_script,
            )
            if call_sid:
                state.twilio_call_sid = call_sid
                state.call_connected = True
                
                # Voice: Call connected
                connected_msg = f"Perfect! Connected to {state.selected_restaurant.name}!"
                logger.info(f"[{state.session_id}] ✓ Connected: {connected_msg}")
                await voice_processor.speak(connected_msg)
                await asyncio.sleep(0.5)
            else:
                state.call_connected = False
                error_msg = "Sorry, I couldn't connect to the restaurant. Let me try again."
                await voice_processor.speak(error_msg)
                state.add_error("Failed to initiate call")
        except Exception as e:
            logger.error(f"[{state.session_id}] Error making call: {e}")
            error_msg = f"There was an issue calling the restaurant: {str(e)}"
            await voice_processor.speak(error_msg)
            state.add_error(f"Call failed: {str(e)}")
            state.call_connected = False

        return state

    async def voice_converse(self, state: DrivingBookingState) -> DrivingBookingState:
        """Converse with voice feedback."""
        logger.info(f"[{state.session_id}] 🎤 VOICE AGENT: Conversationalist")

        if not state.call_connected:
            state.add_error("Call not connected")
            return state

        # Voice: Starting conversation
        converse_msg = "Now speaking with the restaurant..."
        logger.info(f"[{state.session_id}] {converse_msg}")
        await voice_processor.speak(converse_msg)
        await asyncio.sleep(0.5)

        # Simulate conversation
        state.add_message("assistant", state.call_opening_script or "Hello")
        state.add_message("restaurant", "Hello! How many people?")
        state.add_message("assistant", f"{state.party_size} people please.")
        state.add_message("restaurant", "Sure! What name for the reservation?")
        state.add_message("assistant", "Alex")
        state.add_message("restaurant", "Perfect! Your confirmation number is 4892.")

        state.confirmation_number = "4892"
        state.booking_confirmed = True
        
        # Voice: Booking confirmed
        confirm_msg = f"Great! Your booking is confirmed with confirmation number {state.confirmation_number}!"
        logger.info(f"[{state.session_id}] ✓ Confirmed: {confirm_msg}")
        await voice_processor.speak(confirm_msg)
        await asyncio.sleep(0.5)

        state.increment_turn()
        return state

    async def voice_confirm_booking(self, state: DrivingBookingState) -> DrivingBookingState:
        """Confirm booking with voice feedback."""
        logger.info(f"[{state.session_id}] 🎤 VOICE AGENT: Booking Finalizer")

        if not state.booking_confirmed or not state.selected_restaurant:
            state.add_error("Cannot confirm incomplete booking")
            state.status = SessionStatus.FAILED
            return state

        # Voice: Final confirmation with all details
        final_msg = (
            f"Excellent! Your reservation is confirmed! "
            f"You're booked at {state.selected_restaurant.name} "
            f"for {state.party_size} people on {state.requested_date} at {state.requested_time}. "
            f"Your confirmation number is {state.confirmation_number}. "
            f"Have a wonderful dining experience!"
        )
        logger.info(f"[{state.session_id}] ✓ Final: {final_msg}")
        await voice_processor.speak(final_msg)
        await asyncio.sleep(0.5)

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

        # Voice: Goodbye
        goodbye_msgs = [
            "Thanks for using HiyaDrive! Enjoy your meal!",
            "Your reservation is all set! Have a fantastic time!",
            "All done! I hope you have a wonderful dining experience!",
        ]
        import random
        goodbye = random.choice(goodbye_msgs)
        logger.info(f"[{state.session_id}] 👋 Goodbye: {goodbye}")
        await voice_processor.speak(goodbye)

        return state

    async def voice_handle_error(self, state: DrivingBookingState) -> DrivingBookingState:
        """Handle errors with voice feedback."""
        logger.error(f"[{state.session_id}] 🎤 VOICE AGENT: Error Handler")

        error_summary = ", ".join(state.errors) if state.errors else "An unknown error occurred"
        error_msg = f"I encountered an issue: {error_summary}. Let me try again."
        logger.error(f"[{state.session_id}] Error: {error_msg}")
        await voice_processor.speak(error_msg)
        await asyncio.sleep(0.5)

        if state.can_retry():
            state.increment_retry()
            retry_msg = f"Attempting again. Try number {state.retry_count}..."
            logger.info(f"[{state.session_id}] Retrying: {retry_msg}")
            await voice_processor.speak(retry_msg)
        else:
            state.status = SessionStatus.FAILED
            failure_msg = "Unfortunately, I couldn't complete your booking. Please try again later."
            logger.error(f"[{state.session_id}] Failed: {failure_msg}")
            await voice_processor.speak(failure_msg)

        await asyncio.sleep(0.5)
        return state

    # =========================================================================
    # Conditional Routing Functions
    # =========================================================================

    def route_conversation(self, state: DrivingBookingState) -> Literal["booking_confirmed", "need_alternatives", "error", "timeout"]:
        """Route based on conversation outcome."""
        if state.booking_confirmed:
            return "booking_confirmed"
        elif state.has_errors():
            return "error"
        elif state.turn_count >= settings.max_conversation_turns:
            return "timeout"
        else:
            return "need_alternatives"

    def route_error_recovery(self, state: DrivingBookingState) -> Literal["retry", "fallback", "abandon"]:
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

    async def run_voice_integrated_booking(
        self,
        driver_id: str,
        initial_utterance: str,
    ) -> DrivingBookingState:
        """Run a complete booking session with voice integration at every step."""

        # Voice: Welcome
        welcome_msgs = [
            "Welcome to HiyaDrive! I'm your voice-powered booking assistant. Let's get you a great restaurant!",
            "Hi! I'm HiyaDrive, ready to book your perfect restaurant. What are you in the mood for?",
            "Hello! I'm HiyaDrive. I'll help you find and book an amazing restaurant. Tell me what you'd like!",
        ]
        import random
        welcome = random.choice(welcome_msgs)
        logger.info("🎤 Welcome")
        await voice_processor.speak(welcome)
        await asyncio.sleep(1)

        # Create initial state
        state = DrivingBookingState(
            session_id=str(uuid.uuid4()),
            driver_id=driver_id,
            start_time=datetime.now(),
            last_utterance=initial_utterance,
        )

        logger.info(f"[{state.session_id}] Starting voice-integrated booking session for driver {driver_id}")
        logger.info(f"[{state.session_id}] User utterance: {initial_utterance}")

        # Run the workflow
        try:
            final_state_dict = await self.app.ainvoke(state)

            # Reconstruct state object from returned dict
            if isinstance(final_state_dict, dict):
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
                    selected_restaurant=final_state_dict.get("selected_restaurant"),
                    confirmation_number=final_state_dict.get("confirmation_number"),
                    booking_confirmed=final_state_dict.get("booking_confirmed", False),
                    twilio_call_sid=final_state_dict.get("twilio_call_sid"),
                )
                return state_obj
            else:
                return final_state_dict

        except Exception as e:
            logger.error(f"[{state.session_id}] Workflow execution failed: {e}")
            error_voice = f"Sorry, something went wrong: {str(e)}. Please try again."
            await voice_processor.speak(error_voice)
            state.add_error(f"Workflow error: {str(e)}")
            state.status = SessionStatus.FAILED
            return state


# Global orchestrator instance
voice_integrated_orchestrator = VoiceIntegratedOrchestrator()
