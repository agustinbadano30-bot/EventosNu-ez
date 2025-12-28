import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time
import calendar
from config import FAKE_TODAY, RIVER_START_DATE

# --- LOGICA EN BACKEND ---
# Importamos todas las funciones desde api.scrapers
# Nota: Streamlit usa 'cache_data' para persistencia. Como movimos la logica,
# envolveremos la llamada principal aqui.
try:
    from api.scrapers import fetch_all_events, get_weather_data, get_weather_icon
except ImportError:
    # Si ejecutamos desde la raiz, deberia funcionar. 
    # Si no, agregamos path, pero con el __init__.py deberia bastar.
    import sys
    import os
    sys.path.append(os.path.abspath("."))
    from api.scrapers import fetch_all_events, get_weather_data, get_weather_icon

# --- CONFIGURACION PAGINA ---
st.set_page_config(
    page_title="Alerta Nuñez", 
    page_icon="🚦", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- ESTILOS CSS ---
def local_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
            color: #1f2937;
        }

        /* HEADER */
        .header-container {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 1rem;
        }
        .app-title {
            font-size: 1.8rem;
            font-weight: 800;
            color: #111827;
            margin: 0;
            line-height: 1.2;
        }
        .app-subtitle {
            font-size: 0.9rem;
            color: #6b7280;
            margin-top: 0.2rem;
        }

        /* METRICS & ALERTS */
        .alert-box {
            padding: 1rem;
            border-radius: 12px;
            text-align: center;
            margin-bottom: 1.5rem;
            border: 1px solid transparent;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        }
        .alert-red { 
            background: linear-gradient(to bottom right, #fee2e2, #fecaca); 
            color: #991b1b; 
            border-color: #fca5a5; 
        }
        .alert-green { 
            background: linear-gradient(to bottom right, #d1fae5, #a7f3d0); 
            color: #065f46; 
            border-color: #6ee7b7; 
        }
        .alert-gray { background-color: #f3f4f6; color: #374151; border-color: #e5e7eb; }

        .traffic-btn {
            display: inline-block;
            margin-top: 0.8rem;
            padding: 0.4rem 1rem;
            background-color: #ffffff;
            color: #991b1b;
            text-decoration: none;
            border-radius: 8px;
            font-size: 0.85rem;
            font-weight: 600;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
            transition: transform 0.1s;
        }
        .traffic-btn:hover { transform: scale(1.02); }

        /* CARDS */
        .event-card {
            background: white;
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 0.8rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            border-left: 5px solid #ccc;
            transition: transform 0.1s;
        }
        .event-card:hover { transform: translateY(-2px); }

        /* Card Types */
        .type-futbol { 
            border-left-color: #e11d48;
            background-color: #ffffff;
        }
        
        .type-recital { 
            background-color: #0f0f0f !important;
            border: 1px solid #333;
            border-left: 5px solid #ef4444;
        }
        .type-recital .event-name { color: #f9fafb !important; }
        .type-recital .event-location { color: #9ca3af !important; }
        .type-recital .pill-date { 
            background-color: #450a0a; 
            color: #fca5a5; 
            border: 1px solid #7f1d1d;
        }
        .type-recital .pill-today {
            background-color: #7f1d1d;
            color: #fecaca;
            border: 1px solid #991b1b;
        }
        
        .type-obras {
            background-color: #1a1a1a !important;
            border: 1px solid #333;
            border-left: 5px solid #fbbf24;
        }
        .type-obras .event-name { color: #f3f4f6 !important; }
        .type-obras .event-location { color: #d1d5db !important; }
        .type-obras .pill-date { 
            background-color: rgba(251, 191, 36, 0.2); 
            color: #fbbf24; 
            border: 1px solid rgba(251, 191, 36, 0.3);
        }
        .type-obras .pill-today {
            background-color: rgba(251, 191, 36, 0.3);
            color: #fbbf24;
            border: 1px solid #fbbf24;
        }

        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.3rem;
        }
        .pill {
            padding: 0.15rem 0.5rem;
            border-radius: 9999px;
            font-size: 0.7rem;
            font-weight: 600;
            text-transform: uppercase;
        }
        .pill-date { background-color: #f3f4f6; color: #4b5563; }
        .pill-today { background-color: #fee2e2; color: #991b1b; } 

        .event-name {
            font-size: 1.1rem;
            font-weight: 700;
            color: #111827;
            margin-bottom: 0.2rem;
        }
        .event-location {
            font-size: 0.85rem;
            color: #6b7280;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .weather-badge {
            display: inline-block;
            padding: 0.15rem 0.5rem;
            background-color: rgba(59, 130, 246, 0.1);
            color: #2563eb;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 600;
            margin-left: auto;
        }
        
        /* Weather on dark cards */
        .type-obras .weather-badge,
        .type-recital .weather-badge {
            background-color: rgba(59, 130, 246, 0.2);
            color: #60a5fa;
        }

        /* CALENDAR GRID SIMPLE */
        .calendar-grid {
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: 4px;
            margin-top: 1rem;
            font-size: 0.8rem;
        }
        .cal-day {
            aspect-ratio: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            background-color: #f9fafb;
            border-radius: 6px;
            color: #9ca3af;
        }
        .cal-day.active { background-color: #fee2e2; color: #991b1b; font-weight: bold; border: 1px solid #fecaca; cursor: pointer; }
        .cal-day.today { border: 2px solid #3b82f6; } /* Highlight current day */

        /* FOOTER */
        .footer {
            margin-top: 3rem;
            text-align: center;
            font-size: 0.75rem;
            color: #9ca3af;
        }
        </style>
    """, unsafe_allow_html=True)

# --- CACHE WRAPPERS ---
@st.cache_data(ttl=3600, show_spinner=False)
def load_data():
    return fetch_all_events(), get_weather_data()

# --- MAIN APP ---
def main():
    local_css()

    # No sidebar filters - removed per user request

    # DATA LOADING
    with st.spinner("Sincronizando con la matrix..."):
        all_events, weather_data = load_data()
        
    # --- TIME HANDLING ---
    if FAKE_TODAY:
        current_date = FAKE_TODAY
        st.markdown(f"<div style='background:#fef3c7; color:#92400e; padding:0.5rem; text-align:center; font-size:0.8rem; border-radius:6px; margin-bottom:1rem;'>⚠️ MODO SIMULACIÓN: {current_date.strftime('%d/%m/%Y')}</div>", unsafe_allow_html=True)
    else:
        # Ajuste nocturno: si son las 2 AM, sigue siendo el "dia anterior" operativa o visualmente?
        # Mantengamos la logica simple: dia real.
        now = datetime.now()
        current_date = datetime(now.year, now.month, now.day)

    # PROCESS EVENTS
    upcoming = []
    # Filter by date only first
    for e in all_events:
        threshold = current_date
        if e.get('lugar') == "Monumental" and RIVER_START_DATE:
            threshold = RIVER_START_DATE
        
        if e['obj_date'] >= threshold:
            # Enrich with calculated fields
            e['days_diff'] = (e['obj_date'] - current_date).days
            upcoming.append(e)

    # Sort
    upcoming.sort(key=lambda x: x['obj_date'])

    # No filtering - show all events
    filtered_events = upcoming

    # --- HEADER ---
    c1, c2 = st.columns([0.85, 0.15])
    with c1:
        st.markdown(f"""
            <div class="header-container">
                <div>
                    <h1 class="app-title">🚦 Alerta Nuñez</h1>
                    <p class="app-subtitle">Monitoreo inteligente de trafico y eventos en Nuñez.</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
    with c2:
        if st.button("🔄", help="Actualizar"):
            st.cache_data.clear()
            st.rerun()

    # --- TRAFFIC ALERT LOGIC ---
    # Alertamos para CUALQUIER evento de alto impacto en los proximos 2 dias
    # (Monumental, River, Obras)
    
    start_alert = False
    alert_event = None
    
    # Buscamos el proximo evento en los proximos 2 dias (hoy, mañana, pasado)
    for e in upcoming:
        if e['days_diff'] <= 2:
            # Alertar para Monumental (River o Recitales) y Obras
            if e.get('lugar') in ["Monumental", "Estadio Obras"] or "River" in e.get('evento', ''):
                start_alert = True
                alert_event = e
                break 
    
    if start_alert:
        days = alert_event['days_diff']
        when = "HOY" if days == 0 else ("MAÑANA" if days == 1 else f"En {days} días")
        st.markdown(f"""
            <div class="alert-box alert-red">
                <div style="font-size:1.5rem; margin-bottom:0.5rem;">🚨 ALERTA DE TRÁFICO</div>
                <div style="font-weight:600; font-size:1.1rem;">{alert_event['evento']}</div>
                <div>{when} • {alert_event['lugar']}</div>
                <a href="https://www.google.com/maps/@-34.545,-58.449,15z/data=!5m1!1e1" target="_blank" class="traffic-btn">
                    🗺️ Ver Mapa de Tráfico
                </a>
            </div>
        """, unsafe_allow_html=True)
    elif upcoming:
        st.markdown("""
            <div class="alert-box alert-green">
                <div style="font-size:1.2rem; margin-bottom:0.2rem;">🟢 TRÁFICO FLUIDO</div>
                <span style="opacity:0.8">Disfruta la calma mientras puedas.</span>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div class="alert-box alert-gray">
                ⚪ TODO TRANQUILO
            </div>
        """, unsafe_allow_html=True)

    # --- AGENDA DE EVENTOS ---
    st.divider()
    st.subheader("Agenda del Barrio")
    
    if not filtered_events:
        st.info("No hay eventos programados en el radar.")
    
    current_month = -1
    
    for e in filtered_events:
        # Month headers
        m = e['obj_date'].month
        if m != current_month:
            month_name = e['obj_date'].strftime("%B").capitalize()
            # Traducir simple si no tenemos locale configurado
            meses = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
            if 1 <= m <= 12: month_name = meses[m]
            
            st.markdown(f"### {month_name} {e['obj_date'].year}")
            current_month = m

        # Data prep
        d_obj = e['obj_date']
        d_str = d_obj.strftime("%Y-%m-%d")
        
        # Weather with better styling
        w_html = ""
        if d_str in weather_data:
            w = weather_data[d_str]
            icon = get_weather_icon(w['code'])
            # Use a badge style for better visibility
            w_html = f"<span class='weather-badge'>{icon} {w['max']}°C</span>"

        # Badge properties
        days = e['days_diff']
        pill_class = "pill-today" if days == 0 else "pill-date"
        day_text = "HOY" if days == 0 else ("MAÑANA" if days == 1 else f"{d_obj.day} {month_name[:3]}")
        
        # Typo CSS
        tipo = e.get('tipo', 'Otros').lower()
        if "futbol" in tipo: css_type = "type-futbol"
        elif "recital" in tipo: css_type = "type-recital"
        elif "obras" in tipo: css_type = "type-obras"
        else: css_type = ""

        st.markdown(f"""
            <div class="event-card {css_type}">
                <div class="card-header">
                    <span class="pill {pill_class}">{day_text}</span>
                </div>
                <div class="event-name">{e['evento']}</div>
                <div class="event-location">📍 {e['lugar']} {w_html}</div>
            </div>
        """, unsafe_allow_html=True)

    # --- FOOTER ---
    st.markdown(f"""
        <div class="footer">
            Actualizado: {datetime.now().strftime('%H:%M:%S')} <br>
            Desarrollado con ❤️ para los vecinos.
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
