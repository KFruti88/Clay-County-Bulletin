import requests
import csv
from icalendar import Calendar
from datetime import datetime, date, timedelta
import pytz
import io
import re
from geopy.geocoders import Nominatim

# 1. SOURCES
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRaeffFYYrzXJ9JXdmkynl5JbkvWZJusl812_NZuX63o6DynnJwC8G3AxiZLfoh5QGyr2Kys2mVioN7/pub?gid=670653122&single=true&output=csv"
CALENDAR_SOURCES = [
    "https://calendar.google.com/calendar/ical/ceab82d01e29c237da2e761555f2d2c2da76431b94e0def035ff04410e2cd71d%40group.calendar.google.com/public/basic.ics",
    "https://www.facebook.com/events/ical/upcoming/?uid=100063547844172&key=rjmOs5JdN9NQhByz"
]

# Initialize geolocator
geolocator = Nominatim(user_agent="clay_county_bulletin")

def get_real_address(location_text):
    """Converts coordinates to street addresses, or returns original text."""
    # Pattern to find Lat/Long numbers
    coord_pattern = r'(-?\d+\.\d+),\s*(-?\d+\.\d+)'
    match = re.search(coord_pattern, location_text)
    
    if match:
        lat, lon = match.groups()
        try:
            location = geolocator.reverse(f"{lat}, {lon}", timeout=10)
            if location:
                # Clean up the address string to just "Street, Town"
                parts = location.address.split(',')
                return f"{parts[0].strip()}, {parts[1].strip()}"
        except:
            pass # Fall through to return original text
            
    return location_text

def fetch_safety_alerts():
    central = pytz.timezone('America/Chicago')
    now = datetime.now(central)
    cutoff = now - timedelta(hours=24)
    alert_html = ""
    
    try:
        r = requests.get(SHEET_CSV_URL)
        f = io.StringIO(r.text)
        reader = csv.DictReader(f)
        for row in reader:
            timestamp_str = row.get('Timestamp', '')
            if not timestamp_str:
                continue
                
            timestamp = datetime.strptime(timestamp_str, '%m/%d/%Y %H:%M:%S')
            timestamp = central.localize(timestamp)
            
            if timestamp > cutoff:
                # RUN THE ADDRESS FINDER HERE
                raw_loc = row.get('Where is it exactly?', 'Location TBD')
                display_location = get_real_address(raw_loc)

                alert_html += f'''
                <div class="event-entry" style="border-left: 5px solid #eb1c24; background: #fff5f5; padding: 10px; margin-bottom: 10px;">
                    <div class="event-info">
                        <span class="event-meta" style="color: #eb1c24; font-weight: bold;">
                            ⚠️ {row.get('What is the hazard?', 'Hazard')} • {row.get('Town/City', 'Clay County')}
                        </span>
                        <h4 style="margin: 5px 0;">{display_location}</h4>
                        <div class="event-description">Reported: {timestamp.strftime('%I:%M %p')}</div>
                    </div>
                </div>'''
    except Exception as e:
        print(f"Safety Sheet Error: {e}")
    return alert_html

def fetch_calendar_events():
    central = pytz.timezone('America/Chicago')
    today = datetime.now(central).date()
    limit = today + timedelta(days=7)
    all_day, timed = [], []
    seen = set()

    for url in CALENDAR_SOURCES:
        try:
            r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
            cal = Calendar.from_ical(r.text)
            for ev in cal.walk('vevent'):
                title = str(ev.get('summary'))
                if title in seen: continue
                
                start = ev.get('dtstart').dt
                loc = str(ev.get('location') or 'Clay County')
                desc = str(ev.get('description') or '').replace('\\n', '<br>')
                d = start if isinstance(start, date) else start.astimezone(central).date()

                if today <= d <= limit:
                    is_ad = not isinstance(start, datetime)
                    t_label = "ALL DAY" if is_ad else start.astimezone(central).strftime("%I:%M %p").lstrip("0")
                    
                    html = f'''
                    <div class="event-entry">
                        <div class="event-date-box">
                            <span class="event-day">{d.strftime("%d")}</span>
                            <span class="event-month">{d.strftime("%b")}</span>
                        </div>
                        <div class="event-info">
                            <span class="event-meta">{t_label} • <span class="loc-text">{loc}</span></span>
                            <h4>{title}</h4>
                            <div class="event-description">{desc}</div>
                        </div>
                    </div>'''
                    
                    sort_key = start if isinstance(start, datetime) else datetime.combine(start, datetime.min.time()).replace(tzinfo=pytz.utc)
                    (all_day if is_ad else timed).append({'html': html, 'sort': sort_key})
                    seen.add(title)
        except: continue
    
    all_day.sort(key=lambda x: x['sort'])
    timed.sort(key=lambda x: x['sort'])
    return "".join([e['html'] for e in all_day]), "".join([e['html'] for e in timed])

if __name__ == "__main__":
    safety = fetch_safety_alerts()
    ad, t = fetch_calendar_events()
    
    with open("feed.html", "w", encoding="utf-8") as f:
        f.write(f'<div id="bot-safety-data">{safety}</div>')
        f.write(f'<div id="bot-ad-data">{ad}</div>')
        f.write(f'<div id="bot-t-data">{t}</div>')
