"""
Wake word detection for voice activation.
Detects the "hiya" wake word from audio input.
"""

import asyncio
import re
from difflib import SequenceMatcher
from hiya_drive.config.settings import settings
from hiya_drive.utils.logger import logger
from hiya_drive.voice.voice_processor import voice_processor


class WakeWordDetector:
    """Detects wake word from continuous audio stream."""

    def __init__(self):
        """Initialize wake word detector."""
        self.wake_word = settings.wake_word.lower()
        self.enabled = settings.enable_wake_word_detection
        self.similarity_threshold = 0.7  # 70% match required
        logger.info(
            f"Wake word detector initialized: '{self.wake_word}' (threshold: {self.similarity_threshold})"
        )

    def _detect_wake_word(self, transcript: str) -> bool:
        """
        Detect wake word using fuzzy matching.

        Args:
            transcript: Transcribed text to check

        Returns:
            True if wake word detected with sufficient confidence
        """
        if not transcript:
            return False

        text_lower = transcript.lower()

        # Method 1: Exact substring match (fastest)
        if self.wake_word in text_lower:
            logger.info(f"✓ Exact match found for '{self.wake_word}'")
            return True

        # Method 2: Extract single words and fuzzy match them
        # Remove punctuation and split into words
        words = re.findall(r"\b\w+\b", text_lower)

        for word in words:
            # Calculate similarity between word and wake word
            similarity = SequenceMatcher(None, self.wake_word, word).ratio()

            if similarity >= self.similarity_threshold:
                logger.info(
                    f"✓ Fuzzy match found: '{word}' matches '{self.wake_word}' "
                    f"(confidence: {similarity:.1%})"
                )
                return True

        return False

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
                    logger.info(f"Heard: '{transcript}'")

                    # Use fuzzy matching to detect wake word
                    if self._detect_wake_word(transcript):
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
            # Greet immediately after wake word detection
            await self._greet_user()

        return detected

    async def _greet_user(self) -> None:
        """Greet the user after wake word detection using LLM-generated message."""
        from hiya_drive.voice.llm_message_generator import message_generator

        try:
            # Use LLM to generate dynamic greeting
            greeting = await message_generator.generate_greeting()
            logger.info(f"Greeting user with LLM-generated message: {greeting}")
            await voice_processor.speak(greeting)
        except Exception as e:
            logger.error(f"Error generating greeting: {e}")
            # Fallback to simple greeting if LLM fails
            await voice_processor.speak("Hi! I'm HiyaDrive. How can I help you today?")


# Global wake word detector instance
wake_word_detector = WakeWordDetector()
