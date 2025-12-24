
import re
from datetime import datetime

MONTHS_ES = {
    "ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6,
    "jul": 7, "ago": 8, "sep": 9, "oct": 10, "nov": 11, "dic": 12,
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12 
}

def parse_obras_date(text, year_context=2025):
    if not text: return None
    text = text.lower()
    
    matches = re.finditer(r'(\d{1,2})\s*(?:y\s*\d{1,2})?\s*(?:de)?\s*([a-záéíóúñ]+)', text)
    
    found_dates = []
    
    for m in matches:
        day_str = m.group(1)
        month_str = m.group(2)
        
        if month_str in MONTHS_ES:
             day = int(day_str)
             month = MONTHS_ES[month_str]
             year = year_context
             y_match = re.search(r'20\d{2}', text)
             if y_match:
                 year = int(y_match.group(0))
             
             found_dates.append(datetime(year, month, day))
             # Current logic returns immediately!
             return datetime(year, month, day)

    return None

text = "La Kermesse «10 años» 27 y 28 de Diciembre 2025 LEER MÁS"
dt = parse_obras_date(text)
print(f"Parsed: {dt}")
if isinstance(dt, list) or (dt and dt.day == 27):
    print("Confirmed: Returns single date (27). Missing 28.")
