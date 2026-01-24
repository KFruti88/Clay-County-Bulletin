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

# Initialize geolocator with a custom user agent
geolocator = Nominatim(user_agent="clay_county_safety_bulletin_v2")

def get_human_location(location_text):
    """Turns coordinates and techy links into readable landmarks or street names."""
    # Pattern to find Latitude/Longitude
    coord_pattern = r'(-?\d+\.\d+),\s*(-?\d+\.\d+)'
    coord_match = re.search(coord_pattern, location_text)
    
    # 1. If coordinates are found, translate them to a street address
    if coord_match:
        lat, lon = coord_match.groups()
        try:
            location = geolocator.reverse(f"{lat}, {lon}", timeout=10)
            if location:
                # We split the address and keep 'Street Name, Town'
                parts = location.address.split(',')
                return f"{parts[0].strip()}, {parts[1].strip()}"
        except Exception as e:
            print(f"Geopy Error: {e}")

    # 2. Strip out any URLs to see if the user typed a description like 'Rail road west side'
    clean_text = re.sub(r'https?://\S+', '', location_text).strip()
    if clean_text:
        return clean_text
        
    return "Map Location"

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
            if not timestamp_str: continue
                
            timestamp = datetime.strptime(timestamp_str, '%m/%d/%Y %H:%M:%S')
            timestamp = central.localize(timestamp)
            
            if timestamp > cutoff:
                # 1. GET DATA
                hazard = row.get('What is the hazard?', 'Public Safety Alert').upper()
                raw_loc = row.get('Where is it exactly?', '')
                town = row.get('Town/City', 'Clay County')
                
                # 2. DUMB DOWN LOCATION (Translation happens here)
                friendly_loc = get_human_location(raw_loc)
                
                # 3. GENERATE MAP LINK
                map_link = "https://www.google.com/maps"
                link_match = re.search(r'(https?://\S+)', raw_loc)
                if link_match:
                    map_link = link_match.group(1)
                elif re.search(r'(-?\d+\.\d+),\s*(-?\d+\.\d+)', raw_loc):
                    coords = re.search(r'(-?\d+\.\d+),\s*(-?\d+\.\d+)', raw_loc).group(0)
                    map_link = f"https://www.google.com/maps/search/?api=1&query={coords}"

                # 4. BUILD THE HTML BLOCK
                alert_html += f'''
                <div class="event-entry" style="border-left: 6px solid #eb1c24; background: #fff5f5; padding: 15px; margin-bottom: 12px; display: block; border-radius: 4px;">
                    <div class="event-info">
                        <h3 style="margin: 0 0 8px 0; color: #eb1c24; font-family: 'Arial Black', sans-serif; font-size: 20px; font-weight: 900; line-height: 1.1; letter-spacing: -0.5px;">
                            ⚠️ {hazard}
                        </h3>
                        <div style="font-size: 16px; font-weight: bold; color: #222; margin-bottom: 6px; font-family: 'Arial', sans-serif;">
                             📍 {friendly_loc} <span style="color: #666; font-weight: normal;">({town})</span>
                        </div>
                        <div style="font-size: 12px; color: #666; margin-top: 10px; border-top: 1px solid #ff000022; padding-top: 8px;">
                            Reported: {timestamp.strftime('%I:%M %p')} 
                            <span style="margin: 0 10px;">•</span>
                            <a href="{map_link}" target="_blank" style="display: inline-block; background: #eb1c24; color: white; padding: 5px 12px; text-decoration: none; border-radius: 4px; font-weight: bold; font-size: 11px; text-transform: uppercase;">
                                View Map
                            </a>
                        </div>
                    </div>
                </div>'''
    except Exception as e:
        print(f"Safety Error: {e}")
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
