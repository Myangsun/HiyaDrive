"""
Main CLI application for HiyaDrive demo.
Entry point for running the voice booking agent.
"""

import asyncio
import click
from datetime import datetime
from typing import Optional

from hiya_drive.core.orchestrator import orchestrator
from hiya_drive.voice.voice_processor import voice_processor
from hiya_drive.voice.audio_io import audio_io
from hiya_drive.voice.wake_word_detector import wake_word_detector
from hiya_drive.config.settings import settings
from hiya_drive.utils.logger import logger


@click.group()
def cli():
    """HiyaDrive - Voice Booking Agent for Drivers."""
    pass


@cli.command()
@click.option(
    "--utterance",
    default=None,
    help="User utterance (e.g., 'Book a table for 2 at Italian next Friday at 7 PM')",
)
@click.option(
    "--driver-id",
    default="demo_driver_001",
    help="Driver ID for the session",
)
@click.option(
    "--interactive",
    is_flag=True,
    default=False,
    help="Interactive mode: listen to microphone input",
)
def demo(utterance: Optional[str], driver_id: str, interactive: bool):
    """
    Run a booking demo.

    Examples:
        # Text input
        hiya-drive demo --utterance "Book a table for 2 at Italian next Friday at 7 PM"

        # Interactive (voice input from Mac microphone)
        hiya-drive demo --interactive
    """
    asyncio.run(_run_demo(utterance, driver_id, interactive))


async def _run_demo(utterance: Optional[str], driver_id: str, interactive: bool):
    """Run the demo asynchronously."""

    click.secho("\n" + "=" * 70, fg="cyan", bold=True)
    click.secho("   HiyaDrive - Voice Booking Agent for Drivers",
                fg="cyan", bold=True)
    click.secho("=" * 70 + "\n", fg="cyan", bold=True)

    click.echo(f"Demo Mode: {settings.demo_mode}")
    click.echo(f"App Env: {settings.app_env}")
    click.echo(f"Log Level: {settings.log_level}")
    click.echo()

    # Get user input
    if interactive:
        click.echo("🎤 Interactive Mode - Listening to microphone...")
        click.echo(f"   Recording for {settings.voice_timeout} seconds...")
        click.echo(
            "   Say: 'Book a table for X at [cuisine] on [date] at [time]'")
        click.echo()

        utterance = await voice_processor.listen_and_transcribe(
            duration=settings.voice_timeout
        )

        if not utterance:
            click.secho("❌ No speech detected. Try again.", fg="red")
            return

        click.secho(f"✓ Transcribed: {utterance}", fg="green")
        click.echo()

    elif not utterance:
        # Prompt user for input
        utterance = click.prompt(
            "📝 Enter booking request",
            default="Book a table for 2 at Italian next Friday at 7 PM",
        )

    click.echo(f"Driver ID: {driver_id}")
    click.echo(f"User: {utterance}")
    click.echo()

    # Run the booking workflow
    click.secho("▶ Starting booking workflow...\n", fg="yellow")

    try:
        final_state = await orchestrator.run_booking_session(
            driver_id=driver_id,
            initial_utterance=utterance,
        )

        # Display results
        click.secho("\n" + "-" * 70, fg="cyan")
        click.secho("📊 BOOKING SESSION RESULTS", fg="cyan", bold=True)
        click.secho("-" * 70, fg="cyan")

        click.echo()
        click.echo(f"Session ID:          {final_state.session_id}")
        click.echo(f"Status:              {final_state.status.value.upper()}")
        click.echo(
            f"Duration:            ~{(datetime.now() - final_state.start_time).total_seconds():.1f}s"
        )
        click.echo()

        if final_state.booking_confirmed:
            click.secho("✅ BOOKING CONFIRMED", fg="green", bold=True)
            click.echo()
            click.echo(
                f"  Restaurant:        {final_state.selected_restaurant.name}")
            click.echo(
                f"  Phone:             {final_state.selected_restaurant.phone}")
            click.echo(f"  Party Size:        {final_state.party_size}")
            click.echo(f"  Date:              {final_state.requested_date}")
            click.echo(f"  Time:              {final_state.requested_time}")
            click.echo(
                f"  Confirmation #:    {final_state.confirmation_number}")
            click.echo()

            # Speak confirmation
            confirmation_text = (
                f"Your reservation at {final_state.selected_restaurant.name} "
                f"for {final_state.party_size} on {final_state.requested_date} "
                f"at {final_state.requested_time} is confirmed. "
                f"Confirmation number: {final_state.confirmation_number}"
            )
            await voice_processor.speak(confirmation_text)

        else:
            click.secho("❌ BOOKING FAILED", fg="red", bold=True)
            click.echo()
            if final_state.errors:
                click.echo("Errors:")
                for error in final_state.errors:
                    click.echo(f"  - {error}")

        click.echo()
        click.secho("-" * 70, fg="cyan")

        # Show full state for debugging (only in interactive mode)
        try:
            if click.confirm("\n📋 Show full state details?"):
                click.echo()
                state_dict = final_state.to_dict()
                import json

                click.echo(json.dumps(state_dict, indent=2))
        except click.exceptions.Abort:
            # Non-interactive mode or user cancelled
            pass

    except Exception as e:
        click.secho(f"❌ Error: {e}", fg="red")
        logger.exception("Demo error")


@cli.command()
@click.option(
    "--driver-id",
    default="voice_driver_001",
    help="Driver ID for the session",
)
def voice(driver_id: str):
    """
    Run HiyaDrive in voice-first mode.
    Listens for 'hiya' wake word and greets the user.

    Examples:
        hiya-drive voice
        hiya-drive voice --driver-id my_driver_123
    """
    asyncio.run(_run_voice_mode(driver_id))


async def _run_voice_mode(driver_id: str):
    """Run HiyaDrive in voice-first mode with wake word detection."""

    click.secho("\n" + "=" * 70, fg="cyan", bold=True)
    click.secho("   HiyaDrive - Voice Mode (Wake Word Enabled)",
                fg="cyan", bold=True)
    click.secho("=" * 70 + "\n", fg="cyan", bold=True)

    click.echo(f"Driver ID: {driver_id}")
    click.echo(f"Wake Word: '{settings.wake_word}'")
    click.echo()

    try:
        # Listen for wake word
        click.secho("🎤 Listening for wake word...", fg="yellow")
        click.echo("   Say 'hiya driver' to activate HiyaDrive")
        click.echo()

        detected = await wake_word_detector.listen_for_wake_word_and_greet(timeout=120)

        if not detected:
            click.secho("❌ Wake word not detected (timeout).", fg="red")
            return

        click.echo()

        # Ask about task
        click.secho("📋 What would you like me to do?", fg="yellow")
        click.echo("   Examples:")
        click.echo("   - Book a table for 2 at Italian next Friday at 7 PM")
        click.echo("   - Make a reservation for 4 people at a sushi place")
        click.echo()

        # Listen for user task
        click.secho("🎤 Listening for your request...", fg="yellow")
        utterance = await voice_processor.listen_and_transcribe(
            duration=settings.voice_timeout
        )

        if not utterance:
            click.secho("❌ No speech detected. Please try again.", fg="red")
            await voice_processor.speak("Sorry, I didn't hear that. Please try again.")
            return

        click.secho(f"✓ You said: {utterance}", fg="green")
        click.echo()

        # Run the booking workflow
        click.secho("▶ Processing your request...\n", fg="yellow")

        final_state = await orchestrator.run_booking_session(
            driver_id=driver_id,
            initial_utterance=utterance,
        )

        # Display results
        click.secho("\n" + "-" * 70, fg="cyan")
        click.secho("📊 BOOKING SESSION RESULTS", fg="cyan", bold=True)
        click.secho("-" * 70, fg="cyan")

        click.echo()
        click.echo(f"Session ID:          {final_state.session_id}")
        click.echo(f"Status:              {final_state.status.value.upper()}")
        click.echo(
            f"Duration:            ~{(datetime.now() - final_state.start_time).total_seconds():.1f}s"
        )
        click.echo()

        if final_state.booking_confirmed:
            click.secho("✅ BOOKING CONFIRMED", fg="green", bold=True)
            click.echo()
            click.echo(
                f"  Restaurant:        {final_state.selected_restaurant.name}")
            click.echo(
                f"  Phone:             {final_state.selected_restaurant.phone}")
            click.echo(f"  Party Size:        {final_state.party_size}")
            click.echo(f"  Date:              {final_state.requested_date}")
            click.echo(f"  Time:              {final_state.requested_time}")
            click.echo(
                f"  Confirmation #:    {final_state.confirmation_number}")
            click.echo()

            # Speak confirmation
            confirmation_text = (
                f"Your reservation at {final_state.selected_restaurant.name} "
                f"for {final_state.party_size} on {final_state.requested_date} "
                f"at {final_state.requested_time} is confirmed. "
                f"Confirmation number: {final_state.confirmation_number}"
            )
            await voice_processor.speak(confirmation_text)

        else:
            click.secho("❌ BOOKING FAILED", fg="red", bold=True)
            click.echo()
            if final_state.errors:
                click.echo("Errors:")
                for error in final_state.errors:
                    click.echo(f"  - {error}")

        click.echo()
        click.secho("-" * 70, fg="cyan")

    except Exception as e:
        click.secho(f"❌ Error: {e}", fg="red")
        logger.exception("Voice mode error")


@cli.command()
def test_audio():
    """Test audio input/output."""
    click.secho("\n🔊 Audio I/O Test", fg="cyan", bold=True)
    click.echo()

    # List devices
    audio_io.list_devices()

    click.echo()
    click.secho("Testing microphone...", fg="yellow")
    click.echo(f"Recording for 3 seconds...")

    asyncio.run(_test_microphone())

    click.echo()
    click.secho("Testing speaker...", fg="yellow")
    audio_io.play_text_as_audio(
        "Hello! This is HiyaDrive. Testing audio output.")

    click.secho("\n✅ Audio test complete", fg="green")


async def _test_microphone():
    """Test microphone recording."""
    try:
        audio_data = await audio_io.record_audio(duration=3.0)
        click.secho(f"✓ Recorded {len(audio_data)} bytes", fg="green")

        # Save recording
        from pathlib import Path

        recording_file = settings.recordings_dir / "test_recording.wav"
        audio_io.save_audio(audio_data, recording_file)

        click.secho(f"✓ Saved to {recording_file}", fg="green")

    except Exception as e:
        click.secho(f"❌ Microphone test failed: {e}", fg="red")


@cli.command()
def test_tts():
    """Test Text-to-Speech."""
    click.secho("\n🗣️ Text-to-Speech Test", fg="cyan", bold=True)
    click.echo()

    test_texts = [
        "Hello, this is HiyaDrive.",
        "Testing the text to speech system.",
        "Your reservation is confirmed.",
    ]

    for text in test_texts:
        click.echo(f"Speaking: '{text}'")
        asyncio.run(voice_processor.speak(text))
        click.echo()

    click.secho("✅ TTS test complete", fg="green")


@cli.command()
def test_stt():
    """Test Speech-to-Text."""
    click.secho("\n🎤 Speech-to-Text Test", fg="cyan", bold=True)
    click.echo()

    click.echo("Recording for 3 seconds...")
    click.echo("Say something! (e.g., 'Book a table for two')")
    click.echo()

    asyncio.run(_test_stt())


async def _test_stt():
    """Test STT functionality."""
    try:
        transcript = await voice_processor.listen_and_transcribe(duration=3.0)
        click.secho(f"✓ Transcribed: {transcript}", fg="green")

    except Exception as e:
        click.secho(f"❌ STT test failed: {e}", fg="red")


@cli.command()
def status():
    """Show system status and configuration."""
    click.secho("\n📊 HiyaDrive System Status", fg="cyan", bold=True)
    click.echo()

    click.secho("Configuration:", fg="yellow", bold=True)
    click.echo(f"  Environment:       {settings.app_env}")
    click.echo(f"  Debug:             {settings.debug}")
    click.echo(f"  Log Level:         {settings.log_level}")
    click.echo()

    click.secho("API Configuration:", fg="yellow", bold=True)
    click.echo(f"  LLM Model:         {settings.llm_model}")
    click.echo(
        f"  STT Provider:      {'Mock' if settings.use_mock_stt else 'Deepgram'}"
    )
    click.echo(
        f"  TTS Provider:      {'Mock' if settings.use_mock_tts else 'ElevenLabs'}"
    )
    click.echo()

    click.secho("Voice Settings:", fg="yellow", bold=True)
    click.echo(f"  Sample Rate:       {settings.sample_rate} Hz")
    click.echo(f"  Channels:          {settings.channels}")
    click.echo(f"  Voice Timeout:     {settings.voice_timeout}s")
    click.echo()

    click.secho("Feature Flags:", fg="yellow", bold=True)
    click.echo(f"  Demo Mode:         {settings.demo_mode}")
    click.echo(f"  Use Mock STT:      {settings.use_mock_stt}")
    click.echo(f"  Use Mock TTS:      {settings.use_mock_tts}")
    click.echo(f"  Use Mock Calendar: {settings.use_mock_calendar}")
    click.echo(f"  Use Mock Places:   {settings.use_mock_places}")
    click.echo(f"  Use Mock Twilio:   {settings.use_mock_twilio}")
    click.echo()

    click.secho("Directories:", fg="yellow", bold=True)
    click.echo(f"  Project Root:      {settings.project_root}")
    click.echo(f"  Logs:              {settings.logs_dir}")
    click.echo(f"  Recordings:        {settings.recordings_dir}")
    click.echo()


if __name__ == "__main__":
    cli()
