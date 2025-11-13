"""
Advanced interactive orchestrator with restaurant selection and step-by-step confirmations.
"""

from typing import List, Optional
import asyncio
from hiya_drive.core.interactive_orchestrator import InteractiveBookingOrchestrator
from hiya_drive.models.state import DrivingBookingState, Restaurant
from hiya_drive.voice.voice_processor import voice_processor
from hiya_drive.utils.logger import logger


class AdvancedInteractiveOrchestrator(InteractiveBookingOrchestrator):
    """Most advanced orchestrator with full interactive features."""

    async def select_restaurant_with_options(self, state: DrivingBookingState) -> Optional[Restaurant]:
        """
        Present restaurant options and let user (eventually) select one via voice.
        For now, auto-selects the best-rated option and announces it.
        """
        if not state.restaurant_candidates:
            message = "Sorry, I couldn't find any restaurants matching your criteria. Please try a different search."
            logger.warning(f"🍽️  {message}")
            await voice_processor.speak(message)
            return None

        message = f"Great! I found {len(state.restaurant_candidates)} wonderful restaurants for you!"
        logger.info(f"🍽️  {message}")
        await voice_processor.speak(message)
        await asyncio.sleep(0.5)

        # Present top 3 options
        top_options = state.restaurant_candidates[:3]
        for i, restaurant in enumerate(top_options, 1):
            option_msg = (
                f"Option {i}: {restaurant.name}. "
                f"Rating: {restaurant.rating} stars. "
                f"Address: {restaurant.address}"
            )
            logger.info(f"   {option_msg}")
            await voice_processor.speak(option_msg)
            await asyncio.sleep(0.8)

        # Auto-select the best option
        selected = max(top_options, key=lambda r: r.rating)
        selection_msg = f"I'll book the highest-rated restaurant: {selected.name} with {selected.rating} stars."
        logger.info(f"✓ Auto-selected: {selection_msg}")
        await voice_processor.speak(selection_msg)
        
        return selected

    async def run_advanced_interactive_booking_session(
        self,
        driver_id: str,
        initial_utterance: str,
    ) -> DrivingBookingState:
        """
        Run a complete advanced interactive booking session with full voice confirmations
        and option presentation at each step.
        """
        logger.info("\n" + "=" * 70)
        logger.info("ADVANCED INTERACTIVE BOOKING SESSION WITH VOICE OPTIONS")
        logger.info("=" * 70)

        # Step 1: Greet the user
        logger.info("\n📍 STEP 1: GREETING")
        await self.greet_user()
        await asyncio.sleep(1.5)

        # Step 2: Parse and confirm booking details
        logger.info("\n📍 STEP 2: PARSING BOOKING REQUEST")
        state = DrivingBookingState(
            session_id="",
            driver_id=driver_id,
            start_time=None,
            last_utterance=initial_utterance,
        )

        # Parse the intent using Claude
        parsed_state = await self.parse_intent(state)
        detail_msg = (
            f"I understood you want to book for {parsed_state.party_size} people. "
            f"Looking for {parsed_state.cuisine_type} restaurants in {parsed_state.location}. "
            f"Date: {parsed_state.requested_date} at {parsed_state.requested_time}."
        )
        logger.info(f"✓ Parsed: {detail_msg}")
        await voice_processor.speak(detail_msg)
        await asyncio.sleep(1)

        # Step 3: Check calendar
        logger.info("\n📍 STEP 3: CHECKING CALENDAR")
        await self.confirm_calendar_check(parsed_state)
        await asyncio.sleep(1)

        # Step 4: Search restaurants
        logger.info("\n📍 STEP 4: SEARCHING RESTAURANTS")
        search_msg = f"Let me search for {parsed_state.cuisine_type} restaurants in {parsed_state.location}..."
        logger.info(f"🔍 Searching: {search_msg}")
        await voice_processor.speak(search_msg)
        await asyncio.sleep(0.5)

        searched_state = await self.search_restaurants(parsed_state)
        await asyncio.sleep(1)

        # Step 5: Present and select restaurant
        logger.info("\n📍 STEP 5: SELECTING RESTAURANT")
        selected_restaurant = await self.select_restaurant_with_options(searched_state)
        if selected_restaurant:
            searched_state.selected_restaurant = selected_restaurant
        await asyncio.sleep(1)

        # Step 6: Prepare call
        logger.info("\n📍 STEP 6: PREPARING CALL")
        prepared_state = await self.prepare_call(searched_state)
        if prepared_state.call_opening_script:
            script_msg = f"I will say: {prepared_state.call_opening_script}"
            logger.info(f"🗣️  Script: {script_msg}")
            await voice_processor.speak(script_msg)
            await asyncio.sleep(0.5)

        # Step 7: Make the call
        logger.info("\n📍 STEP 7: MAKING CALL")
        call_msg = f"Now I'll call {prepared_state.selected_restaurant.name} at {prepared_state.selected_restaurant.phone}"
        logger.info(f"📞 Calling: {call_msg}")
        await voice_processor.speak(call_msg)
        await asyncio.sleep(1)

        called_state = await self.make_call(prepared_state)
        await asyncio.sleep(1)

        # Step 8: Conversation
        logger.info("\n📍 STEP 8: RESTAURANT CONVERSATION")
        converse_state = await self.converse(called_state)
        await asyncio.sleep(0.5)

        # Step 9: Confirm booking
        logger.info("\n📍 STEP 9: BOOKING CONFIRMATION")
        if converse_state.booking_confirmed:
            await self.confirm_booking(converse_state)
        await asyncio.sleep(1)

        # Step 10: Say goodbye
        logger.info("\n📍 STEP 10: GOODBYE")
        await self.say_goodbye()

        logger.info("=" * 70)
        return converse_state


# Global advanced orchestrator instance
advanced_interactive_orchestrator = AdvancedInteractiveOrchestrator()
