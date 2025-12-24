
from app import parse_obras_dates, get_obras_events

print("=== Testing parse_obras_dates ===")

test_cases = [
    "La Kermesse 10 años 27 y 28 de Diciembre 2025",
    "Solo el 15 de Enero",
    "Festival: 10, 11 y 12 de Febrero 2026",
    "Evento raro 31 de Enero y 1 de Febrero",
]

for case in test_cases:
    dates = parse_obras_dates(case)
    print(f"'{case}'")
    print(f"  -> {[d.strftime('%Y-%m-%d') for d in dates]}")
    print()

print("=== Testing get_obras_events (live scrape) ===")
events = get_obras_events(2025)
print(f"Found {len(events)} events total.")
for e in events:
    print(f"  {e['fecha']} - {e['evento']}")
