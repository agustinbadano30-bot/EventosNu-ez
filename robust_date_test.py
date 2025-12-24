
import re
from datetime import datetime

MONTHS_ES = {
    "ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6,
    "jul": 7, "ago": 8, "sep": 9, "oct": 10, "nov": 11, "dic": 12,
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12 
}

def parse_obras_dates_robust(text, year_context=2025):
    """
    Robustly parses multiple dates associated with a month.
    Supports: "27 y 28 de Diciembre", "27, 28 y 29 de Diciembre", "20 de Enero"
    """
    if not text: return []
    text = text.lower()
    found_dates = []

    # Strategy: Find "de [Month]" and look backwards for numbers
    # Regex to find Month usage:  (?:de\s*)?(MONTH_NAME)
    
    sorted_months = sorted(MONTHS_ES.keys(), key=len, reverse=True)
    month_pattern = "|".join(sorted_months)
    
    # Iterate over all "Month" occurrences
    # We look for "[Number]+ (separated by y/,) ... de [Month]"
    
    # This regex looks for a block ending in a month name
    # It captures the text BEFORE the month to scan for numbers
    # Pattern:  (text_before) (month_name)
    # We use lookahead or just iterate valid months?
    
    # Simpler: Split by month names? No, might lose context.
    
    # 1. Find all month matches with positions
    month_matches = []
    for m in re.finditer(fr'\b({month_pattern})\b', text):
        month_matches.append(m)
        
    last_end = 0
    for m in month_matches:
        month_name = m.group(1)
        start, end = m.span()
        
        # Look at the text immediately preceding this month (up to previous month or start)
        # Limiting to e.g. 50 chars back to avoid false positives from far away text?
        # Usually "27, 28 y 29 de " is close.
        
        snippet_end = start
        snippet_start = max(last_end, start - 50)
        snippet = text[snippet_start:snippet_end]
        
        # Check if "de" is at the end of snippet
        # snippet cleanup
        
        # Find all numbers in this snippet
        # We need to be careful not to pick up "10 años" if it's far back?
        # But "text before month" implies these numbers belong to the month.
        
        # Strict logic: Numbers must be separated by ", " or " y " or " e "
        # Valid pattern from right to left:
        #  "de" (optional)
        #  Number
        #  ( "y" Number | "," Number )*
        
        # Using simple "find all integers" in the immediate preceding text is usually effective enough
        # provided we stop at non-separator characters.
        
        nums = re.findall(r'\d{1,2}', snippet) # Greedy catch all numbers?
        
        # Verify year
        year = year_context
        # Look for year in text AFTER the month?
        year_snippet = text[end:end+20]
        y_match = re.search(r'20\d{2}', year_snippet)
        if y_match:
             year = int(y_match.group(0))
        
        month_val = MONTHS_ES[month_name]
        
        # Add dates
        for day_str in nums:
             d = int(day_str)
             if 1 <= d <= 31:
                 dt = datetime(year, month_val, d)
                 found_dates.append(dt)
                 
        last_end = end

    return found_dates

# Test Cases
cases = [
    "La Kermesse 10 años 27 y 28 de Diciembre 2025",
    "Solo el 15 de Enero",
    "Festival: 10, 11 y 12 de Febrero 2026",
    "Evento raro 31 de Enero y 1 de Febrero", # Multi month!
    "Sin fecha clara"
]

print("Running Robust Tests...")
for c in cases:
    res = parse_obras_dates_robust(c)
    print(f"'{c}' \n  -> {[d.strftime('%Y-%m-%d') for d in res]}")
