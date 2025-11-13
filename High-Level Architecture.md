```mermaid
flowchart TD
    V["In vehicle voice platform"]
    W["Wake word detector"]
    S["Session controller"]

    O["Driver booking orchestration - LangGraph state machine"]
    LLM["LLM core engine - Claude Sonnet model"]
    INTEG["Integration layer"]
    CAL["Google Calendar API"]
    PLACE["Google Places API"]
    TWV["Twilio Voice"]
    VEH["Vehicle interface"]

    STT["Speech to text - Deepgram Nova"]
    TTS["Text to speech - ElevenLabs"]
    TEL["Telephony infrastructure - Twilio programmable voice"]

    %% Voice path
    V --> W --> S
    S --> STT --> O
    O --> LLM
    LLM --> INTEG
    INTEG --> CAL
    INTEG --> PLACE
    INTEG --> TWV
    INTEG --> VEH

    LLM --> TTS --> S
    TWV --> TEL
    TEL --> TWV

```
