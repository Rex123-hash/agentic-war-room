import os
import re
from datetime import datetime, timedelta, timezone

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CREDENTIALS_PATH = os.path.join(BASE_DIR, "credentials.json")
TOKEN_PATH = os.path.join(BASE_DIR, "token.json")

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def get_calendar_service():
    creds = None

    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_PATH, "w") as token_file:
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
    service = get_calendar_service()

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
        title="War-Room Test Event",
        attendees="amaank2405@gmail.com, invalid person, Bob Johnson",
        duration_minutes=15,
        description="Testing Project War-Room calendar integration",
    )
    print(result)