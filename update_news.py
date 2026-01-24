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
geolocator = Nominatim(user_agent="clay_county_safety_bulletin")

def get_human_location(location_text):
    """Turns technical data into 'Landmarks' and 'Street Names'."""
    # Pattern for coordinates
    coord_pattern = r'(-?\d+\.\d+),\s*(-?\d+\.\d+)'
    coord_match = re.search(coord_pattern, location_text)
    
    # 1. If it's coordinates, get the street name
    if coord_match:
        lat, lon = coord_match.groups()
        try:
            location = geolocator.reverse(f"{lat}, {lon}", timeout=10)
            if location:
                address_parts = location.address.split(',')
                # Return 'Street Name, Town'
                return f"{address_parts[0].strip()}, {address_parts[1].strip()}"
        except:
            pass

    # 2. If it's a URL, strip it out to see if there's regular text
    clean_text = re.sub(r'https?://\S+', '', location_text).strip()
    if clean_text:
        return clean_text
        
    return "Location Pin"

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
                
                # Get the "Dumbed Down" location name
                friendly_loc = get_human_location(raw_loc)
                
                # Find any map link to attach to the icon
                map_link = "https://www.google.com/maps"
                link_match = re.search(r'(https?://\S+)', raw_loc)
                if link_match:
                    map_link = link_match.group(1)
                elif re.search(r'(-?\d+\.\d+),\s*(-?\d+\.\d+)', raw_loc):
                    coords = re.search(r'(-?\d+\.\d+),\s*(-?\d+\.\d+)', raw_loc).group(0)
                    map_link = f"https://www.google.com/maps/search/?api=1&query={coords}"

                alert_html += f'''
                <div class="event-entry" style="border-left: 5px solid #eb1c24; background: #fff5f5; padding: 12px; margin-bottom: 10px; display: block;">
                    <div class="event-info">
                        <h3 style="margin: 0 0 5px 0; color: #eb1c24; font-family: 'Arial', sans-serif; font-size: 18px; font-weight: 900; line-height: 1.2;">
                            ⚠️ {hazard}
                        </h3>
                        <div style="font-size: 14px; font-weight: bold; color: #333; margin-bottom: 4px;">
                             📍 {friendly_loc} ({town})
                        </div>
                        <div class="event-meta" style="font-size: 11px; color: #666;">
                            Reported: {timestamp.strftime('%I:%M %p')} • <a href="{map_link}" target="_blank" style="color: #eb1c24; font-weight: bold;">VIEW ON MAP</a>
                        </div>
                    </div>
                </div>'''
    except Exception as e:
        print(f"Safety Error: {e}")
    return alert_html

# ... (rest of the calendar code stays the same)
