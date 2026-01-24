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

# Initialize geolocator with a VERY unique name to prevent being blocked
geolocator = Nominatim(user_agent="Clay_County_Public_Bulletin_Project_v1_KFruti")

def get_human_location(location_text):
    """Deep search for street names with a longer 60-second timeout."""
    coord_pattern = r'(-?\d+\.\d+),\s*(-?\d+\.\d+)'
    coord_match = re.search(coord_pattern, location_text)
    
    if coord_match:
        lat, lon = coord_match.groups()
        # Trying 3 times to be sure
        for attempt in range(3):
            try:
                # Bumping timeout to 60 to ensure the mapping service answers
                location = geolocator.reverse(f"{lat}, {lon}", timeout=60)
                if location:
                    parts = location.address.split(',')
                    # Returns "Street Name, Town"
                    return f"{parts[0].strip()}, {parts[1].strip()}"
                break
            except:
                continue 
                
    # If it's a link or technical junk, strip it and look for landmarks (like "Rail Depo")
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
                # 1. THE BIG HEADLINE (The Hazard)
                hazard = row.get('What is the hazard?', 'SAFETY ALERT').upper()
                raw_loc = row.get('Where is it exactly?', '')
                
                # FIX: Handles 'Town/City', 'Town', or 'City' column names to stop 'undefined'
                town = row.get('Town/City') or row.get('Town') or row.get('City') or 'Clay County'
                
                # 2. THE TRANSLATED LOCATION
                friendly_loc = get_human_location(raw_loc)
                
                # 3. THE HIDDEN MAP LINK
                map_link = "https://www.google.com/maps"
                link_match = re.search(r'(https?://\S+)', raw_loc)
                if link_match:
                    map_link = link_match.group(1)
                elif coord_match := re.search(r'(-?\d+\.\d+),\s*(-?\d+\.\d+)', raw_loc):
                    map_link = f"https://www.google.com/maps/search/?api=1&query={coord_match.group(0)}"

                # 4. THE USER-FRIENDLY DESIGN
                alert_html += f'''
                <div class="event-entry" style="border-left: 10px solid #eb1c24; background: #fff5f5; padding: 20px; margin-bottom: 20px; border-radius: 4px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1);">
                    <div class="event-info">
                        <h3 style="margin: 0 0 8px 0; color: #eb1c24; font-family: 'Arial Black', sans-serif; font-size: 24px; font-weight: 900; line-height: 1.1;">
                            ⚠️ {hazard}
                        </h3>
                        <div style="font-size: 18px; font-weight: bold; color: #333; margin-bottom: 10px;">
                             📍 {friendly_loc} <span style="font-weight: normal; color: #666;">({town})</span>
                        </div>
                        <div style="font-size: 12px; color: #666; border-top: 1px solid #ddd; padding-top: 12px; margin-top: 12px;">
                            Reported: {timestamp.strftime('%I:%M %p')} 
                            <span style="margin: 0 15px;">•</span>
                            <a href="{map_link}" target="_blank" style="display: inline-block; background: #eb1c24; color: white; padding: 8px 16px; text-decoration: none; border-radius: 4px; font-weight: bold; font-size: 12px; text-transform: uppercase;">
                                View on Map
                            </a>
                        </div>
                    </div>
                </div>'''
    except Exception as e:
        print(f"Safety Error: {e}")
    return alert_html

# ... (rest of your calendar code) ...
