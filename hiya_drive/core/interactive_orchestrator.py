"""
Enhanced orchestrator with voice confirmations at each step.
Extends BookingOrchestrator to add interactive voice interactions.
"""

from typing import Optional
import asyncio
from datetime import datetime

from hiya_drive.core.orchestrator import BookingOrchestrator
from hiya_drive.models.state import DrivingBookingState
from hiya_drive.voice.voice_processor import voice_processor
from hiya_drive.utils.logger import logger


class InteractiveBookingOrchestrator(BookingOrchestrator):
    """Enhanced orchestrator with voice-based user interactions."""

    async def greet_user(self) -> None:
        """Greet the user with voice."""
        greetings = [
            "Welcome to HiyaDrive! I'm ready to help you book a restaurant. What would you like to order?",
            "Hi! I'm HiyaDrive, your personal booking assistant. Where would you like to eat today?",
            "Hello! I'm here to help you book a table. Tell me what kind of food you're craving!",
        ]
        import random
        greeting = random.choice(greetings)
        logger.info(f"🎤 Greeting: {greeting}")
        await voice_processor.speak(greeting)

    async def confirm_calendar_check(self, state: DrivingBookingState) -> None:
        """Confirm calendar availability with voice."""
        if state.driver_calendar_free:
            message = f"Great! I checked your calendar and you're available on {state.requested_date} at {state.requested_time}. That works perfectly!"
        else:
            message = f"I see you might have a conflict on {state.requested_date} at {state.requested_time}, but I'll proceed with the booking."
        
        logger.info(f"📅 Calendar: {message}")
        await voice_processor.speak(message)

    async def present_restaurants(self, state: DrivingBookingState) -> None:
        """Present restaurant options with voice."""
        if not state.restaurant_candidates:
            message = f"Sorry, I couldn't find any restaurants matching your criteria. Please try a different search."
            logger.warning(f"🍽️  {message}")
            await voice_processor.speak(message)
            return

        message = f"I found {len(state.restaurant_candidates)} great options for you!"
        logger.info(f"🍽️  {message}")
        await voice_processor.speak(message)
        
        # Read out the top 3 options
        for i, restaurant in enumerate(state.restaurant_candidates[:3], 1):
            option_msg = f"Option {i}: {restaurant.name} with a {restaurant.rating} star rating"
            logger.info(f"   {option_msg}")
            await voice_processor.speak(option_msg)
            await asyncio.sleep(0.5)  # Slight pause between options

    async def confirm_restaurant_selection(self, state: DrivingBookingState) -> None:
        """Confirm the selected restaurant with voice."""
        if not state.selected_restaurant:
            return
        
        message = (
            f"Perfect! I'm booking {state.selected_restaurant.name} for {state.party_size} people "
            f"on {state.requested_date} at {state.requested_time}. "
            f"Their number is {state.selected_restaurant.phone}."
        )
        logger.info(f"✓ Selected: {message}")
        await voice_processor.speak(message)

    async def announce_call(self, state: DrivingBookingState) -> None:
        """Announce that we're making the call."""
        if not state.selected_restaurant or not state.call_opening_script:
            return
        
        message = f"Now let me call {state.selected_restaurant.name} to complete your reservation."
        logger.info(f"📞 Calling: {message}")
        await voice_processor.speak(message)
        
        # Brief pause before "calling"
        await asyncio.sleep(1)
        
        calling_msg = f"Dialing {state.selected_restaurant.phone}..."
        logger.info(f"   {calling_msg}")
        await voice_processor.speak(calling_msg)

    async def announce_call_script(self, state: DrivingBookingState) -> None:
        """Announce the script being used for the call."""
        if not state.call_opening_script:
            return
        
        message = f"I'll say: {state.call_opening_script}"
        logger.info(f"🗣️  Script: {message}")
        await voice_processor.speak(message)

    async def confirm_booking(self, state: DrivingBookingState) -> None:
        """Announce the confirmed booking with voice."""
        if not state.booking_confirmed or not state.selected_restaurant:
            return
        
        message = (
            f"Excellent! Your reservation is confirmed! "
            f"I've booked {state.selected_restaurant.name} for {state.party_size} people. "
            f"Your confirmation number is {state.confirmation_number}. "
            f"Have a wonderful meal!"
        )
        logger.info(f"✅ Confirmed: {message}")
        await voice_processor.speak(message)

    async def say_goodbye(self) -> None:
        """Say goodbye to the user."""
        farewells = [
            "Thanks for using HiyaDrive! Enjoy your meal!",
            "Your reservation is all set! Have a fantastic time!",
            "All done! I hope you have a wonderful dining experience!",
            "Safe travels and enjoy your meal! Feel free to ask me anytime!",
        ]
        import random
        farewell = random.choice(farewells)
        logger.info(f"👋 Goodbye: {farewell}")
        await voice_processor.speak(farewell)

    async def run_interactive_booking_session(
        self,
        driver_id: str,
        initial_utterance: str,
    ) -> DrivingBookingState:
        """
        Run a complete interactive booking session with voice confirmations.
        
        Args:
            driver_id: The driver's ID
            initial_utterance: User's booking request
            
        Returns:
            Final booking state
        """
        logger.info("\n" + "=" * 70)
        logger.info("INTERACTIVE BOOKING SESSION")
        logger.info("=" * 70)
        
        # Greet the user
        await self.greet_user()
        await asyncio.sleep(1)
        
        # Run the main booking workflow
        result = await self.run_booking_session(driver_id, initial_utterance)
        
        # Get the state object details for voice confirmations
        if result.status == "completed":
            # Confirm calendar
            if result.driver_calendar_free:
                await self.confirm_calendar_check(result)
                await asyncio.sleep(0.5)
            
            # Present restaurants
            if result.restaurant_candidates:
                await self.present_restaurants(result)
                await asyncio.sleep(1)
            
            # Confirm selection
            await self.confirm_restaurant_selection(result)
            await asyncio.sleep(0.5)
            
            # Announce call
            await self.announce_call(result)
            await asyncio.sleep(0.5)
            
            # Announce booking
            await self.confirm_booking(result)
            await asyncio.sleep(0.5)
        
        # Say goodbye
        await self.say_goodbye()
        
        logger.info("=" * 70)
        return result


# Global interactive orchestrator instance
interactive_orchestrator = InteractiveBookingOrchestrator()
