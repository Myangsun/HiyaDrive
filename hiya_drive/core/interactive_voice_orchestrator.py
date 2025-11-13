"""
Interactive Voice Orchestrator - User feedback-driven booking flow.
Each step asks for user confirmation and generates messages dynamically using LLM.
This is the recommended orchestrator for true conversational booking experience.
"""

import asyncio
import random
from typing import Optional

from hiya_drive.core.orchestrator import BookingOrchestrator, DrivingBookingState
from hiya_drive.models.state import SessionStatus
from hiya_drive.voice.voice_processor import voice_processor
from hiya_drive.voice.llm_message_generator import message_generator
from hiya_drive.integrations.places_service import places_service
from hiya_drive.utils.logger import logger


class InteractiveVoiceOrchestrator(BookingOrchestrator):
    """
    Orchestrator where every step asks for user feedback.
    Uses LLM to generate dynamic messages.
    Truly conversational and interactive.
    """

    async def run_interactive_voice_booking(
        self, driver_id: str, initial_utterance: str
    ) -> DrivingBookingState:
        """
        Run booking with truly continuous listening throughout entire session.
        Agent greets once, then listens continuously for user input.
        User can provide information or corrections at any time.
        """
        from datetime import datetime

        logger.info(f"[{driver_id}] Starting interactive voice booking")

        # Create initial state with required fields
        state = DrivingBookingState(
            session_id=driver_id,
            driver_id=driver_id,
            start_time=datetime.now(),
            last_utterance=initial_utterance
        )

        try:
            # PARSE INITIAL INTENT from user's first message
            logger.info(f"[{state.session_id}] Parsing initial intent from: {initial_utterance}")
            state = await self.parse_intent(state)

            if state.errors:
                error_msg = f"Sorry, I couldn't understand that. {state.errors[0]}"
                await voice_processor.speak(error_msg)
                return state

            # CONFIRM INTENT and ask for missing details
            logger.info(f"[{state.session_id}] Confirming parsed intent")
            intent_confirmation = await message_generator.generate_intent_confirmation(
                party_size=state.party_size,
                cuisine_type=state.cuisine_type,
                location=state.location,
                date=state.requested_date,
                time=state.requested_time,
            )
            await voice_processor.speak(intent_confirmation)
            await asyncio.sleep(0.5)

            # CONTINUOUS LISTENING LOOP - Listen and process user input throughout entire session
            # No more listening at each step, just one continuous conversation
            logger.info(f"[{state.session_id}] Entering continuous listening mode")

            while not self._has_all_required_details(state):
                logger.info(f"[{state.session_id}] Waiting for user input (continuous listening)...")
                user_response = await voice_processor.listen_and_transcribe(duration=60.0)

                if not user_response or user_response.strip() == "":
                    continue

                logger.info(f"[{state.session_id}] User said: {user_response}")

                # Extract any information from user response
                extracted = await message_generator.extract_intent_from_response(
                    user_response=user_response,
                    current_party_size=state.party_size,
                    current_cuisine=state.cuisine_type,
                    current_location=state.location,
                    current_date=state.requested_date,
                    current_time=state.requested_time,
                )

                # Update state with extracted information
                self._update_state_from_extracted(state, extracted)
                logger.info(f"[{state.session_id}] State updated: party_size={state.party_size}, cuisine={state.cuisine_type}, location={state.location}, date={state.requested_date}, time={state.requested_time}")

            # Step 2: Check Calendar
            logger.info(f"[{state.session_id}] Step 2: Checking calendar")
            state = await self.check_calendar(state)

            if state.errors:
                error_msg = "Let me check your calendar..."
                await voice_processor.speak(error_msg)
                await asyncio.sleep(0.5)
            else:
                calendar_msg = await message_generator.generate_calendar_check_message(
                    date=state.requested_date, time=state.requested_time
                )
                await voice_processor.speak(calendar_msg)
                await asyncio.sleep(0.5)

            # Step 3: Search Restaurants
            logger.info(f"[{state.session_id}] Step 3: Searching restaurants")

            search_msg = f"Searching for {state.cuisine_type} restaurants in {state.location}..."
            await voice_processor.speak(search_msg)

            state = await self.search_restaurants(state)

            if state.errors:
                error_msg = (
                    f"Sorry, I couldn't find {state.cuisine_type} restaurants in {state.location}. "
                    "Try a different location or cuisine type."
                )
                await voice_processor.speak(error_msg)
                await asyncio.sleep(0.5)
                return state

            # Announce results
            found_msg = await message_generator.generate_restaurant_found_message(
                count=len(state.restaurant_candidates),
                cuisine_type=state.cuisine_type,
            )
            await voice_processor.speak(found_msg)
            await asyncio.sleep(0.5)

            # Step 4: Present Restaurant Options
            logger.info(f"[{state.session_id}] Step 4: Presenting restaurant options")

            options_intro = "Here are the top options:"
            await voice_processor.speak(options_intro)

            # Present top 3 options with details
            for i, restaurant in enumerate(state.restaurant_candidates[:3], 1):
                option_msg = (
                    f"Option {i}: {restaurant.name}. "
                    f"Rated {restaurant.rating} stars. "
                    f"Located at {restaurant.address}."
                )
                await voice_processor.speak(option_msg)
                await asyncio.sleep(1.2)  # Pause between options

            # Ask which one they prefer (or use highest rated)
            preference_msg = "I'll book the highest-rated option for you. Does that sound good?"
            await voice_processor.speak(preference_msg)
            await asyncio.sleep(0.5)

            # Listen for response
            user_preference = await voice_processor.listen_and_transcribe(duration=3.0)
            logger.info(f"[{state.session_id}] User preference: {user_preference}")

            # Select restaurant (highest rated)
            state = await self.select_restaurant(state)

            if state.errors or not state.selected_restaurant:
                error_msg = "Sorry, I couldn't select a restaurant. Please try again."
                await voice_processor.speak(error_msg)
                await asyncio.sleep(0.5)
                return state

            # Confirm restaurant selection
            selection_msg = await message_generator.generate_restaurant_selection_message(
                restaurant_name=state.selected_restaurant.name,
                rating=state.selected_restaurant.rating,
            )
            await voice_processor.speak(selection_msg)
            await asyncio.sleep(0.5)

            # Step 5: Prepare Call Script
            logger.info(f"[{state.session_id}] Step 5: Preparing call script")

            prep_msg = await message_generator.generate_call_preparation_message(
                restaurant_name=state.selected_restaurant.name
            )
            await voice_processor.speak(prep_msg)

            state = await self.prepare_call(state)

            if state.call_opening_script:
                script_msg = f"I will say: {state.call_opening_script}"
                await voice_processor.speak(script_msg)
                await asyncio.sleep(0.5)

            # Ask for confirmation
            script_confirm = "Should I call them now?"
            await voice_processor.speak(script_confirm)

            user_confirm = await voice_processor.listen_and_transcribe(duration=3.0)
            logger.info(f"[{state.session_id}] User confirmation: {user_confirm}")

            if user_confirm and "no" in user_confirm.lower():
                cancel_msg = "No problem. Your reservation hasn't been made."
                await voice_processor.speak(cancel_msg)
                await asyncio.sleep(0.5)
                return state

            # Step 6: Make Call
            logger.info(f"[{state.session_id}] Step 6: Making call")

            call_msg = await message_generator.generate_call_initiation_message(
                restaurant_name=state.selected_restaurant.name
            )
            await voice_processor.speak(call_msg)
            await asyncio.sleep(0.5)

            state = await self.make_call(state)

            if state.errors:
                error_msg = "Sorry, I couldn't reach the restaurant. Please try again later."
                await voice_processor.speak(error_msg)
                await asyncio.sleep(0.5)
                return state

            # Connected!
            connected_msg = f"Connected to {state.selected_restaurant.name}!"
            await voice_processor.speak(connected_msg)
            await asyncio.sleep(1)

            # Step 7: Converse
            logger.info(f"[{state.session_id}] Step 7: Conversing with restaurant")

            await voice_processor.speak("Speaking with the restaurant...")
            state = await self.converse(state)
            await asyncio.sleep(0.5)

            if not state.booking_confirmed:
                error_msg = "The restaurant couldn't confirm your booking. Please try again."
                await voice_processor.speak(error_msg)
                await asyncio.sleep(0.5)
                return state

            # Step 8: Confirm Booking
            logger.info(f"[{state.session_id}] Step 8: Confirming booking")

            confirmation_msg = await message_generator.generate_booking_confirmation(
                restaurant_name=state.selected_restaurant.name,
                party_size=state.party_size,
                date=state.requested_date,
                time=state.requested_time,
                confirmation_number=state.confirmation_number or "pending",
            )
            await voice_processor.speak(confirmation_msg)
            await asyncio.sleep(1)

            # Goodbye
            goodbye = await message_generator.generate_goodbye()
            await voice_processor.speak(goodbye)
            await asyncio.sleep(0.5)

            state.status = SessionStatus.COMPLETED
            logger.info(f"[{state.session_id}] Booking completed successfully")

        except Exception as e:
            logger.error(f"[{state.session_id}] Error in interactive booking: {e}")
            state.add_error(f"Booking error: {str(e)}")
            error_msg = "Sorry, something went wrong. Please try again."
            await voice_processor.speak(error_msg)
            await asyncio.sleep(0.5)

        return state

    def _has_all_required_details(self, state: DrivingBookingState) -> bool:
        """Check if all required booking details are present."""
        return all([
            state.party_size,
            state.cuisine_type,
            state.location,
            state.requested_date,
            state.requested_time,
        ])

    def _update_state_from_extracted(self, state: DrivingBookingState, extracted: dict) -> None:
        """Update state with extracted information from user response."""
        if extracted.get("party_size"):
            state.party_size = extracted["party_size"]
        if extracted.get("cuisine_type"):
            state.cuisine_type = extracted["cuisine_type"]
        if extracted.get("location"):
            state.location = extracted["location"]
        if extracted.get("date"):
            state.requested_date = extracted["date"]
        if extracted.get("time"):
            state.requested_time = extracted["time"]


# Global orchestrator instance
interactive_voice_orchestrator = InteractiveVoiceOrchestrator()
