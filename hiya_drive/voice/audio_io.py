"""
Audio I/O for Mac: microphone input and speaker output.
Uses PyAudio for cross-platform audio handling.
"""

import pyaudio
import numpy as np
from typing import Optional, Callable
import threading
import queue
import asyncio
from pathlib import Path

from hiya_drive.config.settings import settings
from hiya_drive.utils.logger import logger


class MacAudioIO:
    """Handle audio input/output for Mac."""

    def __init__(self):
        """Initialize PyAudio and settings."""
        self.pyaudio = pyaudio.PyAudio()
        self.sample_rate = settings.sample_rate
        self.channels = settings.channels
        self.chunk_size = settings.audio_chunk_size
        self.silence_threshold = settings.silence_threshold

        self.input_stream = None
        self.output_stream = None
        self.audio_queue = queue.Queue()
        self.is_listening = False

    def list_devices(self) -> None:
        """List available audio devices."""
        logger.info("Available audio devices:")
        for i in range(self.pyaudio.get_device_count()):
            info = self.pyaudio.get_device_info_by_index(i)
            logger.info(
                f"  {i}: {info['name']} "
                f"(in: {info['maxInputChannels']}, out: {info['maxOutputChannels']})"
            )

    def start_listening(self) -> None:
        """Start listening to microphone input."""
        if self.is_listening:
            logger.warning("Already listening")
            return

        try:
            self.input_stream = self.pyaudio.open(
                format=pyaudio.paFloat32,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
            )
            self.is_listening = True
            logger.info(
                f"Started listening: {self.sample_rate}Hz, {self.channels} channel(s)"
            )

            # Start listening thread
            listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
            listen_thread.start()

        except Exception as e:
            logger.error(f"Failed to start listening: {e}")
            raise

    def stop_listening(self) -> None:
        """Stop listening to microphone."""
        if not self.is_listening:
            return

        self.is_listening = False

        if self.input_stream:
            self.input_stream.stop_stream()
            self.input_stream.close()
            self.input_stream = None

        logger.info("Stopped listening")

    def _listen_loop(self) -> None:
        """Background thread loop for reading audio."""
        while self.is_listening:
            try:
                data = self.input_stream.read(self.chunk_size, exception_on_overflow=False)
                audio_data = np.frombuffer(data, dtype=np.float32)
                self.audio_queue.put(audio_data)
            except Exception as e:
                logger.error(f"Error reading from microphone: {e}")
                break

    async def get_audio_chunk(self, timeout: float = 1.0) -> Optional[np.ndarray]:
        """Get next audio chunk with timeout."""
        try:
            audio_data = self.audio_queue.get(timeout=timeout)
            return audio_data
        except queue.Empty:
            return None

    async def record_audio(
        self, duration: float, on_chunk: Optional[Callable] = None
    ) -> bytes:
        """
        Record audio for specified duration.

        Args:
            duration: Recording duration in seconds
            on_chunk: Optional callback for each chunk

        Returns:
            Audio data as bytes
        """
        logger.info(f"Recording for {duration} seconds...")
        frames = []

        try:
            stream = self.pyaudio.open(
                format=pyaudio.paFloat32,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
            )

            chunks_needed = int(
                (self.sample_rate / self.chunk_size) * duration
            )

            for _ in range(chunks_needed):
                data = stream.read(self.chunk_size, exception_on_overflow=False)
                frames.append(data)

                if on_chunk:
                    audio_array = np.frombuffer(data, dtype=np.float32)
                    on_chunk(audio_array)

            stream.stop_stream()
            stream.close()

            # Convert to bytes
            audio_bytes = b"".join(frames)
            logger.info(f"Recording complete: {len(audio_bytes)} bytes")

            return audio_bytes

        except Exception as e:
            logger.error(f"Error recording audio: {e}")
            raise

    async def play_audio(self, audio_data: bytes, blocking: bool = True) -> None:
        """
        Play audio through speaker.

        Args:
            audio_data: Audio data as bytes
            blocking: Wait for playback to complete
        """
        try:
            logger.info(f"Playing audio: {len(audio_data)} bytes")

            stream = self.pyaudio.open(
                format=pyaudio.paFloat32,
                channels=self.channels,
                rate=self.sample_rate,
                output=True,
                frames_per_buffer=self.chunk_size,
            )

            # Play in chunks
            for i in range(0, len(audio_data), self.chunk_size * 4):
                chunk = audio_data[i : i + self.chunk_size * 4]
                stream.write(chunk)

            if blocking:
                stream.stop_stream()

            stream.close()
            logger.info("Playback complete")

        except Exception as e:
            logger.error(f"Error playing audio: {e}")
            raise

    def play_text_as_audio(self, text: str) -> None:
        """
        Simple text-to-speech for demo (uses system TTS).
        For production, use ElevenLabs API.
        """
        import subprocess
        import sys

        if sys.platform == "darwin":  # macOS
            # Use macOS built-in say command
            logger.info(f"Speaking: {text}")
            subprocess.run(
                ["say", "-r", "150", text],
                check=False,
                capture_output=True,
            )
        else:
            logger.warning("Text-to-speech only supported on macOS in demo mode")

    def save_audio(self, audio_data: bytes, filepath: Path) -> None:
        """Save audio data to file."""
        try:
            import wave

            with wave.open(str(filepath), "wb") as wav_file:
                wav_file.setnchannels(self.channels)
                wav_file.setsampwidth(self.pyaudio.get_sample_size(pyaudio.paFloat32))
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(audio_data)

            logger.info(f"Audio saved to {filepath}")

        except Exception as e:
            logger.error(f"Error saving audio: {e}")

    def __del__(self):
        """Cleanup on deletion."""
        self.stop_listening()
        if self.pyaudio:
            self.pyaudio.terminate()


# Global audio IO instance
audio_io = MacAudioIO()
