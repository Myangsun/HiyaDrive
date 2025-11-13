# HiyaDrive - Voice Booking Agent for Drivers

An AI-powered voice assistant that enables drivers to book restaurant reservations completely hands-free. Built with Claude, LangGraph, and optimized for in-vehicle use.

## 📋 Project Structure

```
HiyaDrive/
├── hiya_drive/                          # Main package
│   ├── __init__.py
│   ├── main.py                          # CLI entry point
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py                  # Configuration management
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   └── orchestrator.py              # LangGraph workflow engine
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   └── state.py                     # State definitions & data models
│   │
│   ├── voice/
│   │   ├── __init__.py
│   │   ├── audio_io.py                  # Mac microphone/speaker I/O
│   │   └── voice_processor.py           # STT/TTS abstraction layer
│   │
│   ├── integrations/
│   │   ├── __init__.py
│   │   ├── calendar_api.py              # Google Calendar integration
│   │   ├── places_api.py                # Google Places integration
│   │   └── twilio_api.py                # Twilio Voice integration
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   └── booking_agent.py             # Booking-specific agent logic
│   │
│   └── utils/
│       ├── __init__.py
│       └── logger.py                    # Logging configuration
│
├── tests/
│   ├── __init__.py
│   ├── unit/                            # Unit tests
│   │   ├── __init__.py
│   │   ├── test_state.py
│   │   ├── test_voice_processor.py
│   │   └── test_orchestrator.py
│   │
│   └── integration/                     # Integration tests
│       ├── __init__.py
│       └── test_e2e_booking.py
│
├── config/                              # Configuration files
├── scripts/                             # Utility scripts
├── data/
│   ├── logs/                            # Application logs
│   └── recordings/                      # Audio recordings
│
├── docs/                                # Documentation
├── .env                                 # Environment variables (local)
├── .env.example                         # Environment template
├── requirements.txt                     # Python dependencies
├── setup.py                             # Package setup
├── Makefile                             # Development commands
├── MVP_IMPLEMENTATION_PLAN.md           # Detailed implementation plan
└── README.md                            # This file
```

## 🚀 Quick Start

### 1. Prerequisites

- **macOS** (audio I/O optimized for Mac)
- **Python 3.9+**
- **API Keys** (for production):
  - Anthropic (Claude API)
  - Deepgram (STT)
  - ElevenLabs (TTS)
  - Google Calendar & Places
  - Twilio

### 2. Setup

```bash
# Clone repository
cd /Users/mingyang/Desktop/AI\ Ideas/HiyaDrive

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Or use make
make dev-install
```

### 3. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials (optional for demo mode)
# For demo, all APIs use mocked implementations
```

### 4. Run Demo

```bash
# Text-based demo
make demo

# Or with custom utterance
python -m hiya_drive.main demo --utterance "Book a table for 4 at sushi next Friday at 8 PM"

# Interactive mode (Mac microphone)
make demo-interactive
```

## 📚 Usage

### CLI Commands

```bash
# Main booking demo
hiya-drive demo [OPTIONS]
  --utterance TEXT        # Provide text input instead of microphone
  --driver-id TEXT        # Driver identifier
  --interactive           # Use microphone input

# Test audio (Mac only)
hiya-drive test-audio     # Test microphone & speaker

# Test Text-to-Speech
hiya-drive test-tts       # Hear the TTS voice

# Test Speech-to-Text
hiya-drive test-stt       # Record and transcribe

# System status
hiya-drive status         # Show configuration
```

## 🏗️ Architecture

### State Machine (LangGraph)

The booking workflow is implemented as a LangGraph state machine with 9 nodes:

1. **parse_intent** - Extract booking parameters from user speech
2. **check_calendar** - Verify driver availability
3. **search_restaurants** - Find matching restaurants
4. **select_restaurant** - Choose restaurant from candidates
5. **prepare_call** - Generate opening script
6. **make_call** - Initiate call to restaurant
7. **converse** - Multi-turn STT/LLM/TTS conversation
8. **confirm_booking** - Save booking & calendar event
9. **handle_error** - Error recovery with retry logic

### Key Components

#### Voice Processing Pipeline
```
Microphone → Deepgram STT → Claude LLM → ElevenLabs TTS → Speaker
```

#### Technology Choices

| Component | Technology | Why |
|-----------|-----------|-----|
| LLM | Claude Sonnet 4.5 | 200-400ms latency, reliable tool-calling |
| STT | Deepgram Nova-2 | 300-500ms streaming, telephony optimized |
| TTS | ElevenLabs Turbo | Human-like prosody, word-by-word streaming |
| Orchestration | LangGraph | State machine with error handling |
| Telephony | Twilio Voice | WebSocket streaming, reliable calls |
| APIs | Google Calendar/Places | Calendar availability, restaurant search |

## 🧪 Testing

```bash
# Run all tests
make test

# Unit tests only
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# With coverage
pytest tests/ --cov=hiya_drive --cov-report=html
```

## 📝 Development

### Code Quality

```bash
# Format code with Black
make format

# Run linting (pylint)
make lint

# Type checking (mypy)
make type-check
```

### Logging

Logs are written to:
- **Console**: Real-time output during development
- **File**: `data/logs/hiya_drive_{env}.log`
- **Errors**: `data/logs/hiya_drive_errors_{env}.log`

View logs:
```bash
tail -f data/logs/hiya_drive_development.log
```

### Feature Flags

Control behavior via `.env`:

```env
USE_MOCK_STT=True          # Use mock STT instead of Deepgram
USE_MOCK_TTS=True          # Use system TTS instead of ElevenLabs
USE_MOCK_CALENDAR=True     # Mock calendar availability
USE_MOCK_PLACES=True       # Mock restaurant search
USE_MOCK_TWILIO=True       # Mock phone calls
DEMO_MODE=True             # Enable all mocks for demo
```

## 🎯 Implementation Phases

### ✅ Phase 1: Core Structure (Complete)
- [x] Project structure and configuration
- [x] State management (LangGraph)
- [x] Voice I/O integration (Mac)
- [x] Mock implementations for demo
- [x] CLI application

### 🔄 Phase 2: API Integration (In Progress)
- [ ] Anthropic Claude integration (partial - no API keys in demo)
- [ ] Google Calendar API integration
- [ ] Google Places API integration
- [ ] Twilio Voice integration
- [ ] Error handling & resilience

### 📋 Phase 3: Testing & Validation
- [ ] Unit tests for all nodes
- [ ] Integration tests (API mocking)
- [ ] Simulator studies (safety validation)
- [ ] Beta testing with real users

### 🚀 Phase 4: Production
- [ ] Performance optimization
- [ ] Multi-language support
- [ ] Vehicle context integration
- [ ] Analytics dashboard

## 🔍 How It Works

### Example Booking Flow

**User**: "Book a table for 2 at Italian next Friday at 7 PM"

1. **Audio Input**: Microphone captures speech
2. **STT**: Deepgram transcribes to text
3. **Intent Parsing**: Claude extracts parameters
   - party_size: 2
   - cuisine: Italian
   - date: next Friday
   - time: 7 PM
4. **Calendar Check**: Verify driver is available
5. **Restaurant Search**: Google Places finds Italian restaurants
6. **Call Preparation**: Claude generates opening script
7. **Outbound Call**: Twilio calls restaurant
8. **Negotiation**: Multi-turn conversation via STT/LLM/TTS
9. **Confirmation**: Extract confirmation number
10. **Booking Save**: Store in database + calendar event
11. **TTS Confirmation**: Speak booking details back to driver

### Demo Mode

In demo mode, all external APIs are mocked:
- ✓ Microphone works (real audio input)
- ✓ Speaker works (real audio output)
- ✗ APIs are stubbed (return mock data)
- ✓ Workflow runs end-to-end
- ✓ Perfect for testing without API keys

## 🐛 Troubleshooting

### Microphone not working
```bash
# List available audio devices
python -m hiya_drive.main test-audio

# Check device permissions (macOS)
System Preferences → Security & Privacy → Microphone
```

### Import errors
```bash
# Reinstall in development mode
pip install -e .
```

### Logs not appearing
```bash
# Check log level in .env
LOG_LEVEL=DEBUG

# View current logs
tail -f data/logs/hiya_drive_development.log
```

## 📖 Documentation

- **MVP_IMPLEMENTATION_PLAN.md**: Detailed technical specification
- **High-Level Architecture.md**: System design overview
- **Data Flow.md**: Sequence diagrams
- **Agents.md**: Workflow node descriptions

## 🤝 Contributing

This is a prototype/demo project. For contributions:

1. Create a feature branch
2. Follow PEP 8 style guide (use `black`)
3. Write tests for new functionality
4. Update documentation
5. Submit pull request

## 📄 License

This project is provided as-is for demonstration purposes.

## 🙋 Support

For issues or questions:
1. Check logs: `data/logs/hiya_drive_development.log`
2. Run diagnostics: `hiya-drive status`
3. Test components individually: `hiya-drive test-audio`, `hiya-drive test-stt`, etc.

---

**Built with**: Claude 4.5 | LangGraph | Deepgram | ElevenLabs | Twilio

**Status**: MVP Proof of Concept (v0.1.0)
