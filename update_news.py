import requests
from icalendar import Calendar
from datetime import datetime, date, timedelta
import pytz
import re

# Your Calendar URL
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
    
    # Set to local Central Time
    central = pytz.timezone('America/Chicago')
    now = datetime.now(central)
    today = now.date()
    limit_date = today + timedelta(days=5) # 5-Day Outlook
    
    all_day_html = ""
    timed_html = ""
    collected_events = []

    for component in gcal.walk('vevent'):
        dtstart = component.get('dtstart').dt
        dtend = component.get('dtend').dt
        
        # Standardize dates for comparison
        start_date = dtstart if isinstance(dtstart, date) else dtstart.astimezone(central).date()
        if dtend:
            end_date = dtend if isinstance(dtend, date) else dtend.astimezone(central).date()
        else:
            end_date = start_date

        # Check for overlap with the 5-day window
        if start_date <= limit_date and end_date >= today:
            is_all_day = not isinstance(dtstart, datetime)
            display_start = max(start_date, today)
            
            if is_all_day:
                display_time = "ALL DAY"
                # Localize to midnight for shading logic
                local_dt = central.localize(datetime.combine(display_start, datetime.min.time()))
                iso_time = local_dt.strftime("%Y-%m-%dT%H:%M:%S%z")
            else:
                event_datetime = dtstart.astimezone(central)
                display_time = event_datetime.strftime("%I:%M %p").lstrip("0")
                iso_time = event_datetime.strftime("%Y-%m-%dT%H:%M:%S%z")

            html = f"""
            <div class="event-entry {get_town_class(str(component.get('summary')), str(component.get('location')))}" data-time="{iso_time}" data-all-day="{str(is_all_day).lower()}">
                <div class="event-date-box">
                    <span class="event-day">{display_start.strftime("%d")}</span>
                    <span class="event-month">{display_start.strftime("%b")}</span>
                </div>
                <div class="event-info">
                    <span class="event-meta">{str(component.get('location') or 'Clay County')} • {display_time}</span>
                    <h4>{str(component.get('summary'))}</h4>
                </div>
            </div>"""
            
            sort_val = dtstart if isinstance(dtstart, datetime) else datetime.combine(dtstart, datetime.min.time()).replace(tzinfo=pytz.utc)
            collected_events.append({'is_all_day': is_all_day, 'html': html, 'sort': sort_val})

    # Sort everything chronologically
    collected_events.sort(key=lambda x: x['sort'])
    
    for e in collected_events:
        if e['is_all_day']: all_day_html += e['html']
        else: timed_html += e['html']
        
    return all_day_html, timed_html

if __name__ == "__main__":
    ad_html, t_html = fetch_events()
    
    with open("index.html", "r", encoding="utf-8") as f:
        content = f.read()
    
    # FIXED REGEX: These patterns now find the exact comment tags in your HTML
    content = re.sub(r".*?", 
                     f"{ad_html}", 
                     content, flags=re.DOTALL)
                     
    content = re.sub(r".*?", 
                     f"{t_html}", 
                     content, flags=re.DOTALL)
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(content)
        
    print("Success: index.html updated with All-Day and Timed events.")
