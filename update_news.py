import requests
import csv
from icalendar import Calendar
from datetime import datetime, date, timedelta
import pytz
import io
import re
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

# 1. SOURCES
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRaeffFYYrzXJ9JXdmkynl5JbkvWZJusl812_NZuX63o6DynnJwC8G3AxiZLfoh5QGyr2Kys2mVioN7/pub?gid=670653122&single=true&output=csv"
CALENDAR_SOURCES = [
    "https://calendar.google.com/calendar/ical/ceab82d01e29c237da2e761555f2d2c2da76431b94e0def035ff04410e2cd71d%40group.calendar.google.com/public/basic.ics",
    "https://www.facebook.com/events/ical/upcoming/?uid=100063547844172&key=rjmOs5JdN9NQhByz"
]

# We use a more unique name here to prevent being blocked
geolocator = Nominatim(user_agent="ClayCountySafetyBulletin_KFruti88_Robot")

def get_human_location(location_text):
    """Translates coordinates into 'People Talk' with extra safety."""
    coord_pattern = r'(-?\d+\.\d+),\s*(-?\d+\.\d+)'
    coord_match = re.search(coord_pattern, location_text)
    
    if coord_match:
        lat, lon = coord_match.groups()
        # We try up to 3 times in case the map service is busy
        for attempt in range(3):
            try:
                location = geolocator.reverse(f"{lat}, {lon}", timeout=10)
                if location:
                    parts = location.address.split(',')
                    return f"{parts[0].strip()}, {parts[1].strip()}"
                break
            except (GeocoderTimedOut, GeocoderServiceError):
                continue # Try again
            except:
                break
                
    # If translation fails or it's a landmark, return the original text minus URLs
    return re.sub(r'https?://\S+', '', location_text).strip() or "Location Pin"

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
                hazard = row.get('What is the hazard?', 'Public Safety Alert').upper()
                raw_loc = row.get('Where is it exactly?', '')
                town = row.get('Town/City', 'Clay County')
                
                friendly_loc = get_human_location(raw_loc)
                
                # Setup the map link
                map_link = "https://www.google.com/maps"
                link_match = re.search(r'(https?://\S+)', raw_loc)
                if link_match:
                    map_link = link_match.group(1)
                elif re.search(r'(-?\d+\.\d+),\s*(-?\d+\.\d+)', raw_loc):
                    coords = re.search(r'(-?\d+\.\d+),\s*(-?\d+\.\d+)', raw_loc).group(0)
                    map_link = f"https://www.google.com/maps/search/?api=1&query={coords}"

                alert_html += f'''
                <div class="event-entry" style="border-left: 6px solid #eb1c24; background: #fff5f5; padding: 15px; margin-bottom: 12px; display: block; border-radius: 4px;">
                    <div class="event-info">
                        <h3 style="margin: 0 0 8px 0; color: #eb1c24; font-family: 'Arial Black', sans-serif; font-size: 20px; font-weight: 900; line-height: 1.1;">
                            ⚠️ {hazard}
                        </h3>
                        <div style="font-size: 16px; font-weight: bold; color: #222; margin-bottom: 6px;">
                             📍 {friendly_loc} <span style="color: #666; font-weight: normal;">({town})</span>
                        </div>
                        <div style="font-size: 12px; color: #666; margin-top: 10px; border-top: 1px solid #ff000022; padding-top: 8px;">
                            Reported: {timestamp.strftime('%I:%M %p')} 
                            <span style="margin: 0 10px;">•</span>
                            <a href="{map_link}" target="_blank" style="display: inline-block; background: #eb1c24; color: white; padding: 5px 12px; text-decoration: none; border-radius: 4px; font-weight: bold; font-size: 11px;">
                                VIEW ON MAP
                            </a>
                        </div>
                    </div>
                </div>'''
    except Exception as e:
        print(f"Safety Error: {e}")
    return alert_html

# ... (Keep the rest of your calendar code)
