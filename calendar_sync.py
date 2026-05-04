"""Google Calendar integration — reads events from the Marina Club Events calendar."""

from datetime import datetime, timezone
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']


def get_calendar_service(credentials_file):
    credentials = service_account.Credentials.from_service_account_file(
        credentials_file, scopes=SCOPES)
    return build('calendar', 'v3', credentials=credentials)


def fetch_upcoming_events(credentials_file, calendar_id):
    """Fetch upcoming events from Google Calendar.

    Returns a list of dicts with keys:
        gcal_event_id, title, start_time, end_time, location, description
    """
    service = get_calendar_service(credentials_file)
    now = datetime.now(timezone.utc).isoformat()

    result = service.events().list(
        calendarId=calendar_id,
        timeMin=now,
        maxResults=50,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = []
    for item in result.get('items', []):
        start = item['start'].get('dateTime', item['start'].get('date'))
        end = item['end'].get('dateTime', item['end'].get('date'))

        start_dt = _parse_datetime(start)
        end_dt = _parse_datetime(end)

        events.append({
            'gcal_event_id': item['id'],
            'title': item.get('summary', 'Untitled Event'),
            'start_time': start_dt,
            'end_time': end_dt,
            'location': item.get('location', ''),
            'description': item.get('description', ''),
        })

    return events


def _parse_datetime(dt_string):
    """Parse Google Calendar datetime string to Python datetime."""
    for fmt in ('%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%dT%H:%M:%S.%f%z', '%Y-%m-%d'):
        try:
            return datetime.strptime(dt_string, fmt)
        except ValueError:
            continue
    return datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
