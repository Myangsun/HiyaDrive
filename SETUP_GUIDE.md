# HiyaDrive Setup Guide

This guide will help you set up the required Google APIs and services for HiyaDrive to work with real data.

## Prerequisites

- Google Cloud Account (https://console.cloud.google.com)
- A Google Cloud Project created
- Existing `.env` file with API keys

---

## 1. Enable Google Places APIs

The system requires **TWO** Google APIs to work:
- **Places API** - for searching restaurants
- **Place Details API** - for getting phone numbers

### Step 1a: Enable Places API (Legacy)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Go to **APIs & Services** → **Library**
3. Search for **"Places API"** (the legacy one labeled "Places API (Old)")
4. Click **Enable**

### Step 1b: Enable Maps JavaScript API (for Place Details)

1. In the same **Library**, search for **"Maps JavaScript API"**
2. Click **Enable**

> ⏱️ **Wait 2-3 minutes** for both APIs to be enabled across Google's systems

### Verify It Works:

Once enabled, your existing `GOOGLE_PLACES_API_KEY` in `.env` will work automatically. The system will:
- Use Places API to search for restaurants
- Use Place Details API to get phone numbers for each restaurant

---

## 2. Set Up Google Calendar API

The system uses Google Calendar to check availability before making reservations.

### Step 1: Create a Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Go to **APIs & Services** → **Credentials**
3. Click **Create Credentials** → **Service Account**
4. Fill in:
   - **Service account name**: `hiya-drive-service`
   - **Service account ID**: Auto-filled
   - **Description**: "HiyaDrive calendar integration"
5. Click **Create and Continue**
6. Skip "Grant this service account access to project" (click **Continue**)
7. Skip "Grant users access" (click **Done**)

### Step 2: Create Service Account Key

1. Click on the service account you just created
2. Go to **Keys** tab
3. Click **Add Key** → **Create new key**
4. Choose **JSON** format
5. Click **Create**

A JSON file will download. This is your credentials file.

### Step 3: Save Credentials

1. Rename the downloaded file to `credentials.json`
2. Copy it to: `/Users/mingyang/Desktop/AI Ideas/HiyaDrive/credentials.json`
3. Update `.env` if needed:
   ```
   GOOGLE_CALENDAR_CREDENTIALS_PATH=/Users/mingyang/Desktop/AI Ideas/HiyaDrive/credentials.json
   ```

### Step 4: Enable Google Calendar API

1. Go to **APIs & Services** → **Library**
2. Search for **"Google Calendar API"**
3. Click **Google Calendar API**
4. Click **Enable**

### Step 5: Share Calendar with Service Account

1. Copy the **client_email** from your `credentials.json` file (looks like: `hiya-drive-service@project-id.iam.gserviceaccount.com`)
2. Go to [Google Calendar](https://calendar.google.com)
3. Go to **Settings** → **Settings**
4. Click **Calendars** and select your calendar
5. Under **Access permissions**, click **Add people**
6. Paste the service account email
7. Give it **Editor** access
8. Click **Send**

---

## 3. Verify Configuration

Run this test to verify everything is set up:

```bash
cd /Users/mingyang/Desktop/AI Ideas/HiyaDrive
python3 << 'EOF'
import asyncio
from hiya_drive.core.orchestrator import BookingOrchestrator

async def test():
    orchestrator = BookingOrchestrator()
    result = await orchestrator.run_booking_session(
        "test_driver",
        "Book a table for 2 at Italian in Boston"
    )
    print("✓ Booking session succeeded!")
    print(f"  Selected: {result.selected_restaurant.name if result.selected_restaurant else 'None'}")

asyncio.run(test())
EOF
```

---

## 4. Summary

| Component | Status | Action |
|-----------|--------|--------|
| **Places API (Legacy)** | ✓ Enable | [Enable](https://console.cloud.google.com/apis/library/places-backend.googleapis.com) |
| **Maps JavaScript API** | ✓ Enable | [Enable](https://console.cloud.google.com/apis/library/maps-backend.googleapis.com) |
| **Google Calendar API** | ✓ Enable | [Enable](https://console.cloud.google.com/apis/library/calendar-json.googleapis.com) |
| **Service Account** | ✓ Create | Create new service account in Credentials |
| **Calendar Share** | ✓ Share | Invite service account email to your calendar |
| **Credentials File** | ✓ Download | Save as `credentials.json` in project root |

---

## Troubleshooting

### "Places API is not enabled"
- Wait 2-3 minutes after enabling and try again
- Check that you enabled the **Places API** (not the new Places API)

### "Google Calendar credentials not found"
- Make sure `credentials.json` is in the correct directory
- Verify `GOOGLE_CALENDAR_CREDENTIALS_PATH` in `.env` matches the file location

### "Unauthorized to access calendar"
- Make sure you shared your calendar with the service account email
- Use the exact `client_email` from your credentials file

---

## Next Steps

Once set up, run the voice mode:

```bash
python -m hiya_drive.main voice
```

Say "Hi driver" to activate the system.
