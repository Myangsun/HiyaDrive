"""
Voice processing: Speech-to-Text and Text-to-Speech.
Provides abstraction layer for STT/TTS with mock implementations.
"""

from typing import Optional
import asyncio
from abc import ABC, abstractmethod

from hiya_drive.config.settings import settings
from hiya_drive.utils.logger import logger


class STTProvider(ABC):
    """Abstract base for Speech-to-Text providers."""

    @abstractmethod
    async def transcribe(self, audio_data: bytes) -> str:
        """Transcribe audio to text."""
        pass


class TTSProvider(ABC):
    """Abstract base for Text-to-Speech providers."""

    @abstractmethod
    async def synthesize(self, text: str) -> bytes:
        """Synthesize text to audio."""
        pass


class MockSTT(STTProvider):
    """Mock STT for development/demo."""

    def __init__(self):
        """Initialize with predefined test responses."""
        self.test_responses = [
            "Book a table for 2 at Italian next Friday at 7 PM",
            "Make a reservation for 4 people at a sushi place near Boston",
            "I want to book dinner at a French restaurant tomorrow at 8 PM",
        ]
        self.response_index = 0

    async def transcribe(self, audio_data: bytes) -> str:
        """Return mock transcription."""
        logger.info(f"MockSTT: Transcribing {len(audio_data)} bytes of audio")

        # Cycle through test responses
        response = self.test_responses[self.response_index % len(self.test_responses)]
        self.response_index += 1

        logger.info(f"MockSTT: Transcribed -> '{response}'")
        await asyncio.sleep(0.1)  # Simulate processing delay

        return response


class DeepgramSTT(STTProvider):
    """Deepgram STT implementation."""

    def __init__(self):
        """Initialize Deepgram client."""
        try:
            from deepgram import Deepgram
        except ImportError:
            raise ImportError("deepgram-sdk not installed. Install with: pip install deepgram-sdk")

        self.dg = Deepgram(settings.deepgram_api_key)

    async def transcribe(self, audio_data: bytes) -> str:
        """Transcribe using Deepgram API."""
        logger.info(f"Deepgram: Transcribing {len(audio_data)} bytes")

        try:
            response = await self.dg.transcription.prerecorded(
                {"buffer": audio_data, "mimetype": "audio/wav"},
                {
                    "model": "nova-2",
                    "language": "en",
                    "punctuation": True,
                },
            )

            transcript = response["results"]["channels"][0]["alternatives"][0]["transcript"]
            logger.info(f"Deepgram: Transcribed -> '{transcript}'")

            return transcript

        except Exception as e:
            logger.error(f"Deepgram transcription error: {e}")
            raise


class ElevenLabsSTT(STTProvider):
    """ElevenLabs Speech-to-Text implementation."""

    def __init__(self):
        """Initialize ElevenLabs client for STT."""
        try:
            from elevenlabs import ElevenLabs
        except ImportError:
            raise ImportError("elevenlabs not installed. Install with: pip install elevenlabs")

        if not settings.elevenlabs_api_key:
            raise ValueError("ELEVENLABS_API_KEY must be set")

        self.client = ElevenLabs(api_key=settings.elevenlabs_api_key)

    async def transcribe(self, audio_data: bytes) -> str:
        """Transcribe using ElevenLabs STT API."""
        logger.info(f"ElevenLabsSTT: Transcribing {len(audio_data)} bytes")

        try:
            from pathlib import Path
            import tempfile

            # Create temporary WAV file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(audio_data)
                tmp_path = tmp.name

            try:
                # Use ElevenLabs speech-to-text API
                # The correct API method is speech_to_text.convert()
                with open(tmp_path, "rb") as audio_file:
                    response = self.client.speech_to_text.convert(
                        audio=audio_file,
                        language_code="en"
                    )

                # Extract transcript from response
                transcript = ""
                if isinstance(response, dict):
                    transcript = response.get("text", "")
                else:
                    # If response is an object, try to get text attribute
                    transcript = getattr(response, "text", str(response))

                logger.info(f"ElevenLabsSTT: Transcribed -> '{transcript}'")
                return transcript

            finally:
                # Clean up temp file
                Path(tmp_path).unlink(missing_ok=True)

        except Exception as e:
            logger.error(f"ElevenLabsSTT transcription error: {e}")
            raise


class MockTTS(TTSProvider):
    """Mock TTS for development/demo."""

    def __init__(self):
        """Initialize mock TTS."""
        pass

    async def synthesize(self, text: str) -> bytes:
        """Return mock audio bytes."""
        logger.info(f"MockTTS: Synthesizing '{text}'")

        # Simulate TTS by using macOS say command
        from hiya_drive.voice.audio_io import audio_io
        audio_io.play_text_as_audio(text)

        # Return dummy audio bytes
        await asyncio.sleep(0.2)  # Simulate processing delay
        logger.info(f"MockTTS: Synthesis complete")

        return b"mock_audio_data"


class ElevenLabsTTS(TTSProvider):
    """ElevenLabs TTS implementation."""

    def __init__(self):
        """Initialize ElevenLabs client."""
        try:
            from elevenlabs import ElevenLabs
        except ImportError:
            raise ImportError("elevenlabs not installed. Install with: pip install elevenlabs")

        self.client = ElevenLabs(api_key=settings.elevenlabs_api_key)
        self.voice_id = settings.elevenlabs_voice_id

    async def synthesize(self, text: str) -> bytes:
        """Synthesize using ElevenLabs API."""
        logger.info(f"ElevenLabs: Synthesizing '{text}'")

        try:
            audio = self.client.generate(
                text=text,
                voice=self.voice_id,
                model="eleven_turbo_v2_5",
            )

            audio_bytes = b"".join(audio)
            logger.info(f"ElevenLabs: Synthesis complete ({len(audio_bytes)} bytes)")

            return audio_bytes

        except Exception as e:
            logger.error(f"ElevenLabs synthesis error: {e}")
            raise


class VoiceProcessor:
    """Main voice processing abstraction."""

    def __init__(self):
        """Initialize STT and TTS providers."""
        self._init_stt()
        self._init_tts()

    def _init_stt(self) -> None:
        """Initialize Speech-to-Text provider."""
        if settings.use_mock_stt or settings.demo_mode:
            self.stt = MockSTT()
            logger.info("Using MockSTT")
        else:
            try:
                self.stt = ElevenLabsSTT()
                logger.info("Using ElevenLabs STT")
            except Exception as e:
                logger.warning(f"ElevenLabs STT init failed: {e}, falling back to mock")
                self.stt = MockSTT()

    def _init_tts(self) -> None:
        """Initialize Text-to-Speech provider."""
        if settings.use_mock_tts or settings.demo_mode:
            self.tts = MockTTS()
            logger.info("Using MockTTS")
        else:
            try:
                self.tts = ElevenLabsTTS()
                logger.info("Using ElevenLabs TTS")
            except Exception as e:
                logger.warning(f"ElevenLabs TTS init failed: {e}, falling back to mock")
                self.tts = MockTTS()

    async def transcribe_audio(self, audio_data: bytes) -> str:
        """Transcribe audio to text."""
        return await self.stt.transcribe(audio_data)

    async def synthesize_text(self, text: str) -> bytes:
        """Synthesize text to audio."""
        return await self.tts.synthesize(text)

    async def speak(self, text: str) -> None:
        """Speak text through speaker."""
        logger.info(f"Speaking: {text}")

        try:
            audio_data = await self.synthesize_text(text)

            from hiya_drive.voice.audio_io import audio_io
            await audio_io.play_audio(audio_data, blocking=True)

        except Exception as e:
            logger.error(f"Error speaking: {e}")

    async def listen_and_transcribe(self, duration: float = 5.0) -> str:
        """Listen to microphone and transcribe."""
        logger.info(f"Listening for {duration} seconds...")

        try:
            from hiya_drive.voice.audio_io import audio_io
            audio_data = await audio_io.record_audio(duration)
            transcript = await self.transcribe_audio(audio_data)
            return transcript

        except Exception as e:
            logger.error(f"Error listening/transcribing: {e}")
            return ""


# Global voice processor instance
voice_processor = VoiceProcessor()
