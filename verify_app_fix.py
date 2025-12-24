
from app import parse_obras_date, MONTHS_ES
from datetime import datetime

print("Verifying app.py logic...")

# 1. The Failing Case
text_fail = "La Kermesse «10 años» 27 y 28 de Diciembre 2025 LEER MÁS"
dt = parse_obras_date(text_fail)
print(f"CASE 1 (Target: 27 Dec): {dt}")

if dt and dt.day == 27 and dt.month == 12:
    print("PASS: Correctly ignored '10' and found '27'")
else:
    print("FAIL: Still broken")

# 2. Standard Case
text_std = "El Mató a un Policía Motorizado 20 de Diciembre 2025 LEER MÁS"
dt2 = parse_obras_date(text_std)
print(f"CASE 2 (Target: 20 Dec): {dt2}")

if dt2 and dt2.day == 20:
     print("PASS: Standard case working")
else:
     print("FAIL: Standard case broken")
