# Calendar Error Handling in HiyaDrive

## Overview

The system handles calendar errors in two different places with different strategies:

### 1. **Step 2: Calendar Availability Check** (CRITICAL)
### 2. **Step 8: Add Reservation to Calendar** (NON-CRITICAL)

---

## Step 2: Checking Calendar Availability (CRITICAL)

### What Happens
1. User provides booking details (date, time, party size)
2. System checks if user is available at that time
3. If calendar check fails → **entire booking is CANCELLED**

### Error Handling Flow

```
┌─────────────────────────────────────────┐
│ Step 2: Check Calendar Availability     │
└────────────┬────────────────────────────┘
             │
             ├─→ TRY: calendar_service.is_available()
             │
             └─→ Catches any Exception
                 │
                 ├─→ Add error to state.errors[]
                 │
                 ├─→ Log error message
                 │
                 └─→ Continue to check state.errors

┌────────────────────────────────────────┐
│ Interactive Orchestrator (line 116)     │
└────────────┬────────────────────────────┘
             │
             ├─→ if state.errors:
             │   ├─→ Speak: "Sorry, I couldn't check your calendar"
             │   ├─→ Set status = SessionStatus.FAILED
             │   └─→ Go to GOODBYE
             │
             └─→ else: Continue to Step 3 (search restaurants)
```

### Code Location
- **Calendar service**: [`hiya_drive/integrations/calendar_service.py:68-155`](hiya_drive/integrations/calendar_service.py#L68-L155) - `is_available()` method
- **Orchestrator**: [`hiya_drive/core/orchestrator.py:199-223`](hiya_drive/core/orchestrator.py#L199-L223) - `check_calendar()` method  
- **Voice orchestrator**: [`hiya_drive/core/interactive_voice_orchestrator.py:106-128`](hiya_drive/core/interactive_voice_orchestrator.py#L106-L128) - Error handling

### Possible Errors

| Error | Cause | User Hears |
|-------|-------|-----------|
| **Not initialized** | Calendar credentials missing or invalid | "Sorry, I couldn't check your calendar. Error: Calendar service not initialized" |
| **Invalid time format** | Can't parse the date/time string | "Sorry, I couldn't check your calendar. Error: Invalid time format: {input}" |
| **API error** | Google Calendar API call failed | "Sorry, I couldn't check your calendar. Error: {details}" |
| **Permission denied** | Service account can't access calendar | "Sorry, I couldn't check your calendar. Error: Insufficient permissions" |

### What NOT to Say
The system does **NOT** say which exact error occurred (privacy). Example:
- ❌ "Error: Calendar ID not properly shared with service account"
- ✅ "Sorry, I couldn't check your calendar"

---

## Step 8: Add Reservation to Calendar (NON-CRITICAL)

### What Happens
1. Restaurant confirms the reservation
2. System tries to add event to user's calendar
3. **Even if this fails, the reservation is still successful**

### Error Handling Flow

```
┌──────────────────────────────────┐
│ Step 8: Confirm Booking          │
│ (Reservation already confirmed)  │
└────────────┬─────────────────────┘
             │
             ├─→ TRY: calendar_service.add_reservation_event()
             │
             └─→ Catches all Exceptions
                 │
                 ├─→ Log warning (not error!)
                 │
                 └─→ Continue anyway

┌──────────────────────────────────┐
│ Result Handling (line 309-322)   │
└────────────┬─────────────────────┘
             │
             ├─→ if success == True:
             │   ├─→ Speak: "I've saved your reservation to your calendar"
             │   └─→ status = COMPLETED
             │
             └─→ if success == False or Exception:
                 ├─→ Log warning (NOT critical)
                 ├─→ DO NOT speak error to user
                 └─→ status = COMPLETED (still!)
```

### Code Location
- **Calendar service**: [`hiya_drive/integrations/calendar_service.py:155-252`](hiya_drive/integrations/calendar_service.py#L155-L252) - `add_reservation_event()` method
- **Voice orchestrator**: [`hiya_drive/core/interactive_voice_orchestrator.py:293-325`](hiya_drive/core/interactive_voice_orchestrator.py#L293-L325) - Calendar add & error handling

### Possible Errors

| Error | Cause | Behavior |
|-------|-------|----------|
| **Not initialized** | Calendar credentials missing | Returns False, session completes, logs warning |
| **Invalid time format** | Can't parse the date/time | Returns False, session completes, logs warning |
| **Permission denied** | Can't write to calendar | Raises Exception, caught & logged, session completes |
| **Calendar not shared** | Service account can't access | Returns False, caught, session completes |

### What User Hears
- ✅ If successful: "I've saved your reservation to your calendar."
- ✅ If failed: **Nothing** - reservation is still confirmed!

---

## Error Handling Summary Table

| Step | Error Type | Severity | User Impact | Session Status |
|------|-----------|----------|------------|-----------------|
| **2** | Calendar not accessible | 🔴 FATAL | Entire booking cancelled | FAILED |
| **2** | Invalid time format | 🔴 FATAL | Entire booking cancelled | FAILED |
| **2** | Credentials missing | 🔴 FATAL | Entire booking cancelled | FAILED |
| **8** | Calendar not accessible | 🟡 WARNING | Booking succeeds, no calendar entry | COMPLETED |
| **8** | Can't add event | 🟡 WARNING | Booking succeeds, no calendar entry | COMPLETED |
| **8** | Permission denied | 🟡 WARNING | Booking succeeds, no calendar entry | COMPLETED |

---

## Code Comparison

### Critical Error (Step 2)
```python
# orchestrator.py - check_calendar()
try:
    state.driver_calendar_free = await calendar_service.is_available(booking_time)
except Exception as e:
    error_msg = f"Calendar availability check failed: {str(e)}"
    state.add_error(error_msg)  # ← FATAL: adds error
    return state

# interactive_voice_orchestrator.py
if state.errors:  # ← Check for errors
    await voice_processor.speak("Sorry, I couldn't check your calendar")
    state.status = SessionStatus.FAILED  # ← Session ends
```

### Non-Critical Error (Step 8)
```python
# interactive_voice_orchestrator.py
try:
    success = await calendar_service.add_reservation_event(...)
    if success:
        await voice_processor.speak("I've saved your reservation to your calendar")
    else:
        # Don't speak anything - reservation still confirmed
        logger.warning("Failed to add reservation to calendar")
except Exception as cal_error:
    # Catch but don't fail
    logger.warning(f"Could not add to calendar: {cal_error}")
    
# Regardless of calendar success/failure:
state.status = SessionStatus.COMPLETED  # ← Session completes!
```

---

## Design Rationale

### Why are these different?

1. **Step 2 is critical** because:
   - We MUST know if the user is available before calling the restaurant
   - Making a reservation when user is busy = bad experience
   - Better to fail now than waste time

2. **Step 8 is non-critical** because:
   - Reservation is already confirmed with the restaurant
   - Calendar is just a "nice to have" convenience feature
   - Don't ruin a successful booking just because we couldn't update calendar

### Example Scenario

**Scenario: Calendar can't be accessed**

```
User: "Can you book a restaurant for 4 people on Friday at 7 PM?"

Step 1-2: Check Calendar
  System: "Let me check your calendar availability..."
  ❌ Calendar service is down / not shared
  System: "Sorry, I couldn't check your calendar. Please try again later."
  ↓ Session FAILS - goodbye

User: "Ugh, the calendar wasn't shared, let me try again after I fix that"
---

After user shares calendar:

User: "Can you book a restaurant for 4 people on Friday at 7 PM?"

Step 1-3: Parse intent → Check calendar ✓ Available
Step 4-7: Find restaurants → Call restaurant ✓ Confirmation #123

Step 8: Add to Calendar
  System: "I've saved your reservation to your calendar."
  OR (if calendar still failing):
  System: "Your reservation is confirmed! Let me try to save to calendar..."
  ❌ Calendar service is down again
  System: "Your booking is all set. Goodbye!"
  ↑ Session COMPLETES despite calendar error!
```

---

## Testing Calendar Errors

### Simulate Missing Credentials
```bash
# .env - temporarily remove or empty this:
GOOGLE_CALENDAR_CREDENTIALS_PATH=

# Run booking → Should fail at Step 2 with:
# "Sorry, I couldn't check your calendar"
```

### Simulate Invalid Time Format
```bash
# In code, change requested_date/time to invalid values
state.requested_date = "invalid-date"
state.requested_time = "not-a-time"

# Should fail at Step 2 with:
# "Sorry, I couldn't check your calendar"
```

### Simulate Calendar Sharing Issue  
```bash
# .env - set wrong calendar ID
GOOGLE_CALENDAR_ID=wrong-email@gmail.com

# Step 2: Fails - "Sorry, I couldn't check your calendar"
# Even if you got past Step 2, Step 8 would silently fail but session completes
```

---

## How to Debug

### For Step 2 Failures
Check logs:
```bash
tail -f hiya_drive.log | grep "Calendar:"
# Look for: "Calendar availability check failed:"
```

Run verification script:
```bash
python3 hiya_drive/scripts/verify_calendar_access.py
```

### For Step 8 Failures
Check logs:
```bash
tail -f hiya_drive.log | grep "Could not add to calendar"
# or
tail -f hiya_drive.log | grep "Failed to add reservation"
```

The session will complete successfully, but no calendar event will be created.

---

## Future Improvements

### Current Limitation
- Step 8 doesn't inform user if calendar save failed (silent failure)
- Could be improved by checking if calendar is configured before Step 2

### Possible Enhancements
1. **Pre-flight check** before Step 1: "Let me verify I can access your calendar"
2. **Retry logic** for Step 8: Try 3 times with exponential backoff
3. **Fallback option** for Step 8: Save to local file if Google Calendar fails
4. **User notification**: "Calendar entry created locally, will sync to Google when available"

