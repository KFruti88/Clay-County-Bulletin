import requests
from icalendar import Calendar
from datetime import datetime, date, timedelta
import pytz
import re
import os

# BOTH CALENDAR SOURCES
SOURCES = [
    "https://calendar.google.com/calendar/ical/ceab82d01e29c237da2e761555f2d2c2da76431b94e0def035ff04410e2cd71d%40group.calendar.google.com/public/basic.ics",
    "https://www.facebook.com/events/ical/upcoming/?uid=100063547844172&key=rjmOs5JdN9NQhByz"
]

def get_town_class(summary, location):
    text = f"{summary} {location}".lower()
    if "flora" in text: return "flora-theme"
    if "louisville" in text or "north clay" in text: return "louisville-theme"
    if "clay city" in text: return "clay-city-theme"
    return "default-theme"

def fetch_all_events():
    central = pytz.timezone('America/Chicago')
    now = datetime.now(central)
    today = now.date()
    limit_date = today + timedelta(days=7) # Looking a full week ahead now
    
    collected = []
    seen_titles = set() # Prevents duplicate events if they are on both calendars

    for url in SOURCES:
        try:
            # Facebook URLs sometimes need a User-Agent to not block the request
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
            gcal = Calendar.from_ical(response.text)
            
            for component in gcal.walk('vevent'):
                summary = str(component.get('summary'))
                if summary in seen_titles: continue
                
                dtstart = component.get('dtstart').dt
                dtend = component.get('dtend').dt
                location = str(component.get('location') or 'Clay County')
                desc = str(component.get('description') or '')

                # Standardize dates
                start_date = dtstart if isinstance(dtstart, date) else dtstart.astimezone(central).date()
                end_date = dtend if isinstance(dtend, date) else (dtend.astimezone(central).date() if dtend else start_date)

                if start_date <= limit_date and end_date >= today:
                    is_all_day = not isinstance(dtstart, datetime)
                    display_start = max(start_date, today)
                    
                    if is_all_day:
                        time_label = "ALL DAY"
                        iso_time = central.localize(datetime.combine(display_start, datetime.min.time())).strftime("%Y-%m-%dT%H:%M:%S%z")
                    else:
                        event_dt = dtstart.astimezone(central)
                        time_label = event_dt.strftime("%I:%M %p").lstrip("0")
                        iso_time = event_dt.strftime("%Y-%m-%dT%H:%M:%S%z")

                    desc_html = f'<div class="event-description">{desc}</div>' if desc else ""
                    
                    html = f"""
                    <div class="event-entry {get_town_class(summary, location)}" data-time="{iso_time}" data-all-day="{str(is_all_day).lower()}">
                        <div class="event-date-box">
                            <span class="event-day">{display_start.strftime("%d")}</span>
                            <span class="event-month">{display_start.strftime("%b")}</span>
                        </div>
                        <div class="event-info">
                            <span class="event-meta">{time_label} • {location}</span>
                            <h4>{summary}</h4>
                            {desc_html}
                        </div>
                    </div>"""
                    
                    sort_val = dtstart if isinstance(dtstart, datetime) else datetime.combine(dtstart, datetime.min.time()).replace(tzinfo=pytz.utc)
                    collected.append({'is_all_day': is_all_day, 'html': html, 'sort': sort_val})
                    seen_titles.add(summary)
        except Exception as e:
            print(f"Error skipping a source: {e}")

    # Sort everything by date
    collected.sort(key=lambda x: x['sort'])
    
    ad_html = "".join([e['html'] for e in collected if e['is_all_day']])
    t_html = "".join([e['html'] for e in collected if not e['is_all_day']])
    
    return ad_html, t_html

if __name__ == "__main__":
    ad_html, t_html = fetch_all_events()
    
    # Use the path-blind finder to locate index.html
    target_file = next((os.path.join(r, f) for r, d, fs in os.walk(".") for f in fs if f == "index.html"), None)

    if target_file:
        with open(target_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        content = re.sub(r".*?", f"{ad_html}", content, flags=re.DOTALL)
        content = re.sub(r".*?", f"{t_html}", content, flags=re.DOTALL)
        
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Updated {target_file} with Google and Facebook events.")
