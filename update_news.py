import requests
from icalendar import Calendar
from datetime import datetime, date, timedelta
import pytz
import os
import re

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

def fetch_events():
    central = pytz.timezone('America/Chicago')
    today = datetime.now(central).date()
    limit = today + timedelta(days=7)
    all_day, timed = [], []
    seen = set()

    for url in SOURCES:
        try:
            r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
            cal = Calendar.from_ical(r.text)
            for ev in cal.walk('vevent'):
                title = str(ev.get('summary'))
                if title in seen: continue
                start = ev.get('dtstart').dt
                loc = str(ev.get('location') or 'Clay County')
                d = start if isinstance(start, date) else start.astimezone(central).date()

                if today <= d <= limit:
                    is_ad = not isinstance(start, datetime)
                    t_label = "ALL DAY" if is_ad else start.astimezone(central).strftime("%I:%M %p").lstrip("0")
                    iso = (central.localize(datetime.combine(d, datetime.min.time())) if is_ad else start.astimezone(central)).strftime("%Y-%m-%dT%H:%M:%S%z")
                    
                    html = f'<div class="event-entry {get_town_class(title, loc)}" data-time="{iso}" data-all-day="{str(is_ad).lower()}"><div class="event-date-box"><span class="event-day">{d.strftime("%d")}</span><span class="event-month">{d.strftime("%b")}</span></div><div class="event-info"><span class="event-meta">{t_label} • {loc}</span><h4>{title}</h4></div></div>\n'
                    
                    sort_key = start if isinstance(start, datetime) else datetime.combine(start, datetime.min.time()).replace(tzinfo=pytz.utc)
                    (all_day if is_ad else timed).append({'html': html, 'sort': sort_key})
                    seen.add(title)
        except: continue

    all_day.sort(key=lambda x: x['sort'])
    timed.sort(key=lambda x: x['sort'])
    return "".join([e['html'] for e in all_day]), "".join([e['html'] for e in timed])

if __name__ == "__main__":
    ad_html, t_html = fetch_events()
    target = next((os.path.join(r, f) for r, d, fs in os.walk(".") for f in fs if f == "index.html"), "index.html")
    
    if os.path.exists(target):
        with open(target, "r", encoding="utf-8") as f:
            content = f.read()

        # THESE MARKERS MUST MATCH THE HTML COMMENTS BELOW
        if "" in content and "" in content:
            content = re.sub(r".*?", f"\n{ad_html}", content, flags=re.DOTALL)
            content = re.sub(r".*?", f"\n{t_html}", content, flags=re.DOTALL)
            
            with open(target, "w", encoding="utf-8") as f:
                f.write(content)
            print("Successfully updated Bot Zones.")
        else:
            print("Markers missing from index.html. Update aborted to protect manual events.")
