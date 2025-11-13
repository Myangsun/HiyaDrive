"""
Unit tests for voice processing (STT/TTS).
"""

import pytest
import asyncio
from hiya_drive.voice.voice_processor import MockSTT, MockTTS, VoiceProcessor
from hiya_drive.config.settings import settings


class TestMockSTT:
    """Test Mock Speech-to-Text."""

    @pytest.mark.asyncio
    async def test_mock_stt_transcription(self):
        """Test mock STT returns valid transcription."""
        stt = MockSTT()

        result = await stt.transcribe(b"mock_audio_data")

        assert isinstance(result, str)
        assert len(result) > 0
        assert "table" in result.lower() or "book" in result.lower()

    @pytest.mark.asyncio
    async def test_mock_stt_cycles_responses(self):
        """Test mock STT cycles through test responses."""
        stt = MockSTT()

        result1 = await stt.transcribe(b"audio1")
        result2 = await stt.transcribe(b"audio2")
        result3 = await stt.transcribe(b"audio3")

        # All should be valid non-empty strings
        assert all(
            isinstance(r, str) and len(r) > 0 for r in [result1, result2, result3]
        )


class TestMockTTS:
    """Test Mock Text-to-Speech."""

    @pytest.mark.asyncio
    async def test_mock_tts_synthesis(self):
        """Test mock TTS returns audio data."""
        tts = MockTTS()

        # Note: MockTTS doesn't actually generate audio in tests
        result = await tts.synthesize("Hello, this is a test.")

        assert isinstance(result, bytes)


class TestVoiceProcessor:
    """Test VoiceProcessor abstraction."""

    def test_voice_processor_initialization(self):
        """Test voice processor initializes correctly."""
        processor = VoiceProcessor()

        assert processor.stt is not None
        assert processor.tts is not None

    def test_voice_processor_uses_mocks_in_demo(self):
        """Test voice processor uses mocks when demo mode enabled."""
        # In demo mode, should use mocks
        if settings.demo_mode:
            processor = VoiceProcessor()
            assert isinstance(processor.stt, MockSTT)
            assert isinstance(processor.tts, MockTTS)

    @pytest.mark.asyncio
    async def test_transcribe_audio(self):
        """Test transcribing audio."""
        processor = VoiceProcessor()

        transcript = await processor.transcribe_audio(b"mock_audio")

        assert isinstance(transcript, str)
        assert len(transcript) > 0

    @pytest.mark.asyncio
    async def test_synthesize_text(self):
        """Test synthesizing text."""
        processor = VoiceProcessor()

        audio_data = await processor.synthesize_text("Test text")

        assert isinstance(audio_data, bytes)

    @pytest.mark.asyncio
    async def test_speak(self):
        """Test speaking text."""
        processor = VoiceProcessor()

        # Should not raise exception
        await processor.speak("Hello")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
