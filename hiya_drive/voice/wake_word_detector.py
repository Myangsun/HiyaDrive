"""
Wake word detection for voice activation.
Detects the "hiya" wake word from audio input.
"""

import asyncio
from hiya_drive.config.settings import settings
from hiya_drive.utils.logger import logger
from hiya_drive.voice.voice_processor import voice_processor


class WakeWordDetector:
    """Detects wake word from continuous audio stream."""

    def __init__(self):
        """Initialize wake word detector."""
        self.wake_word = settings.wake_word.lower()
        self.enabled = settings.enable_wake_word_detection
        logger.info(f"Wake word detector initialized: '{self.wake_word}'")

    async def listen_for_wake_word(self, timeout: float = 120.0) -> bool:
        """
        Listen for wake word in microphone input.

        Args:
            timeout: Maximum time to listen (seconds)

        Returns:
            True if wake word detected, False if timeout
        """
        if not self.enabled:
            return True

        logger.info(f"Listening for wake word '{self.wake_word}' (timeout: {timeout}s)")

        start_time = asyncio.get_event_loop().time()

        try:
            while True:
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed > timeout:
                    logger.warning(f"Wake word detection timeout after {timeout}s")
                    return False

                # Listen for audio chunks and check for wake word
                # Using shorter chunks for responsiveness
                chunk_duration = 2.0  # 2 second chunks
                transcript = await voice_processor.listen_and_transcribe(
                    duration=chunk_duration
                )

                if transcript:
                    transcript_lower = transcript.lower()
                    logger.info(f"Heard: '{transcript}'")

                    if self.wake_word in transcript_lower:
                        logger.info(f"✓ Wake word '{self.wake_word}' detected!")
                        return True

                    # Continue listening if wake word not found
                    logger.debug("Wake word not detected, continuing to listen...")

        except Exception as e:
            logger.error(f"Error in wake word detection: {e}")
            return False

    async def listen_for_wake_word_and_greet(self, timeout: float = 120.0) -> bool:
        """
        Listen for wake word and greet the user if detected.

        Args:
            timeout: Maximum time to listen (seconds)

        Returns:
            True if wake word detected and greeting given, False if timeout
        """
        detected = await self.listen_for_wake_word(timeout)

        if detected:
            # Greet the user
            await self._greet_user()

        return detected

    async def _greet_user(self) -> None:
        """Greet the user after wake word detection."""
        greetings = [
            "Hi! I'm HiyaDrive. How can I help you today?",
            "Hey there! What can I do for you?",
            "I'm here to help. What do you need?",
        ]

        import random

        greeting = random.choice(greetings)

        logger.info(f"Greeting user: {greeting}")
        await voice_processor.speak(greeting)


# Global wake word detector instance
wake_word_detector = WakeWordDetector()
