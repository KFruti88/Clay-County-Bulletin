import requests
from icalendar import Calendar
from datetime import datetime, date
import pytz

ICS_URL = "https://calendar.google.com/calendar/ical/ceab82d01e29c237da2e761555f2d2c2da76431b94e0def035ff04410e2cd71d%40group.calendar.google.com/public/basic.ics"

def get_town_class(summary, location):
    text = f"{summary} {location}".lower()
    if "flora" in text: return "flora-event"
    if "louisville" in text or "north clay" in text: return "louisville-event"
    if "clay city" in text: return "clay-city-event"
    return "default-event"

def get_upcoming_events(url, limit=5):
    response = requests.get(url)
    gcal = Calendar.from_ical(response.text)
    now = datetime.now(pytz.utc)
    events = []

    for component in gcal.walk('vevent'):
        dtstart = component.get('dtstart').dt
        
        # Handle Date vs Datetime (All Day events are Date)
        if isinstance(dtstart, date) and not isinstance(dtstart, datetime):
            event_start = datetime.combine(dtstart, datetime.min.time()).replace(tzinfo=pytz.utc)
            is_all_day = True
            display_time = "ALL DAY"
        else:
            event_start = dtstart.astimezone(pytz.utc)
            is_all_day = False
            # Format time like "6:00 PM"
            display_time = event_start.strftime("%I:%M %p").lstrip("0")

        # Keep if it's today or in the future
        if event_start.date() >= now.date():
            events.append({
                'start': event_start,
                'display_time': display_time,
                'day': event_start.strftime("%d"),
                'month': event_start.strftime("%b"),
                'summary': str(component.get('summary')),
                'location': str(component.get('location') or 'Clay County'),
                'is_all_day': str(is_all_day).lower(),
                'town_class': get_town_class(str(component.get('summary')), str(component.get('location'))),
                'iso_time': event_start.strftime("%Y-%m-%dT%H:%M:%S")
            })

    events.sort(key=lambda x: x['start'])
    return events[:limit]

def generate_html(events):
    html_output = ""
    for e in events:
        html_output += f"""
        <div class="event-entry {e['town_class']}" data-time="{e['iso_time']}" data-all-day="{e['is_all_day']}">
            <div class="event-date-box">
                <span class="event-day">{e['day']}</span>
                <span class="event-month">{e['month']}</span>
            </div>
            <div class="event-info">
                <span class="event-meta">{e['location']} • {e['display_time']}</span>
                <h4>{e['summary']}</h4>
            </div>
        </div>"""
    return html_output

# To use this in your GitHub Action, you'd have the script read your index.html 
# and replace a placeholder tag with the output of generate_html(upcoming)
upcoming = get_upcoming_events(ICS_URL)
print(generate_html(upcoming))
