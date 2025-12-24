
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

MONTHS_ES = {
    "ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6,
    "jul": 7, "ago": 8, "sep": 9, "oct": 10, "nov": 11, "dic": 12,
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12 
}

def get_soup(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return BeautifulSoup(response.content, 'html.parser')
    except Exception as e:
        print(f"Request error: {e}")
    return None

def parse_obras_date(text, year_context=2025):
    if not text: return None
    text = text.lower()
    
    day_match = re.search(r'(\d{1,2})', text)
    if day_match:
        try:
            day = int(day_match.group(1))
            
            sorted_months = sorted(MONTHS_ES.keys(), key=len, reverse=True)
            for m_key in sorted_months:
                 if m_key in text:
                     month = MONTHS_ES[m_key]
                     year = year_context
                     y_match = re.search(r'20\d{2}', text)
                     if y_match:
                        year = int(y_match.group(0))
                     
                     return datetime(year, month, day)
        except: pass
    return None

def get_obras_events(year_context=2025):
    events = []
    soup = get_soup("https://estadioobras.com.ar/")
    if not soup: 
        print("Soup is None")
        return []
    
    print(f"Found {len(soup.find_all('h3'))} h3 tags")
    
    for i, h3 in enumerate(soup.find_all('h3')):
        link = h3.find('a')
        if not link: 
            print(f"h3 #{i} has no link")
            continue
        
        title = link.get_text(strip=True)
        print(f"Checking '{title}'")
        
        card_text = ""
        if h3.parent and h3.parent.parent:
             card_text = h3.parent.parent.get_text(" ", strip=True)
        else:
             card_text = h3.parent.get_text(" ", strip=True)
             
        dt = parse_obras_date(card_text, year_context)
        print(f"  Parsed date: {dt}")
        
        if dt:
            events.append({
                "fecha": dt.strftime("%Y-%m-%d"),
                "evento": title,
                "lugar": "Estadio Obras",
                "obj_date": dt
            })
            
    return events

print("Running scraper...")
events = get_obras_events(2025)
with open("debug_output.txt", "w", encoding="utf-8") as f:
    f.write(f"Found {len(events)} events.\n")
    for e in events:
        f.write(f"E: {e['evento']} -> {e['fecha']}\n")
print(f"Written to debug_output.txt")
