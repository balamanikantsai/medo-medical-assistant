"""Google Calendar — OAuth + medication event creation."""

import datetime
import json
import os
import re

from config import get_config

cfg = get_config()


# ── Time helpers ──────────────────────────────────────────────────────────────

def parse_time_string(time_str: str):
    """Return (hour, minute) or (None, None)."""
    time_str = time_str.upper().strip()

    match_hm_ampm = re.match(r"(\d{1,2}):(\d{2})\s*(AM|PM)", time_str)
    match_h_ampm = re.match(r"(\d{1,2})\s*(AM|PM)", time_str)
    match_hm_24 = re.match(r"(\d{1,2}):(\d{2})", time_str)

    hour, minute = None, 0

    if match_hm_ampm:
        hour, minute = int(match_hm_ampm.group(1)), int(match_hm_ampm.group(2))
        ampm = match_hm_ampm.group(3)
        if ampm == "PM" and hour != 12:
            hour += 12
        elif ampm == "AM" and hour == 12:
            hour = 0
    elif match_h_ampm:
        hour = int(match_h_ampm.group(1))
        ampm = match_h_ampm.group(2)
        if ampm == "PM" and hour != 12:
            hour += 12
        elif ampm == "AM" and hour == 12:
            hour = 0
    elif match_hm_24:
        hour, minute = int(match_hm_24.group(1)), int(match_hm_24.group(2))

    if hour is not None and 0 <= hour <= 23 and 0 <= minute <= 59:
        return hour, minute

    # Fallback: bare hour
    m = re.match(r"(\d{1,2})", time_str)
    if m:
        h = int(m.group(1))
        if 0 <= h <= 23:
            return h, 0
    return None, None


def extract_timing_instructions(timing_str: str):
    """Return (instructions_list, cleaned_timing_string)."""
    lower = timing_str.lower()
    instructions = []
    if re.search(r"before\s+(food|meal|breakfast|lunch|dinner)", lower):
        instructions.append("Take before food")
    if re.search(r"after\s+(food|meal|breakfast|lunch|dinner)", lower):
        instructions.append("Take after food")
    if re.search(r"with\s+(food|meal|breakfast|lunch|dinner)", lower):
        instructions.append("Take with food")

    cleaned = re.sub(
        r"(before|after|with)\s+(food|meal|breakfast|lunch|dinner)",
        "",
        timing_str,
        flags=re.IGNORECASE,
    ).strip()
    return list(set(instructions)), cleaned


# ── OAuth helper ──────────────────────────────────────────────────────────────

def _get_calendar_service():
    """Return an authorized Calendar API service or (None, error_message)."""
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    creds = None
    token_file = cfg.GOOGLE_CALENDAR_TOKEN
    creds_file = cfg.GOOGLE_CALENDAR_CREDENTIALS
    scopes = cfg.GOOGLE_CALENDAR_SCOPES

    if os.path.exists(token_file):
        try:
            creds = Credentials.from_authorized_user_file(token_file, scopes)
        except Exception:
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                with open(token_file, "w") as f:
                    f.write(creds.to_json())
            except Exception as e:
                return None, f"Failed to refresh Calendar token: {e}"
        else:
            if not os.path.exists(creds_file):
                return None, f"OAuth credentials file '{creds_file}' not found."
            try:
                flow = InstalledAppFlow.from_client_secrets_file(creds_file, scopes)
                creds = flow.run_local_server(port=0)
                with open(token_file, "w") as f:
                    f.write(creds.to_json())
            except Exception as e:
                return None, f"Calendar authorization failed: {e}"

    service = build("calendar", "v3", credentials=creds)
    return service, None


# ── Public API ────────────────────────────────────────────────────────────────

def create_calendar_event(parsed_data: dict) -> tuple[bool, str]:
    """Create medication reminders on Google Calendar.

    Returns (success: bool, message: str).
    """
    service, err = _get_calendar_service()
    if err:
        return False, err

    meds = parsed_data.get("medications", [])
    if not meds:
        return False, "No medication details found in the prescription to schedule."

    now_utc = datetime.datetime.now(datetime.timezone.utc)
    tomorrow = datetime.datetime(
        now_utc.year, now_utc.month, now_utc.day, tzinfo=datetime.timezone.utc
    ) + datetime.timedelta(days=1)

    success_count = 0
    errors = []

    KEYWORD_MAP = {
        "breakfast": 8, "morning": 8,
        "lunch": 12, "afternoon": 13,
        "dinner": 18, "evening": 18,
        "night": 20,
    }

    for med in meds:
        name = med.get("name")
        dosage = med.get("dosage", "")
        original_timing = med.get("timing", "daily")
        frequency = med.get("frequency", "")

        if not name:
            continue

        instructions, cleaned = extract_timing_instructions(original_timing)
        lower = cleaned.lower()

        event_times = []
        specific = False

        # 1. Specific clock times
        for tm in re.findall(r"\b(\d{1,2}(?::\d{2})?\s*(?:AM|PM)?)\b", cleaned, re.I):
            h, m = parse_time_string(tm)
            if h is not None:
                event_times.append(tomorrow.replace(hour=h, minute=m, second=0, microsecond=0))
                specific = True

        event_times = sorted(set(event_times))

        # 2. Keyword times
        if not specific:
            for kw, hr in KEYWORD_MAP.items():
                if kw in lower:
                    event_times.append(tomorrow.replace(hour=hr, minute=0, second=0, microsecond=0))
            event_times = sorted(set(event_times))

        # 3. Default fallback
        if not event_times:
            event_times = [tomorrow.replace(hour=8, minute=0, second=0, microsecond=0)]

        for start in event_times:
            end = start + datetime.timedelta(minutes=15)
            summary = f"Take {name}" + (f" ({dosage})" if dosage else "")
            desc_parts = [
                f"Reminder to take {name}",
                f"Dosage: {dosage}" if dosage else None,
                f"Frequency: {frequency}" if frequency else None,
                f"Prescribed Timing: {original_timing}",
                f"Diagnosis: {parsed_data.get('diagnosis', 'N/A')}",
            ]
            if instructions:
                desc_parts.append("Instructions: " + ", ".join(instructions))
            description = "\n".join(filter(None, desc_parts))

            event = {
                "summary": summary,
                "description": description,
                "start": {"dateTime": start.isoformat(), "timeZone": "UTC"},
                "end": {"dateTime": end.isoformat(), "timeZone": "UTC"},
                "reminders": {
                    "useDefault": False,
                    "overrides": [{"method": "popup", "minutes": 10}],
                },
            }

            try:
                service.events().insert(
                    calendarId=cfg.GOOGLE_CALENDAR_ID, body=event
                ).execute()
                success_count += 1
            except Exception as e:
                errors.append(f"{name}: {e}")

    if success_count and not errors:
        return True, f"Successfully added {success_count} medication reminder(s) starting tomorrow."
    if success_count and errors:
        return True, f"Added {success_count} reminder(s), but errors: {'; '.join(errors)}"
    if errors:
        return False, f"Failed to add reminders. Errors: {'; '.join(errors)}"
    return False, "No medication reminders were scheduled."
