from __future__ import print_function
import datetime
import os.path
import json
import re  # Import regular expressions


from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar']
CREDENTIALS_FILE = 'tempCredentials.json'  # Ensure this file exists
TOKEN_FILE = 'token.json'
CALENDAR_ID = 'primary'

def parse_time_string(time_str):
    """Parses a time string (e.g., '9:00 AM', '14:30') and returns (hour, minute)."""
    time_str = time_str.upper().strip()
    match_hm_ampm = re.match(r'(\d{1,2}):(\d{2})\s*(AM|PM)', time_str)
    match_h_ampm = re.match(r'(\d{1,2})\s*(AM|PM)', time_str)
    match_hm_24 = re.match(r'(\d{1,2}):(\d{2})', time_str)

    hour, minute = None, 0  # Default minute to 0

    if match_hm_ampm:
        hour = int(match_hm_ampm.group(1))
        minute = int(match_hm_ampm.group(2))
        ampm = match_hm_ampm.group(3)
        if ampm == 'PM' and hour != 12:
            hour += 12
        elif ampm == 'AM' and hour == 12:  # Midnight case
            hour = 0
    elif match_h_ampm:
        hour = int(match_h_ampm.group(1))
        ampm = match_h_ampm.group(2)
        if ampm == 'PM' and hour != 12:
            hour += 12
        elif ampm == 'AM' and hour == 12:  # Midnight case
            hour = 0
    elif match_hm_24:
        hour = int(match_hm_24.group(1))
        minute = int(match_hm_24.group(2))

    # Validate hour
    if hour is not None and 0 <= hour <= 23 and 0 <= minute <= 59:
        return hour, minute
    else:
        # Try parsing just hour if previous failed
        match_h_24 = re.match(r'(\d{1,2})', time_str)
        if match_h_24:
            hour = int(match_h_24.group(1))
            if 0 <= hour <= 23:
                return hour, 0  # Default minute to 0
        return None, None  # Indicate failure


def extract_timing_instructions(timing_str):
    """Extracts instructions like 'before food', 'after food'."""
    timing_str_lower = timing_str.lower()
    instructions = []
    if re.search(r'before\s+(food|meal|breakfast|lunch|dinner)', timing_str_lower):
        instructions.append("Take before food")
    if re.search(r'after\s+(food|meal|breakfast|lunch|dinner)', timing_str_lower):
        instructions.append("Take after food")
    if re.search(r'with\s+(food|meal|breakfast|lunch|dinner)', timing_str_lower):
        instructions.append("Take with food")
    # Add more specific instructions if needed

    # Remove extracted instructions from the original string for cleaner time parsing
    cleaned_timing_str = re.sub(r'(before|after|with)\s+(food|meal|breakfast|lunch|dinner)', '', timing_str, flags=re.IGNORECASE).strip()

    return list(set(instructions)), cleaned_timing_str  # Return unique instructions and cleaned string


def create_calendar_event(parsed_data):
    """Handles OAuth authentication and adds medication events from parsed_data."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except Exception as e:
            print(f"Error loading {TOKEN_FILE}: {e}. Will attempt new auth flow.")
            creds = None

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing expired credentials...")
            try:
                creds.refresh(Request())
                # Save the refreshed credentials
                with open(TOKEN_FILE, 'w') as token:
                    token.write(creds.to_json())
                print("Credentials refreshed and saved.")
            except Exception as refresh_err:
                print(f"Error refreshing credentials: {refresh_err}")
                # Indicate failure requiring manual intervention
                return False, f"Failed to refresh Google Calendar token. Please run 'python {os.path.basename(__file__)}' manually to re-authorize."
        else:
            # Run the interactive flow if no valid/refreshable token
            if not os.path.exists(CREDENTIALS_FILE):
                return False, f"OAuth credentials file '{CREDENTIALS_FILE}' not found. Cannot authorize."
            try:
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                print("\nStarting Google Calendar authorization flow...")
                creds = flow.run_local_server(port=0)
                print("Authorization successful.")
                # Save the credentials for the next run
                with open(TOKEN_FILE, 'w') as token:
                    token.write(creds.to_json())
                print(f"Credentials saved to {TOKEN_FILE}")
            except Exception as flow_err:
                print(f"Error during authorization flow: {flow_err}")
                return False, f"Google Calendar authorization failed: {flow_err}"

    # If we reach here, creds should be valid
    try:
        service = build('calendar', 'v3', credentials=creds)
        print("✅ Google Calendar Service Initialized.")

        # --- Start: Event creation logic based on parsed_data ---
        if not parsed_data or 'medications' not in parsed_data or not parsed_data['medications']:
            print("⚠️ No valid medication data provided.")
            return False, "No medication details found in the prescription to schedule."

        success_count = 0
        errors = []

        now_utc = datetime.datetime.now(datetime.timezone.utc)
        start_of_tomorrow_utc = datetime.datetime(now_utc.year, now_utc.month, now_utc.day, tzinfo=datetime.timezone.utc) + datetime.timedelta(days=1)

        for med in parsed_data.get('medications', []):
            med_name = med.get('name')
            dosage = med.get('dosage', '')
            original_timing_str = med.get('timing', 'daily')  # Keep original for description
            frequency = med.get('frequency', '')

            if not med_name:
                print("⚠️ Skipping medication with missing name.")
                continue

            # Extract instructions and clean the timing string
            instructions, timing_str_cleaned = extract_timing_instructions(original_timing_str)
            timing_str_lower = timing_str_cleaned.lower()

            event_times_utc = []
            scheduled_specific_time = False

            # 1. Check for specific times first (e.g., "9:00 AM", "14:30", "8pm")
            # Use regex to find all potential time mentions
            potential_times = re.findall(r'\b(\d{1,2}(?::\d{2})?\s*(?:AM|PM)?)\b', timing_str_cleaned, re.IGNORECASE)
            for time_mention in potential_times:
                hour, minute = parse_time_string(time_mention)
                if hour is not None:
                    event_time = start_of_tomorrow_utc.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    event_times_utc.append(event_time)
                    scheduled_specific_time = True

            # Remove duplicates if multiple regex matches point to the same time
            event_times_utc = sorted(list(set(event_times_utc)))

            # 2. If no specific times found, check for keywords
            if not scheduled_specific_time:
                keyword_mapping = {
                    "breakfast": 8,
                    "morning": 8,
                    "lunch": 12,
                    "afternoon": 13,
                    "dinner": 18,
                    "evening": 18,  # Map evening to dinner time
                    "night": 20
                }
                scheduled_keyword = False
                for keyword, hour in keyword_mapping.items():
                    if keyword in timing_str_lower:
                        event_time = start_of_tomorrow_utc.replace(hour=hour, minute=0, second=0, microsecond=0)
                        event_times_utc.append(event_time)
                        scheduled_keyword = True

                # Remove duplicates and sort
                event_times_utc = sorted(list(set(event_times_utc)))

                # 3. If still no times, default to daily morning
                if not scheduled_keyword:
                    event_times_utc.append(start_of_tomorrow_utc.replace(hour=8, minute=0, second=0, microsecond=0))

            # --- Create events for calculated times ---
            for event_start_time in event_times_utc:
                event_end_time = event_start_time + datetime.timedelta(minutes=15)

                event_summary = f"Take {med_name}" + (f" ({dosage})" if dosage else "")

                # Build description including original timing and instructions
                event_description_parts = [
                    f"Reminder to take {med_name}",
                    f"Dosage: {dosage}" if dosage else None,
                    f"Frequency: {frequency}" if frequency else None,
                    f"Prescribed Timing: {original_timing_str}",  # Show original instruction
                    f"Diagnosis: {parsed_data.get('diagnosis', 'N/A')}"
                ]
                # Add extracted instructions
                if instructions:
                    event_description_parts.append("Instructions: " + ", ".join(instructions))

                event_description = "\n".join(filter(None, event_description_parts))

                event = {
                    'summary': event_summary,
                    'description': event_description,
                    'start': {'dateTime': event_start_time.isoformat(), 'timeZone': 'UTC'},
                    'end': {'dateTime': event_end_time.isoformat(), 'timeZone': 'UTC'},
                    'reminders': {
                        'useDefault': False,
                        'overrides': [{'method': 'popup', 'minutes': 10}],
                    },
                }

                # Insert the event
                try:
                    created_event = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
                    print(f'✅ Event created for {med_name} at {event_start_time.strftime("%Y-%m-%d %H:%M:%S %Z")}: {created_event.get("htmlLink")}')
                    success_count += 1
                except HttpError as error:
                    error_content = "Unknown Google API Error"
                    try:
                        error_details = json.loads(error.content.decode('utf-8'))
                        error_content = error_details.get('error', {}).get('message', error.content.decode('utf-8'))
                    except:
                        pass
                    error_msg = f'Failed to create event for {med_name}: {error_content}'
                    print(f"⚠️ {error_msg}")
                    errors.append(f"{med_name}: {error_content}")
                except Exception as e:
                    error_msg = f'Unexpected error creating event for {med_name}: {e}'
                    print(f"⚠️ {error_msg}")
                    errors.append(f"{med_name}: {str(e)}")
        # --- End: Event creation logic ---

        # Construct final status message
        if success_count > 0 and not errors:
            return True, f"Successfully added {success_count} medication reminder(s) to your calendar starting tomorrow."
        elif success_count > 0 and errors:
            return True, f"Added {success_count} reminder(s), but encountered errors with others: {'; '.join(errors)}"
        elif not success_count and errors:
            return False, f"Failed to add any reminders. Errors: {'; '.join(errors)}"
        else:
            return False, "No medication reminders were scheduled (input might be empty or invalid)."

    except HttpError as error:
        print(f'An API error occurred: {error}')
        return False, f"Google Calendar API error: {error}"
    except Exception as e:
        print(f'An unexpected error occurred: {e}')
        return False, f"An unexpected error occurred: {e}"


if __name__ == '__main__':
    print("Running Google Calendar Auth Check / Event Creation Test...")
    test_data = {
        "diagnosis": "Manual Test Complex Timing",
        "medications": [
            {"name": "TestPill AM", "dosage": "1", "timing": "morning before breakfast"},
            {"name": "TestPill PM", "dosage": "1", "timing": "8:00 PM after food"},
            {"name": "TestLiquid", "dosage": "5ml", "timing": "lunch and dinner"},
            {"name": "TestCream", "dosage": "Apply", "timing": "9am and 9pm"},
            {"name": "TestDefault", "dosage": "1", "timing": "daily"}  # Should default to 8 AM
        ]
    }
    print(f"Attempting to add events for test data: {json.dumps(test_data, indent=2)}")
    success, message = create_calendar_event(test_data)

    print("\n--- Result ---")
    print(f"Success: {success}")
    print(f"Message: {message}")
    if not success and "authorize" in message.lower():
        print("\nACTION REQUIRED: Please ensure 'tempCredentials.json' is present and re-run this script.")
    elif not success:
        print("\nCheck logs above for specific errors.")
        