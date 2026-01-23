import requests
from icalendar import Calendar
from datetime import datetime, date
import pytz

# The iCal link you provided
ICS_URL = "https://calendar.google.com/calendar/ical/ceab82d01e29c237da2e761555f2d2c2da76431b94e0def035ff04410e2cd71d%40group.calendar.google.com/public/basic.ics"

def get_upcoming_events(url, limit=5):
    response = requests.get(url)
    gcal = Calendar.from_ical(response.text)
    now = datetime.now(pytz.utc)
    events = []

    for component in gcal.walk('vevent'):
        start = component.get('dtstart').dt
        # Handle all-day events (which are 'date' objects, not 'datetime')
        if isinstance(start, date) and not isinstance(start, datetime):
            event_start = datetime.combine(start, datetime.min.time()).replace(tzinfo=pytz.utc)
            is_all_day = True
        else:
            event_start = start.astimezone(pytz.utc)
            is_all_day = False

        if event_start >= now or event_start.date() == now.date():
            events.append({
                'start': event_start,
                'summary': str(component.get('summary')),
                'location': str(component.get('location') or 'Clay County'),
                'is_all_day': is_all_day
            })

    # Sort by date and take the top 5
    events.sort(key=lambda x: x['start'])
    return events[:limit]

# This is where you'd write the logic to inject 'events' into your HTML file
