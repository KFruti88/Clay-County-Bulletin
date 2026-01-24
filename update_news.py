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

# We use a VERY unique user agent to prevent being blocked by the map service
geolocator = Nominatim(user_agent="Clay_County_Safety_Bulletin_System_v4_KFruti")

def get_human_location(location_text):
    """Deep search for street names with a longer 60-second timeout."""
    coord_pattern = r'(-?\d+\.\d+),\s*(-?\d+\.\d+)'
    coord_match = re.search(coord_pattern, location_text)
    
    if coord_match:
        lat, lon = coord_match.groups()
        for attempt in range(3):
            try:
                # We give it 60 seconds to ensure it finds Flora/Louisville addresses
                location = geolocator.reverse(f"{lat}, {lon}", timeout=60)
                if location:
                    parts = location.address.split(',')
                    return f"{parts[0].strip()}, {parts[1].strip()}"
                break
            except:
                continue 
                
    # If no numbers, strip ugly URLs and show the landmark (e.g., "by race track")
    clean_text = re.sub(r'https?://\S+', '', location_text).strip()
    return clean_text if clean_text else "Flora, IL"

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
                # FIX: Check multiple column names to stop the "undefined" error
                town = row.get('Town/City') or row.get('Town') or row.get('City') or 'Clay County'
                hazard = row.get('What is the hazard?', 'SAFETY ALERT').upper()
                raw_loc = row.get('Where is it exactly?', '')
                
                # Get the translated street name
                friendly_loc = get_human_location(raw_loc)
                
                # Hidden map link for the button
                map_link = "https://www.google.com/maps"
                link_match = re.search(r'(https?://\S+)', raw_loc)
                if link_match:
                    map_link = link_match.group(1)
                elif coord_match := re.search(r'(-?\d+\.\d+),\s*(-?\d+\.\d+)', raw_loc):
                    map_link = f"https://www.google.com/maps/search/?api=1&query={coord_match.group(0)}"

                alert_html += f'''
                <div class="event-entry" style="border-left: 10px solid #eb1c24; background: #fff5f5; padding: 18px; margin-bottom: 15px; border-radius: 4px;">
                    <div class="event-info">
                        <h3 style="margin: 0 0 8px 0; color: #eb1c24; font-family: 'Arial Black', sans-serif; font-size: 24px; font-weight: 900; line-height: 1.1;">
                            ⚠️ {hazard}
                        </h3>
                        <div style="font-size: 17px; font-weight: bold; color: #333; margin-bottom: 10px;">
                             📍 {friendly_loc} <span style="font-weight: normal; color: #666;">({town})</span>
                        </div>
                        <div style="font-size: 12px; color: #666; border-top: 1px solid #ddd; padding-top: 12px; margin-top: 10px;">
                            Reported: {timestamp.strftime('%I:%M %p')} 
                            <span style="margin: 0 15px;">•</span>
                            <a href="{map_link}" target="_blank" style="display: inline-block; background: #eb1c24; color: white; padding: 6px 14px; text-decoration: none; border-radius: 4px; font-weight: bold; font-size: 12px;">
                                VIEW ON MAP
                            </a>
                        </div>
                    </div>
                </div>'''
    except Exception as e:
        print(f"Safety Error: {e}")
    return alert_html

# ... (rest of your calendar code) ...
