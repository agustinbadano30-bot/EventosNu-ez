import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pandas as pd
import re
from config import FAKE_TODAY, RIVER_START_DATE, MONTHS_ES, MONUMENTAL_CONCERTS

# --- CONFIG MOVIDO A config.py ---

# --- HOSTING & HELPERS ---
def get_soup(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return BeautifulSoup(response.content, 'html.parser')
    except: pass
    return None



# --- PARSERS ---
def parse_espn_date(date_str, year_context=2025):
    """
    Parses ESPN formats: "Sáb, 13 Sep" OR "13/09/25" OR "Vie., 24 de Oct."
    Tries to extract Time if present "19:00".
    """
    if not date_str: return None
    date_str = date_str.lower().strip()
    
    # Time Extraction (HH:MM)
    time_obj = None
    t_match = re.search(r'(\d{1,2}):(\d{2})', date_str)
    if t_match:
        time_obj = (int(t_match.group(1)), int(t_match.group(2)))
    
    # 1. Slash Format: "13/09/25" or "13/9"
    match_slash = re.search(r'(\d{1,2})/(\d{1,2})', date_str)
    if match_slash:
        try:
            day = int(match_slash.group(1))
            month = int(match_slash.group(2))
            year = year_context or datetime.now().year
            
            # Year suffix logic: "12/10/25"
            y_match = re.search(r'/(\d{2,4})$', date_str)
            if y_match:
                y_val = int(y_match.group(1))
                year = y_val if y_val > 100 else 2000 + y_val
                
            dt = datetime(year, month, day)
            if time_obj: dt = dt.replace(hour=time_obj[0], minute=time_obj[1])
            return dt
        except: pass

    # 2. Relaxed Text Search
    # Find any 1-2 digits
    day_match = re.search(r'(\d{1,2})', date_str)
    if day_match:
        try:
            day = int(day_match.group(1))
            
            # Find any known month name fragment
            # Sort months by length desc to match "enero" before "ene"
            sorted_months = sorted(MONTHS_ES.keys(), key=len, reverse=True)
            
            month = None
            for m_key in sorted_months:
                if m_key in date_str:
                    month = MONTHS_ES[m_key]
                    break
            
            if month:
                year = year_context or datetime.now().year
                dt = datetime(year, month, day)
                if time_obj: dt = dt.replace(hour=time_obj[0], minute=time_obj[1])
                return dt
        except: pass
        
    return None

def parse_obras_dates(text, year_context=2025):
    """
    Robustly parses multiple dates from event text.
    Supports: "27 y 28 de Diciembre", "10, 11 y 12 de Febrero", "31 de Enero y 1 de Febrero"
    Returns a list of datetime objects.
    """
    if not text: return []
    text = text.lower()
    found_dates = []

    # Find all month occurrences
    sorted_months = sorted(MONTHS_ES.keys(), key=len, reverse=True)
    month_pattern = "|".join(sorted_months)
    
    month_matches = list(re.finditer(fr'\b({month_pattern})\b', text))
    
    last_end = 0
    for m in month_matches:
        month_name = m.group(1)
        start, end = m.span()
        
        # Look at text immediately preceding this month (context window of 50 chars)
        snippet_end = start
        snippet_start = max(last_end, start - 50)
        snippet = text[snippet_start:snippet_end]
        
        # Find all numbers in this snippet
        nums = re.findall(r'\d{1,2}', snippet)
        
        # Extract year (look ahead after month)
        year = year_context
        year_snippet = text[end:end+20]
        y_match = re.search(r'20\d{2}', year_snippet)
        if y_match:
            year = int(y_match.group(0))
        
        month_val = MONTHS_ES[month_name]
        
        # Add valid dates
        for day_str in nums:
            try:
                d = int(day_str)
                if 1 <= d <= 31:
                    dt = datetime(year, month_val, d)
                    # Avoid duplicates
                    if dt not in found_dates:
                        found_dates.append(dt)
            except:
                pass
                
        last_end = end

    return found_dates

# --- SCRAPERS ---
def get_river_data_combined(year_context=2025):
    matches = []
    urls = [
        "https://www.espn.com.ar/futbol/equipo/calendario/_/id/16/river-plate",
        "https://www.espn.com.ar/futbol/equipo/resultados/_/id/16/river-plate"
    ]
    
    for url in urls:
        soup = get_soup(url)
        if not soup: continue
        
        for row in soup.select("tbody tr"):
            try:
                # 1. Parse Date & Time
                date_el = row.select_one('td[data-col-id="0"] span')
                if not date_el: 
                    # Fallback for Results table where date is just text in first col
                    cols = row.find_all('td')
                    if cols: date_text = cols[0].get_text(strip=True)
                    else: continue
                else:
                    date_text = date_el.get_text(strip=True)
                
                # Append full row text for context (time, year)
                full_text = row.get_text(" ")
                dt = parse_espn_date(date_text + " " + full_text, year_context)
                if not dt: continue

                # 2. Identify Opponent via Links (Most Robust)
                # Find all team links in the row
                anchors = row.select('a[href*="/equipo/"]')
                teams = []
                for a in anchors:
                    txt = a.get_text(strip=True)
                    # Filter out short/empty or known irrelevant
                    if len(txt) > 2:
                        teams.append(txt)
                
                # If distinct teams found
                # Filter out "River Plate"
                rivals = [t for t in teams if "River" not in t]
                
                if rivals:
                    opp = rivals[0] # Best guess
                else:
                    # Fallback text analysis if no links (rare)
                    # Try finding the cell with "vs" or "@"
                    txt_clean = full_text.replace("River Plate", "").replace("vs", "").replace("@", "")
                    # This is risky, but a last resort. Better to skip or mark unknown?
                    # Let's try to pluck the biggest text chunk?
                    opp = "Rival a confirmar"

                # 3. Determine Condition (Home/Away)
                # If "vs" is present, usually Home. If "@" or " at ", usually Away.
                # Or check index of River in text.
                cond = "Visitante"
                # Check for explicit "vs" text cell
                for cell in row.find_all('td'):
                    ct = cell.get_text().lower()
                    if "vs" in ct: 
                        cond = "Local"
                        break
                    if "@" in ct:
                        cond = "Visitante"
                        break
                
                # Heuristic: If River appears BEFORE Opponent in text, usually Local (Home) for Results
                # But ESPN Calendar table format: Date | Opponent | Time
                # Validating "Local" only matches
                
                # Logic update: We only want LOCAL matches for the Alert system?
                # The user wants "Alerta Nuñez", implying traffic impact. So YES, only LOCAL.
                # How to definitively know Local?
                # In Calendar: Col 1 is "Adversario". If it starts with "vs", it's Home. If "@", Away.
                # In Results: It lists "vs Rival" or "@ Rival" usually.
                
                if "vs" in full_text.lower():
                    cond = "Local"
                elif "@" in full_text: 
                    cond = "Visitante"
                else:
                    # Score format: "River Plate 2 - 1 Boca Juniors" -> River Home
                    r_idx = full_text.find("River Plate")
                    o_idx = full_text.find(opp)
                    if r_idx != -1 and o_idx != -1 and r_idx < o_idx:
                        cond = "Local"
                
                if cond == "Local":
                    # Deduplication check?
                    # We might scrape same match from Calendar vs Results if near transition.
                    # We can use date + opp as key later or just append.
                    matches.append({
                        "fecha": dt.strftime("%Y-%m-%d"),
                        "evento": f"River Plate Vs {opp}",
                        "lugar": "Monumental",
                        "obj_date": dt
                    })

            except: continue
            
    return matches

def get_obras_events(year_context=2025):
    events = []
    soup = get_soup("https://estadioobras.com.ar/")
    if not soup: return []
    
    seen_keys = set()
    
    for h3 in soup.find_all('h3'):
        link = h3.find('a')
        if not link: continue
        
        title = link.get_text(strip=True)
        # Use grandparent text to ensure we catch date outside title wrapper
        card_text = ""
        if h3.parent and h3.parent.parent:
             card_text = h3.parent.parent.get_text(" ", strip=True)
        else:
             card_text = h3.parent.get_text(" ", strip=True)
             
        dates = parse_obras_dates(card_text, year_context)
        
        for dt in dates:
            # Create a unique key for deduplication
            key = (dt.strftime("%Y-%m-%d"), title)
            if key in seen_keys:
                continue
            
            seen_keys.add(key)
            events.append({
                "fecha": dt.strftime("%Y-%m-%d"),
                "evento": title,
                "lugar": "Estadio Obras",
                "obj_date": dt
            })
            
    return events


def get_monumental_concerts():
    """
    Merges data from Google Sheets (CSV) and hardcoded MONUMENTAL_CONCERTS.
    """
    events = []
    seen_keys = set()
    
    # Helper to add unique events
    def add_event(date_str, title, place):
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            # Key for deduplication: date + title
            key = (date_str, title.lower().strip())
            if key not in seen_keys:
                seen_keys.add(key)
                events.append({
                    "fecha": date_str,
                    "evento": title,
                    "lugar": place,
                    "obj_date": dt
                })
        except: pass

    # 1. Try Google Sheet
    try:
        from config import SHEET_URL
        if SHEET_URL:
            import io
            r = requests.get(SHEET_URL, timeout=5)
            r.raise_for_status()
            
            df = pd.read_csv(io.StringIO(r.text))
            df.columns = [c.lower().strip() for c in df.columns]
            
            for _, row in df.iterrows():
                try:
                    add_event(str(row['fecha']).strip(), row['evento'], row['lugar'])
                except: continue
    except Exception as e:
        print(f"Sheet Error: {e}")

    # 2. Add from Config (Hardcoded)
    # This ensures 2026 data in config is added even if Sheet works
    try:
        from config import MONUMENTAL_CONCERTS
        for c in MONUMENTAL_CONCERTS:
            add_event(c["fecha"], c["evento"], c["lugar"])
    except: pass
        
    return events


# --- WEATHER HELPERS ---
@st.cache_data(ttl=86400, show_spinner=False)
def get_weather_data():
    """Fetches 16-day forecast for Nuñez from Open-Meteo."""
    try:
        # Lat/Lon for Estadio Monumental
        url = "https://api.open-meteo.com/v1/forecast?latitude=-34.5453&longitude=-58.4498&daily=weathercode,temperature_2m_max,temperature_2m_min&timezone=auto"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            daily = data.get('daily', {})
            
            weather_map = {}
            dates = daily.get('time', [])
            codes = daily.get('weathercode', [])
            maxs = daily.get('temperature_2m_max', [])
            mins = daily.get('temperature_2m_min', [])
            
            for i, d_str in enumerate(dates):
                weather_map[d_str] = {
                    "code": codes[i],
                    "max": round(maxs[i]),
                    "min": round(mins[i])
                }
            return weather_map
    except: pass
    return {}

def get_weather_icon(code):
    # WMO Weather interpretation codes
    if code == 0: return "☀️"
    if code in [1, 2, 3]: return "🌥️"
    if code in [45, 48]: return "🌫️"
    if code in [51, 53, 55, 56, 57]: return "🌦️"
    if code in [61, 63, 65, 66, 67, 80, 81, 82]: return "🌧️"
    if code in [71, 73, 75, 77, 85, 86]: return "❄️"
    if code in [95, 96, 99]: return "⛈️"
    return "🌡️"

@st.cache_data(ttl=86400, show_spinner=False)
def fetch_all_events():
    # Fetch 2025 (River)
    r25 = get_river_data_combined(2025)
    
    # Fetch 2026 (River)
    r26 = get_river_data_combined(2026)
    
    # Obras: call ONCE. The scraper grabs all H3/Cards from the live page.
    # The parser handles year extraction if present in text, or assumes context.
    o_all = get_obras_events(2025)
    
    # Concerts
    ev_monu = get_monumental_concerts()
    
    return r25 + r26 + o_all + ev_monu

# --- MAIN APP ---
def main():
    st.set_page_config(page_title="Alerta Nuñez", page_icon="🚦", layout="centered")
    
    # Header Layout with Refresh Button
    c_title, c_btn = st.columns([5, 1])
    with c_title:
        st.title("🚦 Alerta Nuñez")
        st.caption("Monitoreo de tráfico y eventos: River Plate (Fútbol), Estadio Monumental (Recitales) y Estadio Obras.")
    with c_btn:
        if st.button("🔄", help="Actualizar datos ahora"):
            st.cache_data.clear()
            st.rerun()

    sim_mode = True if FAKE_TODAY else False
    if sim_mode:
        current_date = FAKE_TODAY
        st.caption(f"📅 MODO SIMULACIÓN: {current_date.strftime('%d/%m/%Y')}")
    else:
        # LOGICA "NOCTURNA":
        now = datetime.now() - timedelta(hours=3) 
        current_date = datetime(now.year, now.month, now.day)
        st.caption(f"📅 Fecha Real (Ajustada): {current_date.strftime('%d/%m/%Y')}")

    # --- STYLES ---
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
        }

        /* ULTRA COMPACT LAYOUT */
        div.block-container {
            padding-top: 1rem !important; /* Minimal top spacing */
            padding-bottom: 1rem !important;
            max-width: 700px;
        }
        
        /* Hide default Streamlit Header/Hamburger to save space */
        header[data-testid="stHeader"] {
            display: none !important;
        }

        h1 {
            color: #111827;
            font-weight: 800 !important;
            letter-spacing: -0.025em;
            margin-bottom: 0.1rem !important;
            font-size: 1.6rem !important;
            line-height: 1.2;
        }
        p {
            margin-bottom: 0.25rem;
            font-size: 0.9rem;
        }
        
        h2, h3 {
            color: #374151;
            font-weight: 600 !important;
            margin-top: 1rem !important;
            margin-bottom: 0.5rem !important;
            font-size: 1.2rem !important;
        }
        
        hr {
            margin-top: 0.5rem !important;
            margin-bottom: 0.5rem !important;
        }
        
        /* Event Card */
        .event-card {
            border-radius: 12px;
            padding: 0.85rem; 
            margin-bottom: 0.6rem; 
            box-shadow: 0 1px 3px -1px rgba(0, 0, 0, 0.1);
            transition: all 0.2s ease-in-out;
            border-left: 5px solid #9ca3af;
            background-color: #ffffff;
            color: #1f2937;
        }
        
        .event-card:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }

        /* RIVER PLATE */
        .card-river { 
            background-color: #ffffff;
            border: 1px solid #e5e7eb;
            border-left-color: #e11d48;
        }
        .card-river .event-title { color: #111827; }
        .card-river .date-badge { background-color: #fee2e2; color: #991b1b; }
        
        /* OBRAS SANITARIAS */
        .card-obras {
            background-color: #1a1a1a !important;
            border: 1px solid #333;
            border-left-color: #fbbf24;
        }
        .card-obras .event-title { color: #f3f4f6 !important; }
        .card-obras .location-tag { color: #d1d5db !important; }
        .card-obras .date-badge { 
            background-color: rgba(251, 191, 36, 0.2); 
            color: #fbbf24; 
            border: 1px solid rgba(251, 191, 36, 0.3);
        }

        /* RECITALES */
        /* RECITALES */
        .card-recital { 
            background-color: #0f0f0f !important;
            border: 1px solid #333;
            border-left-color: #ef4444; /* Red */
        }
        .card-recital .event-title { color: #f9fafb !important; }
        .card-recital .location-tag { color: #9ca3af !important; }
        .card-recital .date-badge { 
            background-color: #450a0a; 
            color: #fca5a5; 
            border: 1px solid #7f1d1d;
        }

        .event-title {
            font-size: 1rem;
            font-weight: 700;
            margin: 0.2rem 0 0.1rem 0;
            line-height: 1.2;
        }
        
        .location-tag {
            font-size: 0.75rem;
            color: #6b7280;
            font-weight: 500;
            display: flex;
            align-items: center;
        }

        .date-badge {
            display: inline-block;
            padding: 0.1rem 0.5rem;
            border-radius: 9999px;
            font-size: 0.65rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .alert-box {
            padding: 0.6rem;
            border-radius: 8px;
            text-align: center;
            font-weight: 500;
            margin-bottom: 0.75rem;
            border: 1px solid transparent;
            font-size: 0.9rem;
            line-height: 1.4;
        }
        
        .alert-red { background-color: #fee2e2; color: #991b1b; border-color: #fca5a5; }
        .alert-green { background-color: #d1fae5; color: #065f46; border-color: #6ee7b7; }
        .alert-gray { background-color: #f3f4f6; color: #374151; border-color: #e5e7eb; }
        
        .btn-traffic {
            display: inline-block;
            margin-top: 0.4rem;
            padding: 0.25rem 0.75rem;
            background-color: #ffffff;
            color: #991b1b;
            text-decoration: none;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 600;
            border: 1px solid #fca5a5;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
            transition: all 0.2s;
        }
        .btn-traffic:hover {
            background-color: #fff1f2;
            transform: translateY(-1px);
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        }
        
        /* Spinner */
        .stSpinner > div { border-top-color: #3b82f6 !important; }
        </style>
    """, unsafe_allow_html=True)
    
    # Fetch Data
    with st.spinner("Actualizando agenda del barrio..."):
        all_events = fetch_all_events()
        weather_data = get_weather_data()
        
    # --- DASHBOARD LOGIC ---
    future = []
    
    for e in all_events:
        threshold = current_date
        
        # Override threshold for River if configured
        if e.get('lugar') == "Monumental" and RIVER_START_DATE:
            threshold = RIVER_START_DATE
            
        if e['obj_date'] >= threshold:
             future.append(e)

    future.sort(key=lambda x: x['obj_date'])
    
    nearby = False
    details = ""
    if future:
        diff = (future[0]['obj_date'] - current_date).days
        if diff <= 3:
            nearby = True
            details = f"{future[0]['lugar']}: {future[0]['evento']}"

    st.divider()
    
    if nearby:
        st.markdown(f"""
            <div class="alert-box alert-red">
                🚨 ALERTA DE TRÁFICO <br>
                <span style="font-weight:normal">{details}</span> <br>
                En {diff} días <br>
                <a href="https://www.google.com/maps/@-34.545,-58.449,15z/data=!5m1!1e1" target="_blank" class="btn-traffic">
                    🗺️ Ver Tráfico en Vivo
                </a>
            </div>
        """, unsafe_allow_html=True)
    elif future:
        st.markdown("""
            <div class="alert-box alert-green">
                🟢 TRÁFICO NORMAL <br>
                <span style="font-weight:normal">Zona liberada por ahora.</span>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div class="alert-box alert-gray">
                ⚪ SIN DATOS / VACACIONES
            </div>
        """, unsafe_allow_html=True)
        
    st.divider()
    st.subheader("Agenda del Barrio")
    
    if future:
        for e in future:
            # Determine Style
            card_class = "event-card"
            if "Monumental" in e['lugar']:
                if "Recital" in e['lugar']:
                    card_class += " card-recital"
                else:
                    card_class += " card-river"
            elif "Obras" in e['lugar']:
                card_class += " card-obras"
                
            # Date Formatting
            d_obj = e['obj_date']
            d_diff = (d_obj - current_date).days
            
            # Smart Label
            if d_diff == 0: day_label = "HOY"
            elif d_diff == 1: day_label = "MAÑANA"
            else: day_label = f"En {d_diff} días"
            
            # Weather Lookup
            weather_html = ""
            date_key = d_obj.strftime("%Y-%m-%d")
            if date_key in weather_data:
                w = weather_data[date_key]
                icon = get_weather_icon(w['code'])
                weather_html = f" • {w['max']}°C {icon}"

            # Formatting Date & Time
            date_pretty = d_obj.strftime("%d/%m/%Y")
            time_str = ""
            if d_obj.hour != 0 or d_obj.minute != 0:
                time_str = f" • ⏰ {d_obj.strftime('%H:%M')} hs"
            
            st.markdown(f"""
                <div class="{card_class}">
                    <div class="date-badge">{date_pretty} • {day_label}{weather_html}</div>
                    <div class="event-title">{e['evento']}</div>
                    <div class="location-tag">📍 {e['lugar']}{time_str}</div>
                </div>
            """, unsafe_allow_html=True)

    else:
        st.caption("No hay eventos programados en el radar.")

if __name__ == "__main__":
    main()

