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
    """
    if not date_str: return None
    date_str = date_str.lower().strip()
    
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
                
            return datetime(year, month, day)
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
            
            for m_key in sorted_months:
                if m_key in date_str:
                    month = MONTHS_ES[m_key]
                    year = year_context or datetime.now().year
                    return datetime(year, month, day)
        except: pass
        
    return None

def parse_obras_date(text, year_context=2025):
    """
    Parses Obras format from full card text.
    Looking for "20 de Diciembre" or any "DD ... Month" pattern.
    """
    if not text: return None
    text = text.lower()
    
    # Reuse Relaxed logic or slightly distinct if needed. 
    # For safe keeping, identical relaxed logic is best.
    
    # 1. Find Day
    day_match = re.search(r'(\d{1,2})', text)
    if day_match:
        try:
            day = int(day_match.group(1))
            
            # Find Month
            sorted_months = sorted(MONTHS_ES.keys(), key=len, reverse=True)
            for m_key in sorted_months:
                 # Check if month name appears after the day digit to avoid false positives?
                 # Obras usually: "27 y 28 de Diciembre"
                 if m_key in text:
                     month = MONTHS_ES[m_key]
                     
                     # Year logic check
                     year = year_context
                     y_match = re.search(r'20\d{2}', text)
                     if y_match:
                        year = int(y_match.group(0))
                     
                     return datetime(year, month, day)
        except: pass
        
    return None

# --- SCRAPERS ---
def get_river_data_combined(year_context=2025):
    matches = []
    
    # 1. CALENDAR (Future)
    soup = get_soup("https://www.espn.com.ar/futbol/equipo/calendario/_/id/16/river-plate")
    if soup:
        for row in soup.select("tbody tr"):
            try:
                date_el = row.select_one('td[data-col-id="0"] span')
                if not date_el: continue
                
                dt = parse_espn_date(date_el.get_text(strip=True), year_context)
                if not dt: continue
                
                opp_cell = row.select_one('td[data-col-id="1"]')
                cond = "Local" if "vs" in opp_cell.get_text() else "Visitante"
                opp = opp_cell.select_one('div.ScoreCell__TeamName span, a div span').get_text(strip=True)
                
                if cond == "Local":
                    matches.append({
                        "fecha": dt.strftime("%Y-%m-%d"),
                        "evento": f"Vs {opp}",
                        "lugar": "Monumental",
                        "obj_date": dt
                    })
            except: continue

    # 2. Results (Past)
    soup = get_soup("https://www.espn.com.ar/futbol/equipo/resultados/_/id/16/river-plate")
    if soup:
        for row in soup.select("tbody tr"):
            try:
                cols = row.find_all('td')
                if not cols: continue
                
                dt = parse_espn_date(cols[0].get_text(strip=True), year_context)
                if not dt: continue
                
                teams = [a.get_text(strip=True) for a in row.select('a.AnchorLink') 
                         if a.find_parent('div', class_='ScoreCell__TeamName')]
                if not teams: 
                     teams = [a.get_text(strip=True) for a in row.select('a.AnchorLink') if len(a.get_text(strip=True)) > 3]
                
                rivals = [t for t in teams if "River" not in t]
                rival = rivals[0] if rivals else "Desconocido"
                
                row_text = row.get_text()
                cond = "Local" if row_text.find("River Plate") < row_text.find(rival) else "Visitante"
                
                if cond == "Local":
                    matches.append({
                        "fecha": dt.strftime("%Y-%m-%d"),
                        "evento": f"Vs {rival}",
                        "lugar": "Monumental",
                        "obj_date": dt
                    })
            except: continue
            
    return matches

def get_obras_events(year_context=2025):
    events = []
    soup = get_soup("https://estadioobras.com.ar/")
    if not soup: return []
    
    for h3 in soup.find_all('h3'):
        link = h3.find('a')
        if not link: continue
        
        title = link.get_text(strip=True)
        # Use grandparent text to ensure we catch date outside title wrapper
        # h3.parent is often just the title container. h3.parent.parent is the Card.
        card_text = ""
        if h3.parent and h3.parent.parent:
             card_text = h3.parent.parent.get_text(" ", strip=True)
        else:
             card_text = h3.parent.get_text(" ", strip=True)
             
        dt = parse_obras_date(card_text, year_context)
        
        if dt:
            events.append({
                "fecha": dt.strftime("%Y-%m-%d"),
                "evento": title,
                "lugar": "Estadio Obras",
                "obj_date": dt
            })
            
    return events

def get_monumental_concerts():
    """
    Returns hardcoded concerts from config.
    """
    events = []
    for c in MONUMENTAL_CONCERTS:
        try:
            dt = datetime.strptime(c["fecha"], "%Y-%m-%d")
            events.append({
                "fecha": c["fecha"],
                "evento": c["evento"],
                "lugar": c["lugar"],
                "obj_date": dt
            })
        except: pass
    return events

# --- MAIN APP ---
def main():
    st.set_page_config(page_title="Alerta Nuñez", page_icon="🚦", layout="centered")
    st.title("🚦 Alerta Nuñez")
    st.caption("Monitoreo de tráfico y eventos: River Plate (Fútbol), Estadio Monumental (Recitales) y Estadio Obras.")

    sim_mode = True if FAKE_TODAY else False
    if sim_mode:
        current_date = FAKE_TODAY
        st.caption(f"📅 MODO SIMULACIÓN: {current_date.strftime('%d/%m/%Y')}")
    else:
        # LOGICA "NOCTURNA":
        # Si son las 00:00, 01:00 o 02:00 AM, seguimos considerando que es "el día anterior"
        # para que no desaparezcan los eventos de la lista hasta las 3 AM.
        now = datetime.now() - timedelta(hours=3) 
        current_date = datetime(now.year, now.month, now.day)
        st.caption(f"📅 Fecha Real (Ajustada): {current_date.strftime('%d/%m/%Y')}")

    # Fetch
    with st.spinner("Actualizando agenda del barrio..."):
        # We assume 2025 for simplicity as per user context
        ev_river = get_river_data_combined(2025)
        ev_obras = get_obras_events(2025)
        ev_monu = get_monumental_concerts()
        
        all_events = ev_river + ev_obras + ev_monu
        
    # Filter Future / Custom Start
    future = []
    
    for e in all_events:
        threshold = current_date
        
        # Override threshold for River if configured
        if e.get('lugar') == "Monumental" and RIVER_START_DATE:
            threshold = RIVER_START_DATE
            
        if e['obj_date'] >= threshold:
             future.append(e)

    future.sort(key=lambda x: x['obj_date'])
    
    # --- STYLES ---
    st.markdown("""
        <style>
        .stApp { background-color: #f8f9fa; }
        .event-card {
            background-color: white;
            padding: 15px;
            border-radius: 12px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            margin-bottom: 12px;
            border-left: 5px solid #ccc;
            font-family: sans-serif;
            color: #333;
        }
        .card-river { border-left-color: #E30613; }
        .card-obras { border-left-color: #FFD700; background-color: #222; color: #fff; }
        .card-recital { border-left-color: #9b59b6; }
        
        .date-badge {
            font-weight: bold;
            font-size: 0.9em;
            text-transform: uppercase;
            color: #888;
        }
        .card-obras .date-badge { color: #FFD700; }
        
        .event-title {
            font-size: 1.1em;
            font-weight: 600;
            margin: 5px 0;
        }
        .location-tag {
            font-size: 0.8em;
            opacity: 0.8;
        }
        
        /* ALERT STYLES */
        .alert-box {
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
            font-weight: bold;
        }
        .alert-red { background-color: #ffeebe; border: 2px solid #E30613; color: #E30613; }
        .alert-green { background-color: #d4edda; border: 1px solid #c3e6cb; color: #155724; }
        .alert-gray { background-color: #e2e3e5; color: #383d41; }
        </style>
    """, unsafe_allow_html=True)

    # --- DASHBOARD LOGIC ---
    nearby = False
    details = ""
    if future:
        diff = (future[0]['obj_date'] - current_date).days
        if diff <= 3:
            nearby = True
            details = f"{future[0]['lugar']}: {future[0]['evento']}"

    st.divider()
    
    # Modern Alert
    if nearby:
        st.markdown(f"""
            <div class="alert-box alert-red">
                � ALERTA DE TRÁFICO <br>
                <span style="font-weight:normal">{details}</span> <br>
                En {diff} días
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
            
            date_pretty = d_obj.strftime("%d/%m/%Y")
            
            st.markdown(f"""
                <div class="{card_class}">
                    <div class="date-badge">{date_pretty} • {day_label}</div>
                    <div class="event-title">{e['evento']}</div>
                    <div class="location-tag">📍 {e['lugar']}</div>
                </div>
            """, unsafe_allow_html=True)

    else:
        st.caption("No hay eventos programados en el radar.")

if __name__ == "__main__":
    main()
