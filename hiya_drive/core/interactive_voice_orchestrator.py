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
        Ensures consistent voice and single goodbye at the end.
        """
        from datetime import datetime

        logger.info(f"[{driver_id}] Starting interactive voice booking")

        # Create initial state with required fields
        state = DrivingBookingState(
            session_id=driver_id,
            driver_id=driver_id,
            start_time=datetime.now(),
            last_utterance=initial_utterance,
        )

        try:
            # PARSE INITIAL INTENT from user's first message
            logger.info(
                f"[{state.session_id}] Parsing initial intent from: {initial_utterance}"
            )
            state = await self.parse_intent(state)

            if state.errors:
                error_msg = f"Sorry, I couldn't understand that. {state.errors[0]}"
                await voice_processor.speak(error_msg)
                state.status = SessionStatus.FAILED
            else:
                # CONFIRM INTENT and ask for missing details
                logger.info(f"[{state.session_id}] Confirming parsed intent")
                intent_confirmation = (
                    await message_generator.generate_intent_confirmation(
                        party_size=state.party_size,
                        cuisine_type=state.cuisine_type,
                        location=state.location,
                        date=state.requested_date,
                        time=state.requested_time,
                    )
                )
                await voice_processor.speak(intent_confirmation)
                await asyncio.sleep(0.5)

                # CONTINUOUS LISTENING LOOP - Listen and process user input throughout entire session
                # No more listening at each step, just one continuous conversation
                logger.info(f"[{state.session_id}] Entering continuous listening mode")

                while not self._has_all_required_details(state):
                    logger.info(
                        f"[{state.session_id}] Waiting for user input (continuous listening)..."
                    )
                    user_response = await voice_processor.listen_and_transcribe(
                        duration=60.0
                    )

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
                    logger.info(
                        f"[{state.session_id}] State updated: party_size={state.party_size}, cuisine={state.cuisine_type}, location={state.location}, date={state.requested_date}, time={state.requested_time}"
                    )

                # Step 1 Confirmation - All details collected
                logger.info(
                    f"[{state.session_id}] Step 1 Complete: All booking details confirmed"
                )
                step1_confirmation = (
                    f"Perfect! I have confirmed your booking request: {state.party_size} people at a "
                    f"{state.cuisine_type} restaurant in {state.location} on {state.requested_date} at {state.requested_time}. "
                    f"Let me proceed with checking your availability."
                )
                await voice_processor.speak(step1_confirmation)
                await asyncio.sleep(0.5)

                # Step 2: Check Calendar - with retry logic for unavailable times
                logger.info(f"[{state.session_id}] Step 2: Checking calendar")

                max_calendar_retries = 3
                calendar_attempt = 0
                calendar_confirmed = False

                while (
                    calendar_attempt < max_calendar_retries and not calendar_confirmed
                ):
                    calendar_attempt += 1
                    logger.info(
                        f"[{state.session_id}] Calendar check attempt {calendar_attempt}/{max_calendar_retries}"
                    )

                    # Announce we're checking calendar
                    if calendar_attempt == 1:
                        announce_check = (
                            "Now let me check your calendar availability..."
                        )
                    else:
                        announce_check = "Let me check that time..."
                    await voice_processor.speak(announce_check)
                    await asyncio.sleep(0.5)

                    state = await self.check_calendar(state)

                    if state.errors:
                        # Calendar API failure - fatal error
                        error_msg = f"Sorry, I couldn't check your calendar. Error: {state.errors[0]}"
                        await voice_processor.speak(error_msg)
                        await asyncio.sleep(0.5)
                        state.status = SessionStatus.FAILED
                        break
                    elif state.driver_calendar_free:
                        # User is available at this time!
                        availability_msg = f"Great! You are available at {state.requested_time} on {state.requested_date}."
                        await voice_processor.speak(availability_msg)
                        logger.info(
                            f"[{state.session_id}] Calendar check passed - user available at {state.requested_time}"
                        )
                        calendar_confirmed = True
                    else:
                        # User is BUSY at this time - ask for different time
                        logger.info(
                            f"[{state.session_id}] User is busy at {state.requested_time} on {state.requested_date}"
                        )
                        busy_msg = (
                            f"You're already busy at {state.requested_time} on {state.requested_date}. "
                            f"What time would work better for you?"
                        )
                        await voice_processor.speak(busy_msg)
                        await asyncio.sleep(0.5)

                        # Listen for new time
                        new_time_response = await voice_processor.listen_and_transcribe(
                            duration=10.0
                        )
                        logger.info(
                            f"[{state.session_id}] User suggested new time: {new_time_response}"
                        )

                        if not new_time_response or new_time_response.strip() == "":
                            # No response, ask again
                            logger.debug(
                                f"[{state.session_id}] No time provided, retrying..."
                            )
                            continue

                        # Extract time from response using LLM
                        try:
                            extracted = (
                                await message_generator.extract_intent_from_response(
                                    user_response=new_time_response,
                                    current_party_size=state.party_size,
                                    current_cuisine=state.cuisine_type,
                                    current_location=state.location,
                                    current_date=state.requested_date,
                                    current_time=state.requested_time,
                                )
                            )

                            # Update time if extraction found a new time
                            if extracted.get("time"):
                                state.requested_time = extracted["time"]
                                logger.info(
                                    f"[{state.session_id}] Updated time to: {state.requested_time}"
                                )
                            # Also check if date was updated
                            if extracted.get("date"):
                                state.requested_date = extracted["date"]
                                logger.info(
                                    f"[{state.session_id}] Updated date to: {state.requested_date}"
                                )

                            # Clear previous errors for retry
                            state.errors = []
                            # Retry calendar check with new time
                            continue

                        except Exception as e:
                            logger.error(
                                f"[{state.session_id}] Failed to extract new time: {e}"
                            )
                            retry_msg = "I couldn't understand the new time. Could you please say it again?"
                            await voice_processor.speak(retry_msg)
                            await asyncio.sleep(0.5)
                            continue

                # Check if we gave up on finding available time
                if (
                    state.status not in [SessionStatus.FAILED, SessionStatus.CANCELLED]
                    and not calendar_confirmed
                ):
                    logger.warning(
                        f"[{state.session_id}] Gave up on finding available time after {max_calendar_retries} attempts"
                    )
                    gave_up_msg = f"I couldn't find an available time after {max_calendar_retries} attempts. Please try again later."
                    await voice_processor.speak(gave_up_msg)
                    await asyncio.sleep(0.5)
                    state.status = SessionStatus.FAILED

                await asyncio.sleep(0.5)

                # Only proceed if calendar was confirmed
                if state.status not in [SessionStatus.FAILED, SessionStatus.CANCELLED]:
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
                        state.status = SessionStatus.FAILED
                    else:
                        # Announce results
                        found_msg = (
                            await message_generator.generate_restaurant_found_message(
                                count=len(state.restaurant_candidates),
                                cuisine_type=state.cuisine_type,
                            )
                        )
                        await voice_processor.speak(found_msg)
                        await asyncio.sleep(0.5)

                        # Step 4: Present Restaurant Options with Continuous Listening
                        logger.info(
                            f"[{state.session_id}] Step 4: Presenting restaurant options"
                        )

                        options_intro = "Here are the top options:"
                        await voice_processor.speak(options_intro)
                        await asyncio.sleep(0.5)

                        # Present top 3 options with details
                        num_options = min(3, len(state.restaurant_candidates))
                        for i, restaurant in enumerate(
                            state.restaurant_candidates[:num_options], 1
                        ):
                            option_msg = (
                                f"Option {i}: {restaurant.name}. "
                                f"Rated {restaurant.rating} stars. "
                                f"Located at {restaurant.address}."
                            )
                            await voice_processor.speak(option_msg)
                            await asyncio.sleep(1.2)  # Pause between options

                        # Continuous listening loop for restaurant selection
                        max_attempts = 3
                        attempt = 0
                        selected_option = None

                        while attempt < max_attempts and selected_option is None:
                            attempt += 1

                            if attempt == 1:
                                # First attempt: ask which one they prefer
                                selection_msg = "Which one would you like? Just say the option number."
                            else:
                                # Retry: ask again
                                selection_msg = f"I didn't catch that. Please tell me option 1, 2, or 3."

                            await voice_processor.speak(selection_msg)
                            await asyncio.sleep(0.5)

                            # Listen for user's selection
                            user_response = await voice_processor.listen_and_transcribe(
                                duration=10.0
                            )
                            logger.info(
                                f"[{state.session_id}] User response (attempt {attempt}): {user_response}"
                            )

                            if not user_response or user_response.strip() == "":
                                logger.debug(
                                    f"[{state.session_id}] No response detected, retrying..."
                                )
                                continue

                            # Extract which option they selected using LLM
                            selection_result = (
                                await message_generator.extract_restaurant_selection(
                                    user_response=user_response, num_options=num_options
                                )
                            )

                            selected_option = selection_result.get("selected_option")
                            confidence = selection_result.get("confidence", "low")
                            feedback = selection_result.get("feedback", "")

                            logger.info(
                                f"[{state.session_id}] Selection extraction - option: {selected_option}, confidence: {confidence}, feedback: {feedback}"
                            )

                            # Accept selection if high confidence or medium confidence
                            if selected_option is not None and confidence in [
                                "high",
                                "medium",
                            ]:
                                logger.info(
                                    f"[{state.session_id}] User selected option {selected_option}"
                                )
                                break
                            else:
                                # Low confidence or no clear selection, retry
                                logger.debug(
                                    f"[{state.session_id}] Selection unclear (confidence: {confidence}), retrying..."
                                )
                                selected_option = None

                        # Select the restaurant based on user choice or default to highest-rated
                        state = await self.select_restaurant(
                            state, user_choice=selected_option
                        )

                        if state.errors or not state.selected_restaurant:
                            error_msg = "Sorry, I couldn't select a restaurant. Please try again."
                            await voice_processor.speak(error_msg)
                            await asyncio.sleep(0.5)
                            state.status = SessionStatus.FAILED
                        elif not state.errors:
                            # Skip confirmation message - we'll provide feedback when calling
                            pass

                        # Step 5: Prepare Call Script
                        logger.info(
                            f"[{state.session_id}] Step 5: Preparing call script"
                        )

                        # Prepare the call opening script
                        state = await self.prepare_call(state)

                        # Simply announce we're about to call
                        call_announce = (
                            f"I'm about to call {state.selected_restaurant.name}."
                        )
                        await voice_processor.speak(call_announce)
                        await asyncio.sleep(0.5)

                        # Ask for confirmation
                        script_confirm = "Should I call them now?"
                        await voice_processor.speak(script_confirm)

                        user_confirm = await voice_processor.listen_and_transcribe(
                            duration=3.0
                        )
                        logger.info(
                            f"[{state.session_id}] User confirmation: {user_confirm}"
                        )

                        if user_confirm and "no" in user_confirm.lower():
                            cancel_msg = (
                                "No problem. Your reservation hasn't been made."
                            )
                            await voice_processor.speak(cancel_msg)
                            await asyncio.sleep(0.5)
                            state.status = SessionStatus.CANCELLED

                        # Only proceed if no errors or cancellation
                        if state.status not in [
                            SessionStatus.FAILED,
                            SessionStatus.CANCELLED,
                        ]:
                            # Step 6: Make Call
                            logger.info(f"[{state.session_id}] Step 6: Making call")

                            state = await self.make_call(state)

                            if state.errors:
                                error_msg = "Sorry, I couldn't reach the restaurant. Please try again later."
                                await voice_processor.speak(error_msg)
                                await asyncio.sleep(0.5)
                                state.status = SessionStatus.FAILED
                            else:
                                # Connected!
                                connected_msg = (
                                    f"Connected to {state.selected_restaurant.name}!"
                                )
                                await voice_processor.speak(connected_msg)
                                await asyncio.sleep(1)

                                # Step 7: Converse
                                logger.info(
                                    f"[{state.session_id}] Step 7: Conversing with restaurant"
                                )

                                await voice_processor.speak(
                                    "Speaking with the restaurant..."
                                )
                                state = await self.converse(state)
                                await asyncio.sleep(0.5)

                        # Only proceed to Step 8 if still no errors
                        if state.status not in [
                            SessionStatus.FAILED,
                            SessionStatus.CANCELLED,
                        ]:
                            if not state.booking_confirmed:
                                error_msg = "The restaurant couldn't confirm your booking. Please try again."
                                await voice_processor.speak(error_msg)
                                await asyncio.sleep(0.5)
                                state.status = SessionStatus.FAILED
                            else:
                                # Step 8: Confirm Booking
                                logger.info(
                                    f"[{state.session_id}] Step 8: Confirming booking"
                                )
                                logger.info(
                                    f"[{state.session_id}] Reservation confirmed at {state.selected_restaurant.name} for {state.party_size} on {state.requested_date} at {state.requested_time}. Confirmation #: {state.confirmation_number or 'pending'}"
                                )

                                # Add reservation to calendar
                                try:
                                    from hiya_drive.integrations.calendar_service import (
                                        calendar_service,
                                    )

                                    # Format the reservation time for calendar
                                    calendar_time_str = f"{state.requested_date} at {state.requested_time}"

                                    # Add the event to Google Calendar
                                    success = await calendar_service.add_reservation_event(
                                        restaurant_name=state.selected_restaurant.name,
                                        reservation_time=calendar_time_str,
                                        party_size=state.party_size,
                                        duration_minutes=120,
                                        confirmation_number=state.confirmation_number,
                                    )

                                    if success:
                                        logger.info(
                                            f"[{state.session_id}] Reservation added to calendar successfully"
                                        )
                                        calendar_status = "Added to calendar"
                                        # Inform user
                                        calendar_confirm = "I've saved your reservation to your calendar."
                                        await voice_processor.speak(calendar_confirm)
                                        await asyncio.sleep(0.5)
                                    else:
                                        logger.warning(
                                            f"[{state.session_id}] Failed to add reservation to calendar"
                                        )
                                        calendar_status = "Failed to add to calendar"

                                except Exception as cal_error:
                                    logger.warning(
                                        f"[{state.session_id}] Could not add to calendar: {cal_error}"
                                    )
                                    calendar_status = (
                                        f"Failed to add to calendar: {str(cal_error)}"
                                    )

                                state.status = SessionStatus.COMPLETED
                                logger.info(
                                    f"[{state.session_id}] Booking completed successfully - {calendar_status}"
                                )

                # SINGLE GOODBYE - Always executed regardless of status
                logger.info(
                    f"[{state.session_id}] Session ending with status: {state.status}"
                )
                goodbye = await message_generator.generate_goodbye()
                await voice_processor.speak(goodbye)

        except Exception as e:
            logger.error(f"[{state.session_id}] Error in interactive booking: {e}")
            state.add_error(f"Booking error: {str(e)}")
            state.status = SessionStatus.FAILED
            error_msg = "Sorry, something went wrong. Please try again."
            await voice_processor.speak(error_msg)
            await asyncio.sleep(0.5)

            # Say goodbye even on exception
            try:
                goodbye = await message_generator.generate_goodbye()
                await voice_processor.speak(goodbye)
            except Exception as goodbye_error:
                logger.warning(f"Could not say goodbye: {goodbye_error}")

        return state

    def _has_all_required_details(self, state: DrivingBookingState) -> bool:
        """Check if all required booking details are present."""
        return all(
            [
                state.party_size,
                state.cuisine_type,
                state.location,
                state.requested_date,
                state.requested_time,
            ]
        )

    def _update_state_from_extracted(
        self, state: DrivingBookingState, extracted: dict
    ) -> None:
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
