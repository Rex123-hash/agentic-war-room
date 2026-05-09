import os
import re
import json
from datetime import datetime, timedelta, timezone

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CREDENTIALS_PATH = os.path.join(BASE_DIR, "credentials.json")
TOKEN_PATH = os.path.join(BASE_DIR, "token.json")
CALENDAR_CREDENTIALS_ENV = "GOOGLE_CALENDAR_CREDENTIALS_JSON"
CALENDAR_TOKEN_ENV = "GOOGLE_CALENDAR_TOKEN_JSON"

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _load_json_from_env_or_file(env_name: str, path: str) -> dict | None:
    raw_value = os.getenv(env_name)
    if raw_value:
        return json.loads(raw_value)

    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as json_file:
            return json.load(json_file)

    return None


def get_calendar_service():
    credentials_info = _load_json_from_env_or_file(CALENDAR_CREDENTIALS_ENV, CREDENTIALS_PATH)
    token_info = _load_json_from_env_or_file(CALENDAR_TOKEN_ENV, TOKEN_PATH)

    if not credentials_info:
        raise FileNotFoundError(
            "Missing Google Calendar OAuth credentials. Configure "
            f"{CALENDAR_CREDENTIALS_ENV} or provide {CREDENTIALS_PATH} locally."
        )

    creds = None

    if token_info:
        creds = Credentials.from_authorized_user_info(token_info, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if os.getenv("K_SERVICE"):
                raise RuntimeError(
                    "Google Calendar OAuth token is missing or invalid in Cloud Run. "
                    f"Configure {CALENDAR_TOKEN_ENV} with a valid authorized-user token."
                )

            flow = InstalledAppFlow.from_client_config(credentials_info, SCOPES)
            creds = flow.run_local_server(port=0)

        if not os.getenv(CALENDAR_TOKEN_ENV):
            with open(TOKEN_PATH, "w", encoding="utf-8") as token_file:
                token_file.write(creds.to_json())

    return build("calendar", "v3", credentials=creds)


def _extract_valid_attendees(attendees: str) -> list[dict]:
    attendee_list = []

    for raw_value in attendees.split(","):
        value = raw_value.strip()
        if value and EMAIL_PATTERN.match(value):
            attendee_list.append({"email": value})

    return attendee_list


def create_calendar_event(
    title: str,
    attendees: str,
    duration_minutes: int,
    description: str,
) -> dict:
    try:
        service = get_calendar_service()
    except FileNotFoundError as exc:
        return {
            "status": "skipped",
            "reason": str(exc),
            "title": title,
            "valid_attendees_count": 0,
        }
    except Exception as exc:
        return {
            "status": "skipped",
            "reason": f"Calendar integration unavailable: {exc}",
            "title": title,
            "valid_attendees_count": 0,
        }

    start_time = datetime.now(timezone.utc) + timedelta(minutes=10)
    end_time = start_time + timedelta(minutes=duration_minutes)

    attendee_list = _extract_valid_attendees(attendees)

    event = {
        "summary": title,
        "description": description,
        "start": {
            "dateTime": start_time.isoformat(),
            "timeZone": "UTC",
        },
        "end": {
            "dateTime": end_time.isoformat(),
            "timeZone": "UTC",
        },
    }

    if attendee_list:
        event["attendees"] = attendee_list

    created_event = service.events().insert(calendarId="primary", body=event).execute()

    return {
        "status": "success",
        "event_id": created_event.get("id"),
        "event_link": created_event.get("htmlLink"),
        "title": title,
        "valid_attendees_count": len(attendee_list),
    }


if __name__ == "__main__":
    result = create_calendar_event(
        title="Stratify Test Event",
        attendees="amaank2405@gmail.com, invalid person, Bob Johnson",
        duration_minutes=15,
        description="Testing Stratify calendar integration",
    )
    print(result)
