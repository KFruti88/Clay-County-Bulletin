import requests
from icalendar import Calendar
from datetime import datetime, date, timedelta
import pytz

SOURCES = [
    "https://calendar.google.com/calendar/ical/ceab82d01e29c237da2e761555f2d2c2da76431b94e0def035ff04410e2cd71d%40group.calendar.google.com/public/basic.ics",
    "https://www.facebook.com/events/ical/upcoming/?uid=100063547844172&key=rjmOs5JdN9NQhByz"
]

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
                
                # GRABBING THE SPECIFIC DATA
                start = ev.get('dtstart').dt
                loc = str(ev.get('location') or 'Clay County')
                desc = str(ev.get('description') or '').replace('\\n', '<br>')
                
                d = start if isinstance(start, date) else start.astimezone(central).date()

                if today <= d <= limit:
                    is_ad = not isinstance(start, datetime)
                    t_label = "ALL DAY" if is_ad else start.astimezone(central).strftime("%I:%M %p").lstrip("0")
                    
                    # This HTML structure MUST have these classes for the index to see them
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
    ad, t = fetch_events()
    with open("feed.html", "w", encoding="utf-8") as f:
        f.write(f'<div id="bot-ad-data">{ad}</div><div id="bot-t-data">{t}</div>')
