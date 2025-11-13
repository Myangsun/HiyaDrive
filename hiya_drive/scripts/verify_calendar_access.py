#!/usr/bin/env python3
"""
Verify that the Google Calendar is properly shared with the HiyaDrive service account.
Run this after sharing your calendar to confirm everything is working.
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from hiya_drive.config.settings import settings
from hiya_drive.utils.logger import logger

def verify_calendar_access():
    """Verify calendar sharing is working."""
    
    print("\n" + "=" * 80)
    print("GOOGLE CALENDAR VERIFICATION")
    print("=" * 80)
    
    print(f"\nConfiguration:")
    print(f"  Calendar ID: {settings.google_calendar_id}")
    print(f"  Credentials: {settings.google_calendar_credentials_path}")
    
    try:
        from google.oauth2.service_account import Credentials
        import googleapiclient.discovery
        from datetime import datetime
        import pytz
        
        # Load credentials
        creds_path = Path(settings.google_calendar_credentials_path)
        if not creds_path.exists():
            print(f"\n✗ ERROR: Credentials file not found at {creds_path}")
            return False
        
        creds = Credentials.from_service_account_file(
            creds_path, scopes=["https://www.googleapis.com/auth/calendar"]
        )
        service = googleapiclient.discovery.build("calendar", "v3", credentials=creds)
        
        # Get service account email
        import json
        with open(creds_path) as f:
            creds_data = json.load(f)
            service_account_email = creds_data.get('client_email')
        
        print(f"\nService Account: {service_account_email}")
        
        # List calendars
        print(f"\nChecking accessible calendars...")
        calendar_list = service.calendarList().list().execute()
        calendars = calendar_list.get('items', [])
        
        if not calendars:
            print(f"✗ No calendars accessible")
            print(f"\nThe calendar sharing did NOT work properly.")
            print(f"Please re-read CALENDAR_SETUP_GUIDE.md and try again.")
            return False
        
        print(f"✓ Found {len(calendars)} accessible calendar(s)")
        
        # Check if our target calendar is in the list
        target_found = False
        for cal in calendars:
            cal_id = cal.get('id')
            cal_summary = cal.get('summary', 'Calendar')
            is_primary = cal.get('primary', False)
            
            status = "(PRIMARY)" if is_primary else ""
            print(f"  - {cal_summary} {status}")
            print(f"    ID: {cal_id}")
            
            if cal_id == settings.google_calendar_id:
                target_found = True
                print(f"    ✓ This is our target calendar!")
        
        if not target_found:
            print(f"\n✗ Target calendar {settings.google_calendar_id} not found")
            print(f"Available calendars don't include your configured calendar.")
            return False
        
        # Try to create a test event
        print(f"\nTesting event creation...")
        from datetime import timedelta
        
        now = datetime.now(pytz.utc)
        start = now + timedelta(hours=2)
        end = start + timedelta(hours=1)
        
        test_event = {
            "summary": "TEST: HiyaDrive Calendar Access",
            "description": "This is a test event created by HiyaDrive to verify calendar access.",
            "start": {
                "dateTime": start.isoformat(),
                "timeZone": "UTC"
            },
            "end": {
                "dateTime": end.isoformat(),
                "timeZone": "UTC"
            }
        }
        
        created = service.events().insert(
            calendarId=settings.google_calendar_id,
            body=test_event
        ).execute()
        
        event_id = created.get('id')
        print(f"✓ Successfully created test event")
        print(f"  Event ID: {event_id}")
        print(f"  Title: {created.get('summary')}")
        
        # Clean up
        service.events().delete(
            calendarId=settings.google_calendar_id,
            eventId=event_id
        ).execute()
        print(f"✓ Cleaned up test event")
        
        print(f"\n{'='*80}")
        print(f"✅ SUCCESS: Calendar is properly configured!")
        print(f"{'='*80}")
        print(f"\nThe HiyaDrive app can now:")
        print(f"  ✓ Check your calendar availability")
        print(f"  ✓ Create restaurant reservation events")
        print(f"\nEvents will be saved to: {settings.google_calendar_id}")
        
        return True
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = verify_calendar_access()
    sys.exit(0 if success else 1)
