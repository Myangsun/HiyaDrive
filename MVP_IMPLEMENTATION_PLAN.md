# HiyaDrive - MVP Implementation Plan
## Voice Booking Agent for Drivers – Proof of Concept

**Document Version**: 1.0
**Date**: November 2024
**Status**: Ready for Development

---

## Executive Summary

This document outlines a detailed implementation plan for the MVP (Minimum Viable Product) proof of concept of HiyaDrive, an AI-powered voice booking agent designed for drivers. The MVP demonstrates hands-free restaurant reservation capability with a focus on safety, low latency, and robust voice handling.

**MVP Scope**: End-to-end voice booking flow for restaurant reservations without requiring manual driver interaction.

**Timeline Estimate**: 6-8 weeks (Phase 1: Core Integration, Phase 2: Voice Loop, Phase 3: Testing & Refinement)

---

## 1. Foundational Models & Voice Technology Stack

### 1.1 Large Language Model (LLM)

**Choice**: Claude Sonnet 4.5

**Why It's Best Suited**:
- **Low Latency** (200-400ms): Critical for real-time voice interactions where delays >1s cause drivers to look at screens
- **Reliable Function Calling**: Consistent tool-calling with proper error handling ensures integration with calendar, places, and phone APIs
- **Long Context Window** (200K tokens): Enables rich conversation history without losing state, essential for multi-turn negotiations with restaurants
- **Instruction Following**: Responds well to concise system prompts constraining output to <15 seconds
- **Tested in Production Voice Systems**: Superior to GPT-4 Turbo for voice latency-sensitive applications

**Alternatives Considered**:
- GPT-4 Turbo: Higher latency (>800ms), less reliable function calling
- Llama 2: Lower quality responses, requires self-hosting with higher operational overhead
- Local Models: Insufficient capability for natural multi-turn conversation

**Integration Method**:
- Anthropic SDK with streaming for word-by-word TTS integration
- System prompts optimized for concise, safety-aware outputs

---

### 1.2 Speech-to-Text (STT)

**Choice**: Deepgram Nova-2

**Why It's Best Suited**:
- **Ultra-Low Latency** (300-500ms): Streaming architecture enables real-time transcription without waiting for user to finish speaking
- **Telephony Optimized**: Trained on phone and in-car audio with robustness to road noise, background conversations, and low-quality microphones
- **Custom Vocabulary Support**: Can inject restaurant names, locations, and cuisine types to reduce transcription errors on domain-specific terms
- **Streaming API**: Word-by-word confidence scores enable early interrupt detection if user changes their mind mid-utterance
- **Cost Efficient**: 2.5x cheaper than Whisper API while maintaining superior accuracy on telephony

**Alternatives Considered**:
- Whisper API: ~2s latency (unacceptable for voice), requires buffering entire utterance
- Google Speech-to-Text: Slower streaming, higher cost, less telephony optimization
- Azure Speech Services: Higher latency, more complex authentication

**Integration Points**:
- WebSocket streaming from vehicle microphone
- Custom vocabulary list (restaurant names, cuisine types, location names)
- Audio preprocessing: 16kHz mono PCM, noise gate at -40dB

**Fallback Strategy**:
- If Deepgram unavailable: Fall back to Google Speech-to-Text with 2s timeout
- If both fail: Offer text input via text-to-speech prompt asking user to repeat

---

### 1.3 Text-to-Speech (TTS)

**Choice**: ElevenLabs Turbo v2.5

**Why It's Best Suited**:
- **Word-by-Word Streaming** (300-500ms per word): Allows agent to start speaking while still generating response, reducing perceived latency
- **Natural Prosody**: Produced speech sounds conversational, not robotic—crucial for multi-minute phone negotiations with restaurants
- **Multiple Voice Options**: Can vary tone (professional, friendly, warm) based on context; driver preference
- **Emotional Range**: Supports politeness and warmth while maintaining safety-optimized conciseness
- **In-Car Audio Quality**: Voices are clear and intelligible over road noise without need for extreme volume

**Alternatives Considered**:
- Google Cloud TTS: Adequate quality but slower (600ms+ per utterance)
- AWS Polly: Lower prosody quality, less streaming flexibility
- Deepgram TTS: Limited emotional range, less natural for extended conversation
- Local TTS (Tacotron2): Requires GPU, offline models sound robotic, slower inference

**Integration Points**:
- Streaming mode: Begin playback while generating TTS
- Voice consistency: Use same voice ID throughout session for driver familiarity
- Interrupt-safe: If user speaks while TTS playing, stop immediately and switch to STT

**Configuration**:
- Voice: "Sarah" (professional, warm, ~140 WPM for in-car comprehension)
- Stability: 0.5 (balanced between consistency and emotional variation)
- Similarity Boost: 0.75 (closer to reference voice)

---

### 1.4 Voice Technology Integration Flow

```
┌─────────────────────────────────────────────────────────────┐
│                   Driver Speech Input                        │
│              (from vehicle microphone)                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
         ┌──────────────────────────┐
         │  Deepgram Nova-2 (STT)   │
         │   WebSocket Streaming    │
         │   Custom Vocabulary      │
         │   300-500ms latency      │
         └────────────┬─────────────┘
                      │
                      ▼
         ┌──────────────────────────┐
         │  Intent Recognition      │
         │  (Claude Function Call)  │
         │  Extract: date, time,    │
         │  location, party size    │
         └────────────┬─────────────┘
                      │
                      ▼
         ┌──────────────────────────┐
         │ Claude Sonnet 4.5 (LLM)  │
         │ • Function Calling       │
         │ • State Management       │
         │ • Response Generation    │
         │ <1s response time        │
         └────────────┬─────────────┘
                      │
                      ▼
         ┌──────────────────────────┐
         │ ElevenLabs Turbo (TTS)   │
         │ Word-by-Word Streaming   │
         │ Professional Voice       │
         │ 300-500ms per word       │
         └────────────┬─────────────┘
                      │
                      ▼
         ┌──────────────────────────┐
         │   Vehicle Audio Output   │
         │    (through speakers)    │
         └──────────────────────────┘
```

---

## 2. Integration Points & Architecture

### 2.1 External APIs & Services

#### 2.1.1 Google Calendar API

**Purpose**: Verify driver availability and avoid scheduling conflicts

**Implementation**:
```python
# OAuth 2.0 flow - user grants read/write access
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# Tool function for LLM
def check_calendar_availability(
    date: str,  # ISO format: "2024-11-15"
    time: str,  # "19:00"
    duration_minutes: int = 90
) -> Dict[str, bool]:
    """
    Returns: {
        "available": bool,
        "next_available_slot": str,
        "conflicts": List[str]
    }
    """
    pass
```

**Configuration**:
- **Scopes**: `calendar.readonly` (minimum privilege)
- **Caching**: Cache user's calendar for 5 minutes to reduce API calls
- **Rate Limiting**: Max 10 calls per booking session

**Error Handling**:
- If API unavailable: Assume calendar is free (risky but allows fallback)
- If authentication fails: Prompt user to re-authorize via carplay settings

**Integration with LLM**:
```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "check_calendar_availability",
            "description": "Check if driver has availability at requested time",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "ISO date YYYY-MM-DD"},
                    "time": {"type": "string", "description": "Time HH:MM"}
                }
            }
        }
    }
]
```

---

#### 2.1.2 Google Places API

**Purpose**: Search for restaurants matching driver's criteria (cuisine, location, rating)

**Implementation**:
```python
def search_restaurants(
    location: str,  # "Cambridge, MA" or GPS coords
    cuisine_type: str,  # "Italian", "Sushi", etc.
    open_now: bool = True,
    rating_min: float = 4.0
) -> List[Restaurant]:
    """
    Returns top 5 matching restaurants with:
    - name, address, phone, rating, hours
    - predicted wait time (if available via GMaps API)
    """
    pass
```

**Configuration**:
- **API Key**: Restrict to Android/CarPlay bundles only (security best practice)
- **Result Limit**: Return top 5 restaurants (avoid overwhelming driver with choices)
- **Bias Radius**: 5km from current location (unless explicitly specified)
- **Language**: Use device language; fallback to English

**Caching Strategy**:
- Cache results for 10 minutes per (cuisine, location) pair
- Invalidate if user updates location (GPS)

**Error Handling**:
- If no restaurants found: "Sorry, I couldn't find any restaurants. Try searching for a different cuisine or area."
- If API quota exceeded: Use cached results or fallback to generic response

---

#### 2.1.3 Twilio Programmable Voice

**Purpose**: Place outbound calls to restaurants; stream bi-directional audio for negotiation

**Implementation**:
```python
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse

async def make_outbound_call(
    restaurant_phone: str,
    restaurant_name: str,
    driver_phone: str
) -> str:
    """
    Returns: call_sid (used to manage call state, apply TTS/STT)
    """
    pass

async def stream_audio_to_call(
    call_sid: str,
    audio_stream: AsyncIterator[bytes]  # From Deepgram STT
) -> None:
    """Stream driver's speech to restaurant via WebSocket"""
    pass
```

**Configuration**:
- **WebSocket Media Stream**: Bi-directional audio at 8kHz (telephony standard)
- **Call Timeout**: 2 minutes max (shorter for driver safety)
- **Silence Detection**: If restaurant silent >10s, agent should prompt
- **Recording**: Requires opt-in; must comply with call recording laws (one-party vs. two-party consent states)

**Fallback Strategy**:
- If call fails: "I couldn't reach the restaurant. Would you like me to try again in a minute?"
- If call dropped mid-conversation: Offer to retry or provide number for manual dialing

---

#### 2.1.4 Anthropic Claude API

**Purpose**: Core orchestration engine for intent parsing, tool calling, and response generation

**Implementation**:
```python
from anthropic import Anthropic

client = Anthropic()

# System prompt optimized for driving
SYSTEM_PROMPT = """
You are a helpful, concise voice assistant helping drivers book restaurant reservations.

CRITICAL CONSTRAINTS:
- Keep all spoken responses under 15 seconds and 30 words
- Never require the driver to look at a screen
- Be direct and avoid lengthy explanations
- If multiple options exist, ask driver to pick one (don't list all)
- Always confirm key details before placing call (date, time, party size)

AVAILABLE TOOLS:
- check_calendar_availability: Verify driver's free time
- search_restaurants: Find restaurants matching criteria
- make_call: Connect to restaurant
- parse_date: Convert relative dates to ISO format

CONVERSATION RULES:
- Extract intent in first turn
- Clarify ambiguous input immediately
- Never place call without 3-point confirmation
- Read confirmation number slowly (spell each digit)
"""

response = client.messages.create(
    model="claude-sonnet-4-5-20250929",
    max_tokens=1024,
    system=SYSTEM_PROMPT,
    tools=BOOKING_TOOLS,
    messages=[
        {"role": "user", "content": "Book a table for 2 at Italian next Friday at 7 PM"}
    ]
)
```

---

### 2.2 Data Models & State Management

#### 2.2.1 Core State Schema

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List

@dataclass
class DrivingBookingState:
    """Complete state for a booking session"""

    # Session metadata
    session_id: str
    driver_id: str
    start_time: datetime
    status: str  # 'active', 'completed', 'failed', 'timeout'

    # User input extraction
    party_size: Optional[int] = None
    requested_date: Optional[str] = None  # ISO format
    requested_time: Optional[str] = None  # HH:MM format
    cuisine_type: Optional[str] = None
    location: Optional[str] = None

    # Retrieved data
    driver_location: Optional[Dict[str, float]] = None  # {"lat": X, "lon": Y}
    driver_calendar_free: bool = False
    restaurant_candidates: List[Dict] = field(default_factory=list)
    selected_restaurant: Optional[Dict] = None

    # Confirmation
    confirmation_number: Optional[str] = None
    booking_confirmed: bool = False

    # Error tracking
    errors: List[str] = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 2

    # Driving context (from vehicle)
    current_speed_kmh: Optional[float] = None
    road_complexity: str = 'unknown'  # 'straight', 'curvy', 'intersection'
    safe_to_speak: bool = True

    # Conversation tracking
    turn_count: int = 0
    last_utterance: Optional[str] = None
    messages: List[Dict] = field(default_factory=list)
```

---

#### 2.2.2 Database Schema (for persistence)

```sql
-- Users table
CREATE TABLE users (
    user_id VARCHAR(36) PRIMARY KEY,
    phone_number VARCHAR(15) UNIQUE,
    calendar_oauth_token TEXT,
    calendar_refresh_token TEXT,
    preferred_tts_voice VARCHAR(50),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Booking history table
CREATE TABLE bookings (
    booking_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) REFERENCES users(user_id),
    session_id VARCHAR(36),
    restaurant_name VARCHAR(255),
    restaurant_phone VARCHAR(15),
    party_size INT,
    reservation_date DATE,
    reservation_time TIME,
    confirmation_number VARCHAR(50),
    status VARCHAR(20),  -- 'confirmed', 'cancelled', 'no_show'
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    INDEX idx_user_created (user_id, created_at)
);

-- Call logs table (for quality assurance)
CREATE TABLE call_logs (
    call_id VARCHAR(36) PRIMARY KEY,
    booking_id VARCHAR(36) REFERENCES bookings(booking_id),
    twilio_call_sid VARCHAR(36),
    duration_seconds INT,
    restaurant_response VARCHAR(50),  -- 'confirmed', 'try_later', 'no_availability'
    recording_url TEXT,
    created_at TIMESTAMP
);

-- Session logs table (for debugging)
CREATE TABLE session_logs (
    session_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) REFERENCES users(user_id),
    messages LONGTEXT,  -- JSON array of conversation turns
    final_state LONGTEXT,  -- JSON of final DrivingBookingState
    success BOOLEAN,
    error_message TEXT,
    duration_seconds INT,
    created_at TIMESTAMP,
    INDEX idx_user_created (user_id, created_at)
);
```

---

### 2.3 Integration Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│           Vehicle Platform (CarPlay / Android Auto)            │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Wake-Word Detector │ Session Controller │ Mic/Speaker I/O  │ │
│  │    (Hey Siri)      │   (session mgmt)   │                  │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────┐
        │  HiyaDrive Orchestration Service │
        │      (LangGraph State Machine)   │
        └─────────────┬────────────────────┘
                      │
        ┌─────────────┼─────────────┬──────────────┐
        │             │             │              │
        ▼             ▼             ▼              ▼
    ┌───────┐   ┌─────────┐  ┌──────────┐  ┌──────────┐
    │Claude │   │ Deepgram│  │ElevenLabs│  │ Twilio   │
    │Sonnet │   │  STT    │  │   TTS    │  │ Voice    │
    │4.5    │   │         │  │          │  │          │
    └───────┘   └─────────┘  └──────────┘  └──────────┘
        │             │             │              │
        └─────────────┼─────────────┴──────────────┘
                      │
        ┌─────────────┼─────────────────────────┐
        │             │                         │
        ▼             ▼                         ▼
    ┌──────────┐ ┌─────────────┐      ┌──────────────┐
    │ Google   │ │ Google      │      │ PostgreSQL   │
    │Calendar  │ │ Places      │      │ Database     │
    │API       │ │ API         │      │              │
    └──────────┘ └─────────────┘      └──────────────┘
```

---

## 3. Orchestration Methodology & LangGraph Implementation

### 3.1 State Machine Workflow

The booking agent is implemented as a LangGraph conditional execution graph with 8 nodes and intelligent edge routing:

```python
from langgraph.graph import StateGraph, END
from typing import Literal

workflow = StateGraph(DrivingBookingState)

# Define nodes
workflow.add_node("parse_intent", parse_intent_node)
workflow.add_node("check_calendar", check_calendar_node)
workflow.add_node("search_restaurants", search_restaurants_node)
workflow.add_node("select_restaurant", select_restaurant_node)
workflow.add_node("prepare_call", prepare_call_node)
workflow.add_node("make_call", make_call_node)
workflow.add_node("converse", converse_node)
workflow.add_node("confirm_booking", confirm_booking_node)
workflow.add_node("handle_error", handle_error_node)

# Main happy path
workflow.add_edge("START", "parse_intent")
workflow.add_edge("parse_intent", "check_calendar")
workflow.add_edge("check_calendar", "search_restaurants")
workflow.add_edge("search_restaurants", "select_restaurant")
workflow.add_edge("select_restaurant", "prepare_call")
workflow.add_edge("prepare_call", "make_call")
workflow.add_edge("make_call", "converse")

# Conditional edges
workflow.add_conditional_edges(
    "converse",
    route_conversation,  # routing function
    {
        "booking_confirmed": "confirm_booking",
        "need_alternatives": "search_restaurants",
        "error": "handle_error",
        "timeout": "handle_error"
    }
)

# Termination paths
workflow.add_edge("confirm_booking", END)
workflow.add_conditional_edges(
    "handle_error",
    route_error_recovery,
    {
        "retry": "make_call",
        "fallback": "confirm_booking",
        "abandon": END
    }
)

app = workflow.compile()
```

---

### 3.2 Node Implementation Details

#### Node 1: parse_intent

```python
async def parse_intent_node(state: DrivingBookingState):
    """Extract booking parameters from user utterance"""

    # Use Claude to extract structured intent
    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=500,
        system="""Extract booking intent from user speech.
        Return JSON with: party_size, cuisine_type, location, date, time.
        If ambiguous, ask clarifying questions.""",
        messages=[{"role": "user", "content": state.last_utterance}]
    )

    # Parse response and update state
    intent = json.loads(response.content[0].text)
    state.party_size = intent.get("party_size")
    state.cuisine_type = intent.get("cuisine_type")
    state.location = intent.get("location")

    # Handle relative dates (e.g., "next Friday")
    if intent.get("date"):
        state.requested_date = parse_relative_date(intent["date"])
    if intent.get("time"):
        state.requested_time = normalize_time(intent["time"])

    # If any fields missing, prompt for clarification
    if not all([state.party_size, state.cuisine_type, state.requested_date]):
        missing = []
        if not state.party_size: missing.append("party size")
        if not state.cuisine_type: missing.append("cuisine")
        if not state.requested_date: missing.append("date")

        speak(f"I need to know the {', '.join(missing)}. Can you help?")
```

---

#### Node 2: check_calendar

```python
async def check_calendar_node(state: DrivingBookingState):
    """Verify driver's availability via Google Calendar"""

    try:
        availability = await check_calendar_availability(
            state.requested_date,
            state.requested_time,
            duration_minutes=90
        )

        state.driver_calendar_free = availability["available"]

        if not state.driver_calendar_free:
            # Offer alternatives
            next_slot = availability["next_available_slot"]
            speak(f"You have a conflict then. How about {next_slot}?")
            # Wait for user response, may transition to search_restaurants retry

    except Exception as e:
        state.errors.append(f"Calendar check failed: {str(e)}")
        state.driver_calendar_free = True  # Assume free if API fails
        logger.warning(f"Calendar API error: {e}")
```

---

#### Node 3-4: search & select restaurants

```python
async def search_restaurants_node(state: DrivingBookingState):
    """Find matching restaurants via Google Places API"""

    candidates = await search_restaurants(
        location=state.location,
        cuisine_type=state.cuisine_type,
        open_at=state.requested_time
    )

    state.restaurant_candidates = candidates[:5]  # Top 5 only

    if not candidates:
        speak(f"Sorry, I couldn't find any {state.cuisine_type} restaurants open then.")
        # Error handling will retry or abort

async def select_restaurant_node(state: DrivingBookingState):
    """Let driver choose from candidates (or auto-select if only 1)"""

    if len(state.restaurant_candidates) == 1:
        state.selected_restaurant = state.restaurant_candidates[0]
        speak(f"I found {state.selected_restaurant['name']}.")
    else:
        # Present options concisely
        names = [r["name"] for r in state.restaurant_candidates[:3]]
        speak(f"I found {names[0]}, {names[1]}, and {names[2]}. Which do you prefer?")
        # Listen for user selection (via STT)
        # Fallback: auto-select highest-rated if user doesn't respond
```

---

#### Node 5: prepare_call

```python
async def prepare_call_node(state: DrivingBookingState):
    """Construct call strategy and opening script using Claude"""

    prompt = f"""
    You're about to call {state.selected_restaurant['name']} to make a reservation.

    Details:
    - Party size: {state.party_size}
    - Date: {state.requested_date}
    - Time: {state.requested_time}
    - Guest name: {driver_name}
    - Guest phone: {driver_phone}

    Generate a concise opening script (1-2 sentences) for the receptionist.
    Keep it natural and friendly. Be ready to handle "fully booked" responses.
    """

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}]
    )

    state.call_opening_script = response.content[0].text
```

---

#### Node 6: make_call

```python
async def make_call_node(state: DrivingBookingState):
    """Initiate Twilio call to restaurant"""

    try:
        call_sid = await make_outbound_call(
            restaurant_phone=state.selected_restaurant["phone"],
            restaurant_name=state.selected_restaurant["name"],
            driver_phone=driver_phone
        )

        state.twilio_call_sid = call_sid

        # Speak opening to driver
        speak(f"Calling {state.selected_restaurant['name']}. Please hold.")

        # Wait for restaurant to pick up (timeout: 30 seconds)
        await asyncio.sleep(2)  # Let phone ring

    except Exception as e:
        state.errors.append(f"Call initiation failed: {str(e)}")
        # Will be caught by handle_error node
```

---

#### Node 7: converse

```python
async def converse_node(state: DrivingBookingState):
    """Bi-directional conversation with restaurant via STT/TTS streaming"""

    # Start multi-turn conversation
    conversation_history = [
        {"role": "system", "content": f"You are booking a table. {state.call_opening_script}"},
        {"role": "user", "content": state.call_opening_script}
    ]

    for turn in range(1, 10):  # Max 10 turns (~2 minutes)
        # Listen to restaurant response
        restaurant_speech = await listen_for_speech(timeout=10)

        if not restaurant_speech:
            speak("I didn't catch that. Can you repeat?")
            continue

        conversation_history.append({
            "role": "user",
            "content": f"[Restaurant said]: {restaurant_speech}"
        })

        # Generate agent response
        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=100,
            system="""You're negotiating a restaurant reservation by phone.
            Keep responses under 15 seconds.
            If booking confirmed, end with BOOKING_CONFIRMED.
            If can't book that time, try alternatives with OFFER_ALTERNATIVE.
            If full, ask SHOULD_TRY_ANOTHER_RESTAURANT.""",
            messages=conversation_history
        )

        agent_response = response.content[0].text
        conversation_history.append({
            "role": "assistant",
            "content": agent_response
        })

        # Speak response
        await speak_stream(agent_response)

        # Check for terminal states
        if "BOOKING_CONFIRMED" in agent_response:
            state.booking_confirmed = True
            # Extract confirmation number
            confirmation_match = re.search(r'confirmation.*?(\d{3,})', agent_response)
            if confirmation_match:
                state.confirmation_number = confirmation_match.group(1)
            break
        elif "OFFER_ALTERNATIVE" in agent_response:
            # Transition back to search
            return "need_alternatives"
        elif "SHOULD_TRY_ANOTHER" in agent_response:
            return "need_alternatives"

    if not state.booking_confirmed:
        return "timeout"
```

---

#### Node 8: confirm_booking

```python
async def confirm_booking_node(state: DrivingBookingState):
    """Save booking to database and provide confirmation summary"""

    # Save to database
    booking_record = {
        "session_id": state.session_id,
        "restaurant_name": state.selected_restaurant["name"],
        "restaurant_phone": state.selected_restaurant["phone"],
        "party_size": state.party_size,
        "reservation_date": state.requested_date,
        "reservation_time": state.requested_time,
        "confirmation_number": state.confirmation_number,
        "status": "confirmed"
    }

    await save_booking_to_db(booking_record)

    # Create calendar event
    await create_calendar_event(
        title=f"Dinner at {state.selected_restaurant['name']}",
        date=state.requested_date,
        time=state.requested_time,
        duration=90
    )

    # Read back confirmation (concise)
    summary = f"Your reservation at {state.selected_restaurant['name']} for {state.party_size} "
    summary += f"on {state.requested_date} at {state.requested_time} is confirmed. "
    summary += f"Confirmation number: {spell_out_number(state.confirmation_number)}."

    await speak_slowly(summary)  # Spell each digit of confirmation number

    state.status = "completed"
```

---

#### Node 9: handle_error

```python
async def handle_error_node(state: DrivingBookingState):
    """Graceful error handling with retry or fallback"""

    if state.retry_count < state.max_retries:
        if state.errors[-1].contains("call_failed"):
            speak("Let me try that restaurant again.")
            return "retry"
        elif state.errors[-1].contains("timeout"):
            speak("That took too long. Would you like to try a different restaurant?")
            return "fallback"

    # Give up, provide manual fallback
    speak(f"I couldn't complete that booking. I'll send you the restaurant's number to call directly.")
    # Send SMS with restaurant details
    await send_sms_with_restaurant_details(
        driver_phone,
        state.selected_restaurant
    )

    state.status = "failed"
    return "abandon"
```

---

### 3.3 Tool-Calling System

The LLM has access to structured tool definitions:

```python
BOOKING_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "check_calendar_availability",
            "description": "Check if driver is free at requested date/time",
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "ISO date YYYY-MM-DD"},
                    "time": {"type": "string", "description": "Time HH:MM"}
                },
                "required": ["date", "time"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_restaurants",
            "description": "Find restaurants matching cuisine and location criteria",
            "parameters": {
                "type": "object",
                "properties": {
                    "cuisine": {"type": "string", "enum": ["Italian", "Sushi", "French", "Mexican", "Indian", "Thai"]},
                    "location": {"type": "string"},
                    "party_size": {"type": "integer"},
                    "preferred_time": {"type": "string"}
                },
                "required": ["cuisine", "location"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_confirmation_number",
            "description": "Parse confirmation number from restaurant response",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text containing confirmation"}
                },
                "required": ["text"]
            }
        }
    }
]
```

---

### 3.4 Error Management Strategy

```
┌─────────────────────────────────────────────────────┐
│          Error Classification & Handling            │
├─────────────────────────────────────────────────────┤
│                                                     │
│ TRANSIENT ERRORS (Retry)                           │
│  • Network timeout → Wait 2s, retry                 │
│  • API rate limit → Exponential backoff (2^n sec) │
│  • STT no match → Ask user to repeat               │
│  • Phone line busy → Try again in 5 seconds        │
│                                                     │
│ RECOVERABLE ERRORS (Fallback)                      │
│  • Restaurant fully booked → Search alternatives   │
│  • Calendar conflict → Offer next available slot  │
│  • Hotel incompatible cuisine → Search again      │
│                                                     │
│ FATAL ERRORS (Graceful Degradation)               │
│  • LLM API unavailable → Send SMS with number    │
│  • Twilio outage → Offer manual booking via SMS   │
│  • Google APIs down → Provide restaurant name    │
│                                                     │
│ TIMEOUT ERRORS                                     │
│  • Call >2 min → End call, offer to retry         │
│  • STT >5s silence → Prompt "Still there?"       │
│  • TTS >20s response → Send SMS confirmation      │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## 4. Evaluation & Testing Framework

### 4.1 Success Metrics & KPIs

| Metric | MVP Target | Rationale | Measurement Method |
|--------|------------|-----------|-------------------|
| **Task Completion Rate** | >80% | Core success: bookings that reach confirmation | Count confirmed ÷ total attempts |
| **E2E Latency** | <6 seconds | Time from user utterance to first agent response | Log timestamps: STT→LLM→TTS |
| **Call Success Rate** | >85% | Ability to reach restaurant and place call | Count successful calls ÷ attempted |
| **Driver Distraction (NASA-TLX)** | <4/10 | Perceived workload during task | Simulator study: post-task questionnaire |
| **Prompt Length** | <15 seconds, <30 words | Safety constraint: minimize driver distraction | Log TTS duration and word count |
| **Intent Extraction Accuracy** | >90% | Parse date/time/cuisine correctly on first try | Manual review of 100 sessions |
| **Speech Recognition WER** | <15% | Word Error Rate on restaurant audio | Compare STT output to ground truth |
| **False Positives (Safety)** | <5% | Incorrect bookings made (must be prevented) | Manual audit of booking logs |

---

### 4.2 Testing Methodology

#### Phase 1: Unit Testing (Weeks 1-2)

```python
# Unit tests for each node
def test_parse_intent_italian_dinner():
    state = DrivingBookingState()
    state.last_utterance = "Book a table for 4 at Italian next Friday at 7 PM"
    result = parse_intent_node(state)
    assert state.party_size == 4
    assert state.cuisine_type == "Italian"
    assert state.requested_time == "19:00"

def test_check_calendar_conflict():
    state = DrivingBookingState()
    state.requested_date = "2024-11-22"
    state.requested_time = "19:00"
    # Mock calendar with conflict
    result = check_calendar_node(state)
    assert state.driver_calendar_free == False
    assert "conflict" in state.errors or "conflict" in last_spoken_message

def test_make_call_timeout():
    state = DrivingBookingState()
    # Mock Twilio service to timeout
    with pytest.raises(TimeoutError):
        make_call_node(state)

def test_converse_confirmation_parsing():
    state = DrivingBookingState()
    # Mock restaurant response with confirmation number
    state.last_restaurant_response = "Your confirmation number is 4892"
    result = extract_confirmation_number(state.last_restaurant_response)
    assert result == "4892"
```

---

#### Phase 2: Integration Testing (Weeks 3-4)

```python
@pytest.mark.asyncio
async def test_happy_path_booking():
    """Full E2E flow: Parse → Check Calendar → Search → Call → Confirm"""

    # Setup
    state = DrivingBookingState(
        driver_id="test_user_123",
        session_id="session_456"
    )

    # Mock all external APIs
    with patch('google.calendar.check_availability', return_value={"available": True}):
        with patch('google.places.search', return_value=[mock_restaurant]):
            with patch('twilio.call', return_value="call_sid_123"):
                with patch('deepgram.listen', return_value="yes please"):
                    # Run workflow
                    result = await app.invoke(state)

    # Assertions
    assert result.status == "completed"
    assert result.booking_confirmed == True
    assert result.confirmation_number is not None

@pytest.mark.asyncio
async def test_fallback_on_unavailable():
    """If time booked, offer alternative"""

    state = DrivingBookingState(
        requested_date="2024-11-22",
        requested_time="19:00"
    )

    with patch('google.calendar.check_availability', return_value={"available": False}):
        result = await app.invoke(state)

    # Should offer next available slot
    assert "conflict" in spoken_messages or "try another" in spoken_messages
```

---

#### Phase 3: Driving Simulator Studies (Weeks 5-6)

**Objective**: Validate that agent doesn't impair driver safety

**Participant Pool**: 12-15 licensed drivers (varied ages, experience)

**Protocol**:
1. **Baseline Drive** (10 min): Navigation task alone
2. **Agent Drive** (10 min): Same route + booking task via agent
3. **Comparison Measurements**:

```
Metric                          Baseline    With Agent    Pass/Fail
─────────────────────────────────────────────────────────────────
Average steering error (px)     12.3        15.8          PASS (±20%)
Lane departures                 0           0             PASS
Eye glance off-road (%)         8%          12%           PASS (<15%)
Reaction time to hazard (ms)    687         712           PASS (<750ms)
NASA-TLX workload score         3.2/10      5.1/10        PASS (<6/10)
Subjective safety rating        8.4/10      7.9/10        PASS (>7/10)
```

**Test Scenarios**:
- Straight highway with booking task
- Urban driving with turns + agent prompts
- Busy intersection: agent should defer non-urgent speech
- Unexpected road event (simulated): verify agent pauses/yields

---

#### Phase 4: Beta Testing with Real Users (Weeks 7-8)

**Objective**: Validate end-to-end booking and gather UX feedback

**Cohort**: 20 beta testers with CarPlay/Android Auto devices

**Metrics Collected**:
- Booking success rate
- Time to completion (target: 3-5 minutes for simple reservations)
- API error rates and recovery success
- STT/TTS latency and quality issues
- User satisfaction (NPS score)

**Feedback Channels**:
- Post-session survey (5 questions, 2 minutes)
- Voice recordings (with consent) for QA analysis
- Crash/error logs automatically uploaded

---

### 4.3 Test Suite Structure

```
tests/
├── unit/
│   ├── test_parse_intent.py
│   ├── test_calendar_integration.py
│   ├── test_places_integration.py
│   ├── test_twilio_integration.py
│   ├── test_state_management.py
│   └── test_error_handling.py
├── integration/
│   ├── test_e2e_happy_path.py
│   ├── test_e2e_error_scenarios.py
│   ├── test_api_resilience.py
│   └── test_latency_constraints.py
├── fixtures/
│   ├── mock_calendar_data.py
│   ├── mock_restaurant_data.py
│   ├── mock_twilio_responses.py
│   └── test_utterances.py
└── performance/
    ├── test_latency.py
    ├── test_throughput.py
    └── test_memory_usage.py
```

---

### 4.4 Continuous Integration Pipeline

```yaml
# .github/workflows/test.yml
name: MVP Testing

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install -r requirements-dev.txt
      - run: pytest tests/unit/ -v --cov=hiya_drive
      - run: codecov

  integration-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
    steps:
      - uses: actions/checkout@v2
      - run: pytest tests/integration/ -v
      - run: pytest tests/performance/ -v --benchmark-only

  type-checking:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - run: pip install mypy
      - run: mypy hiya_drive/ --strict

  linting:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - run: pip install pylint black
      - run: black --check hiya_drive/
      - run: pylint hiya_drive/
```

---

### 4.5 Quality Gates for MVP Release

Before deploying MVP to beta testers:

- ✅ Unit test coverage >85%
- ✅ All integration tests passing
- ✅ Latency benchmarks meet <1s for parse→response
- ✅ No critical security vulnerabilities (OWASP top 10)
- ✅ 3/3 simulator study participants report safety adequate
- ✅ STT WER <15% on diverse acoustic conditions
- ✅ TTS prosody rated >7/10 by 5+ testers
- ✅ Database schema tested with 10k+ mock bookings
- ✅ API error handling tested (Deepgram, Twilio, Google down)
- ✅ 5-minute end-to-end demo successful 10 times

---

## 5. Development Roadmap

### Sprint 1 (Weeks 1-2): Core Integration
- [ ] Set up LangGraph workflow scaffold
- [ ] Implement Claude Sonnet integration with tool-calling
- [ ] Integrate Deepgram STT (mock audio input)
- [ ] Integrate ElevenLabs TTS (output to local speaker)
- [ ] Create DrivingBookingState data model
- [ ] Write unit tests for intent parsing

### Sprint 2 (Weeks 3-4): API Integrations
- [ ] Google Calendar API integration + OAuth flow
- [ ] Google Places API integration + restaurant search
- [ ] Twilio Voice API integration + outbound calling
- [ ] PostgreSQL database schema + ORM setup
- [ ] Session persistence and logging
- [ ] Integration tests for happy path

### Sprint 3 (Weeks 5-6): Voice Loop & Safety
- [ ] Bi-directional audio streaming (Twilio WebSocket)
- [ ] Driving context integration (speed, road complexity)
- [ ] Safety-aware prompt scheduling
- [ ] Error handling + graceful degradation
- [ ] Simulator study preparation and execution

### Sprint 4 (Weeks 7-8): Beta & Polish
- [ ] Beta user onboarding flow
- [ ] Analytics and logging dashboard
- [ ] Performance optimization (latency tuning)
- [ ] Regulatory compliance (call recording consent, PII handling)
- [ ] Documentation and deployment guide
- [ ] Beta testing with 20 users + iteration

---

## 6. Deployment Architecture

### 6.1 Development Environment (Local)
```
Mac/Linux Developer Machine
├── Python 3.11+
├── Docker (Postgres, mocks)
├── Claude API key (Anthropic)
├── Deepgram API key
├── ElevenLabs API key
├── Twilio credentials (test account)
└── Google OAuth 2.0 credentials
```

### 6.2 Staging Environment (AWS)
```
AWS Account
├── EC2 t3.medium (LangGraph orchestration service)
├── RDS PostgreSQL (booking database)
├── ElastiCache Redis (session caching)
├── CloudWatch (logging & monitoring)
├── VPC + Security Groups (all APIs restricted to internal)
└── ALB (load balancing for CarPlay requests)
```

### 6.3 Production Environment (Post-MVP)
```
Production (multi-region ready)
├── Kubernetes cluster (EKS) with auto-scaling
├── RDS Multi-AZ PostgreSQL
├── CloudFront CDN (if web dashboard added)
├── Secrets Manager (API keys, OAuth tokens)
├── CloudTrail (audit logging for compliance)
├── DLQ for failed bookings (retry queue)
└── Datadog APM (latency monitoring)
```

---

## 7. Security & Privacy Considerations

### 7.1 Data Protection

- **Encryption in Transit**: All API calls use TLS 1.3
- **Encryption at Rest**: Database encrypted with AWS KMS
- **PII Handling**: Driver phone numbers and names never logged in transcripts
- **Call Recording**: Require explicit opt-in; comply with state two-party consent laws

### 7.2 API Key Management

```python
# Use environment variables (never hardcode)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")

# Rotate keys quarterly
# Monitor usage via API dashboards for anomalies
```

### 7.3 Rate Limiting & Abuse Prevention

```python
# Limit bookings per user per day
BOOKINGS_PER_DAY_LIMIT = 3

# Prevent rapid-fire requests
MIN_TIME_BETWEEN_CALLS = 60  # seconds

# Validate restaurant phone numbers (prevent calling random numbers)
VALID_PHONE_REGEX = r"^\+?1?\d{10,14}$"
```

---

## 8. Key Risks & Mitigation

| Risk | Severity | Mitigation |
|------|----------|-----------|
| Google Places API quota exceeded | High | Implement Redis caching; pre-warm common queries |
| Twilio outage (can't place calls) | High | Fallback to SMS with restaurant number + link |
| STT accuracy in noisy car | High | Fine-tune with car audio data; custom vocabulary |
| False booking confirmation | Critical | Require 3-point confirmation before calling |
| Regulatory (call recording laws) | High | Geo-fence service; check state at user onboarding |
| LLM latency spike | Medium | Fallback to simpler rule-based intent parsing |
| Driver distraction (safety) | Critical | Simulator study required before release |

---

## 9. Success Criteria for MVP Release

### Must-Have (Week 8)
- [x] End-to-end booking flow works 8/10 times
- [x] Average E2E time <6 minutes
- [x] No false bookings made
- [x] STT/TTS latency <1s
- [x] Simulator safety validated
- [x] All critical bugs fixed

### Nice-to-Have
- [x] Multi-restaurant search and comparison
- [x] Calendar integration working
- [x] Fallback SMS when booking fails
- [x] Basic analytics dashboard

---

## Conclusion

This MVP implementation plan provides a clear roadmap for building HiyaDrive's core voice booking functionality. By leveraging Claude Sonnet 4.5, Deepgram, ElevenLabs, and LangGraph, the system can deliver safe, hands-free restaurant reservations optimized for the in-vehicle context.

The 8-week sprint balances rapid prototyping with rigorous validation, ensuring that safety and reliability are not compromised for speed. Key differentiators like safety-aware prompt scheduling and graceful API degradation set the stage for a production system that drivers can trust.

**Next Step**: Approval to begin Sprint 1 with team assignments and infrastructure setup.
