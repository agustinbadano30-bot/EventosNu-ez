
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
    
    # Improved Logic: Prioritize "DD de Month" or "DD ... Month"
    # We construct a big regex for "(\d{1,2}) ... (MonthName)"
    
    # 1. Try Specific Pattern: "27 de Diciembre" or "27 y 28 de Diciembre"
    # match (\d{1,2}) then maybe " y \d" then " de " then Month
    
    # Iterate months to build regex part? Or just find "de (Month)"
    
    sorted_months = sorted(MONTHS_ES.keys(), key=len, reverse=True)
    month_regex = "|".join(sorted_months)
    
    # Pattern: Number ... (optional "de") ... Month
    # We want the number closest to the month? 
    # Or just `(\d{1,2})\s*(?:y\s*\d{1,2})?\s*(?:de)?\s*(\w+)` and check if group 2 is a month.
    
    matches = re.finditer(r'(\d{1,2})\s*(?:y\s*\d{1,2})?\s*(?:de)?\s*([a-záéíóúñ]+)', text)
    
    for m in matches:
        day_str = m.group(1)
        month_str = m.group(2)
        
        if month_str in MONTHS_ES:
             day = int(day_str)
             month = MONTHS_ES[month_str]
             
             # Extract year
             year = year_context
             y_match = re.search(r'20\d{2}', text)
             if y_match:
                 year = int(y_match.group(0))
             
             return datetime(year, month, day)

    # Fallback to old behavior if needed, or just fail safely.
    # The old behavior was: find FIRST digit, then find ANY month.
    # That caused the "10 años" bug.
    # Maybe we only fallback if no "Month" was found?
    
    return None

# Test cases based on what I saw
texts = [
    "La Kermesse «10 años» 27 y 28 de Diciembre 2025 LEER MÁS",
    "El Plan de la Mariposa 17 y 18 de Diciembre 2025 LEER MÁS",
    "El Mató a un Policía Motorizado 20 de Diciembre 2025 LEER MÁS",
    "Event with just month: Diciembre 2025", # Should fail
    "Just date: 27 de Diciembre" # Should default year?
]

print("Running tests...")
for t in texts:
    print(f"'{t}' -> {parse_obras_date(t)}")
