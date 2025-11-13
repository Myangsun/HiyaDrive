# HiyaDrive Quick Start Guide

Get up and running with HiyaDrive in 5 minutes.

## Prerequisites

- macOS (with microphone and speaker)
- Python 3.9 or higher
- `pip` package manager

## Step 1: Clone/Setup

```bash
cd /Users/mingyang/Desktop/AI\ Ideas/HiyaDrive
```

## Step 2: Automated Setup (Recommended)

```bash
bash setup_dev.sh
```

This script will:
- Check Python version
- Create virtual environment
- Install all dependencies
- Create necessary directories
- Set up .env configuration

## Step 3: Activate Environment

```bash
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt.

## Step 4: Run Your First Demo

### Option A: Text Input (Simplest)

```bash
python -m hiya_drive.main demo --utterance "Book a table for 2 at Italian next Friday at 7 PM"
```

Expected output:
```
======================================================================
   HiyaDrive - Voice Booking Agent for Drivers
======================================================================

▶ Starting booking workflow...

----------------------------------------------------------------------
📊 BOOKING SESSION RESULTS
----------------------------------------------------------------------

Session ID:          xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
Status:              COMPLETED

✅ BOOKING CONFIRMED

  Restaurant:        Olive Garden
  Phone:             +1-555-0100
  Party Size:        2
  Date:              next Friday
  Time:              7 PM
  Confirmation #:    4892

Your reservation at Olive Garden for 2 on next Friday at 7 PM is confirmed.
Confirmation number: 4892
```

### Option B: Interactive Mode (Voice Input)

```bash
python -m hiya_drive.main demo --interactive
```

The system will:
1. Listen to your microphone for 30 seconds
2. Transcribe your speech
3. Process the booking
4. Speak back the confirmation

Say something like:
> "Book a table for 2 at Italian next Friday at 7 PM"

## Step 5: Test Components

### Test Audio (Microphone & Speaker)

```bash
python -m hiya_drive.main test-audio
```

This will:
- List available audio devices
- Record 3 seconds from microphone
- Save recording to `data/recordings/test_recording.wav`

### Test Text-to-Speech

```bash
python -m hiya_drive.main test-tts
```

The system will speak several test sentences aloud.

### Test Speech-to-Text

```bash
python -m hiya_drive.main test-stt
```

The system will record for 3 seconds and transcribe what you say.

## Step 6: View System Status

```bash
python -m hiya_drive.main status
```

Shows configuration, API providers, feature flags, etc.

## Step 7: Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/unit/test_state.py -v

# Run with coverage
pytest tests/ --cov=hiya_drive --cov-report=html
```

## Step 8: View Logs

```bash
# Real-time log watching
tail -f data/logs/hiya_drive_development.log

# View errors only
tail -f data/logs/hiya_drive_errors_development.log
```

## Using Make Commands

If you prefer make:

```bash
# List all commands
make help

# Run demo
make demo

# Run interactive demo
make demo-interactive

# Run tests
make test

# Format code
make format

# Check code quality
make lint
```

## Configuration

Edit `.env` to configure:

```env
# API Settings
ANTHROPIC_API_KEY=your_key_here
DEEPGRAM_API_KEY=your_key_here
ELEVENLABS_API_KEY=your_key_here

# Behavior
DEBUG=True
LOG_LEVEL=DEBUG
DEMO_MODE=True

# Use mocks or real APIs
USE_MOCK_STT=True      # Mock speech-to-text
USE_MOCK_TTS=True      # Mock text-to-speech
USE_MOCK_CALENDAR=True # Mock calendar checks
USE_MOCK_PLACES=True   # Mock restaurant search
USE_MOCK_TWILIO=True   # Mock phone calls
```

## Common Issues

### "ModuleNotFoundError: No module named 'hiya_drive'"

Make sure your virtual environment is activated:
```bash
source venv/bin/activate
```

### Microphone not working

Check available devices:
```bash
python -m hiya_drive.main test-audio
```

Then in macOS System Preferences:
- Security & Privacy → Microphone → Allow Terminal

### Tests failing

Ensure you have pytest-asyncio installed:
```bash
pip install -r requirements.txt
```

### No audio output

Check speaker settings and volume. To test:
```bash
python -m hiya_drive.main test-tts
```

## Next Steps

1. **Explore the code**: Read through `hiya_drive/core/orchestrator.py` to understand the workflow
2. **Run tests**: `pytest tests/unit/ -v` to see how components work
3. **Integrate real APIs**: Replace mock implementations with actual API calls
4. **Build on it**: Extend the agent with more features

## Project Structure

```
hiya_drive/
├── core/              # Orchestration engine
├── models/            # State and data models
├── voice/             # Audio I/O and processing
├── config/            # Configuration management
├── utils/             # Logging and utilities
└── main.py           # CLI entry point
```

## Architecture Diagram

```
┌─────────────────────┐
│   User Input        │
│  (Voice/Text)       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  Intent Parsing (Claude LLM)        │
│  Extract: party size, date, time    │
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  Restaurant Search (Google Places)  │
│  Find matching restaurants          │
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  Phone Call (Twilio)                │
│  Negotiate reservation with staff   │
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  Confirmation                       │
│  Save booking + calendar event      │
└─────────────────────────────────────┘
           │
           ▼
┌─────────────────────┐
│   TTS Confirmation  │
│   Speak details     │
└─────────────────────┘
```

## Performance Expectations

- **Demo Mode**: ~2-5 seconds for complete booking (all mocked)
- **With Real APIs**: ~15-30 seconds (depends on network)
- **STT Latency**: 300-500ms (Deepgram)
- **TTS Latency**: 300-500ms per sentence (ElevenLabs)
- **LLM Response**: 200-400ms (Claude Sonnet 4.5)

## More Commands

See all available commands:
```bash
make help
python -m hiya_drive.main --help
```

## Support

For detailed documentation:
- **README.md** - Full project documentation
- **MVP_IMPLEMENTATION_PLAN.md** - Technical architecture
- **High-Level Architecture.md** - System design
- **Data Flow.md** - Sequence diagrams

---

**Ready?** Run your first demo:

```bash
python -m hiya_drive.main demo --utterance "Book a table for 2 at Italian next Friday at 7 PM"
```

Enjoy! 🚗🎙️
