# Initialize geolocator with an even more unique name
geolocator = Nominatim(user_agent="Clay_County_Public_Safety_Portal_v3")

def get_human_location(location_text):
    """Deep search for street names with a longer 30-second timeout."""
    coord_pattern = r'(-?\d+\.\d+),\s*(-?\d+\.\d+)'
    coord_match = re.search(coord_pattern, location_text)
    
    if coord_match:
        lat, lon = coord_match.groups()
        # Trying 3 times with a longer 30-second wait
        for attempt in range(3):
            try:
                # Bumping timeout to 30 to ensure the mapping service answers
                location = geolocator.reverse(f"{lat}, {lon}", timeout=30)
                if location:
                    parts = location.address.split(',')
                    return f"{parts[0].strip()}, {parts[1].strip()}"
                break
            except:
                continue 
                
    # If it's a link or technical junk, strip it and look for landmarks (like "Rail Depo")
    clean_text = re.sub(r'https?://\S+', '', location_text).strip()
    return clean_text if clean_text else "Location Pin"

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
                town = row.get('Town/City', 'Clay County')
                
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
                <div class="event-entry" style="border-left: 8px solid #eb1c24; background: #fff5f5; padding: 15px; margin-bottom: 15px; border-radius: 4px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1);">
                    <div class="event-info">
                        <h3 style="margin: 0 0 5px 0; color: #eb1c24; font-family: 'Arial Black', sans-serif; font-size: 22px; font-weight: 900; line-height: 1.1;">
                            ⚠️ {hazard}
                        </h3>
                        <div style="font-size: 16px; font-weight: bold; color: #333; margin-bottom: 8px;">
                             📍 {friendly_loc} <span style="font-weight: normal; color: #666;">({town})</span>
                        </div>
                        <div style="font-size: 12px; color: #666; border-top: 1px solid #ddd; padding-top: 10px; margin-top: 10px;">
                            Reported: {timestamp.strftime('%I:%M %p')} 
                            <span style="margin: 0 10px;">•</span>
                            <a href="{map_link}" target="_blank" style="display: inline-block; background: #eb1c24; color: white; padding: 6px 12px; text-decoration: none; border-radius: 4px; font-weight: bold; font-size: 11px; text-transform: uppercase;">
                                View on Map
                            </a>
                        </div>
                    </div>
                </div>'''
    except Exception as e:
        print(f"Safety Error: {e}")
    return alert_html
