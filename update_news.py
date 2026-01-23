import requests
from icalendar import Calendar
from datetime import datetime, date, timedelta
import pytz
import re

ICS_URL = "https://calendar.google.com/calendar/ical/ceab82d01e29c237da2e761555f2d2c2da76431b94e0def035ff04410e2cd71d%40group.calendar.google.com/public/basic.ics"

def get_town_class(summary, location):
    text = f"{summary} {location}".lower()
    if "flora" in text: return "flora-theme"
    if "louisville" in text or "north clay" in text: return "louisville-theme"
    if "clay city" in text: return "clay-city-theme"
    return "default-theme"

def fetch_events():
    response = requests.get(ICS_URL)
    gcal = Calendar.from_ical(response.text)
    
    # Accurate timezone for Clay County
    central = pytz.timezone('America/Chicago')
    now = datetime.now(central)
    today = now.date()
    limit_date = today + timedelta(days=5) # 5-Day Outlook
    
    events = []

    for component in gcal.walk('vevent'):
        dtstart = component.get('dtstart').dt
        dtend = component.get('dtend').dt
        
        # Standardize dates for comparison
        start_date = dtstart if isinstance(dtstart, date) else dtstart.astimezone(central).date()
        if dtend:
            end_date = dtend if isinstance(dtend, date) else dtend.astimezone(central).date()
        else:
            end_date = start_date

        # Include if the event overlaps with our 5-day window
        if start_date <= limit_date and end_date >= today:
            is_all_day = not isinstance(dtstart, datetime)
            
            # For multi-day tournaments, show the date it is active (today or start date)
            display_start = max(start_date, today)
            
            if is_all_day:
                display_time = "ALL DAY"
                # Set ISO time to midnight Central for the shading script
                local_dt = central.localize(datetime.combine(display_start, datetime.min.time()))
                iso_time = local_dt.strftime("%Y-%m-%dT%H:%M:%S%z")
            else:
                event_datetime = dtstart.astimezone(central)
                display_time = event_datetime.strftime("%I:%M %p").lstrip("0")
                iso_time = event_datetime.strftime("%Y-%m-%dT%H:%M:%S%z")

            events.append({
                'sort_key': dtstart if isinstance(dtstart, datetime) else datetime.combine(dtstart, datetime.min.time()).replace(tzinfo=pytz.utc),
                'display_time': display_time,
                'day': display_start.strftime("%d"),
                'month': display_start.strftime("%b"),
                'summary': str(component.get('summary')),
                'location': str(component.get('location') or 'Clay County'),
                'is_all_day': str(is_all_day).lower(),
                'town_class': get_town_class(str(component.get('summary')), str(component.get('location'))),
                'iso_time': iso_time
            })

    # Sort by time and take top 5
    events.sort(key=lambda x: x['sort_key'])
    
    html_output = ""
    for e in events[:5]:
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

if __name__ == "__main__":
    new_html = fetch_events()
    
    with open("index.html", "r", encoding="utf-8") as f:
        content = f.read()
    
    # FIXED REGEX: Specifically looks for your comment tags
    pattern = r".*?"
    replacement = f"{new_html}"
    
    updated_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(updated_content)
    
    print("Bulletin successfully updated with 5-day outlook.")
