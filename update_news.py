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

def get_real_address(location_text):
    """Translates techy data into 'People Talk'."""
    # Check for coordinates (the long numbers)
    coord_pattern = r'(-?\d+\.\d+),\s*(-?\d+\.\d+)'
    coord_match = re.search(coord_pattern, location_text)
    
    # Check for a URL (the link)
    link_pattern = r'(https?://\S+)'
    link_match = re.search(link_pattern, location_text)

    # 1. If it's a coordinate, translate it to a street name
    if coord_match:
        lat, lon = coord_match.groups()
        try:
            location = geolocator.reverse(f"{lat}, {lon}", timeout=10)
            if location:
                parts = location.address.split(',')
                # Return 'Street, Town' (e.g., 'Old Hwy 50, Flora')
                return f"{parts[0].strip()}, {parts[1].strip()}"
        except:
            pass

    # 2. If they pasted a link but ALSO typed a description (like "Rail road west side")
    # we want to strip the link out and just show their words.
    if link_match:
        clean_text = location_text.replace(link_match.group(1), "").strip()
        if clean_text:
            return clean_text
        return "Shared Map Location" # Fallback if they ONLY sent a link

    # 3. If they just typed words, keep them! (e.g., "By the water tower")
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
            if not timestamp_str: continue
                
            timestamp = datetime.strptime(timestamp_str, '%m/%d/%Y %H:%M:%S')
            timestamp = central.localize(timestamp)
            
            if timestamp > cutoff:
                raw_loc = row.get('Where is it exactly?', 'Location TBD')
                display_location = get_real_address(raw_loc)
                
                # Check if there is a link for the "Hover" map
                map_link = ""
                link_match = re.search(r'(https?://\S+)', raw_loc)
                if link_match:
                    map_link = link_match.group(1)
                elif re.search(r'(-?\d+\.\d+),\s*(-?\d+\.\d+)', raw_loc):
                    # If they gave coords, turn them into a google link for the hover
                    coords = re.search(r'(-?\d+\.\d+),\s*(-?\d+\.\d+)', raw_loc).group(0)
                    map_link = f"https://www.google.com/maps/search/?api=1&query={coords}"

                # Wrap the location in a 'tooltip' style for the hover effect
                alert_html += f'''
                <div class="event-entry" style="border-left: 5px solid #eb1c24; background: #fff5f5; padding: 10px; margin-bottom: 10px;">
                    <div class="event-info">
                        <span class="event-meta" style="color: #eb1c24; font-weight: bold;">
                            ⚠️ {row.get('What is the hazard?', 'Hazard')} • {row.get('Town/City', 'Clay County')}
                        </span>
                        <h4 style="margin: 5px 0;">
                            <a href="{map_link}" target="_blank" title="Click to see on Map" style="text-decoration: none; color: #222;">
                                {display_location} 📍
                            </a>
                        </h4>
                        <div class="event-description">Reported: {timestamp.strftime('%I:%M %p')}</div>
                    </div>
                </div>'''
    except Exception as e:
        print(f"Safety Sheet Error: {e}")
    return alert_html

# ... (Keep your fetch_calendar_events and main block as they were) ...
