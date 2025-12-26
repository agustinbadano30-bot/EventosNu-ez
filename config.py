from datetime import datetime

# --- CONFIGURACIÓN PRINCIPAL ---

# 1. FECHA DE REFERENCIA
# False = Usar fecha real del sistema (datetime.now())
# datetime(...) = Usar fecha simulada (Ideal para pruebas)
FAKE_TODAY = datetime(2025, 9, 1) 
FAKE_TODAY = False 

# 2. FILTRO FECHA RIVER
# False = Mostrar desde "hoy" en adelante (según FECHA DE REFERENCIA)
# datetime(...) = Forzar inicio de historial (ej: 1 de Enero)
RIVER_START_DATE = False 
# RIVER_START_DATE = datetime(2025, 1, 1)

# --- CONSTANTES ---
MONTHS_ES = {
    "ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6,
    "jul": 7, "ago": 8, "sep": 9, "oct": 10, "nov": 11, "dic": 12,
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12 
}

# 3. GOOGLE SHEET (CSV)
# Link público "Publish to Web" -> CSV
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQVbJOia6Aaoa7T7r-7eUEZ0laciKatu07PVuPa61FDLyhfaNyrzLVofMbBzYUroFufae-VhQTIvA6O/pub?output=csv"

# 4. RECITALES MONUMENTAL (Hardcoded / Fallback)
# Fuente: Web Search (LiveNation/Songkick blocked)
MONUMENTAL_CONCERTS = [
    {"fecha": "2025-10-04", "evento": "Kendrick Lamar", "lugar": "Monumental (Recital)"},
    {"fecha": "2025-10-05", "evento": "Airbag", "lugar": "Monumental (Recital)"},
    {"fecha": "2025-11-07", "evento": "Dua Lipa", "lugar": "Monumental (Recital)"},
    {"fecha": "2025-11-08", "evento": "Dua Lipa", "lugar": "Monumental (Recital)"},
    {"fecha": "2025-11-15", "evento": "Oasis", "lugar": "Monumental (Recital)"},
    {"fecha": "2025-11-16", "evento": "Oasis", "lugar": "Monumental (Recital)"},
    {"fecha": "2025-12-12", "evento": "María Becerra", "lugar": "Monumental (Recital)"},
    {"fecha": "2025-12-13", "evento": "María Becerra", "lugar": "Monumental (Recital)"},
    {"fecha": "2025-12-17", "evento": "Airbag (Cierre)", "lugar": "Monumental (Recital)"},
    {"fecha": "2025-12-18", "evento": "Airbag (Cierre)", "lugar": "Monumental (Recital)"},
    # 2026
    {"fecha": "2026-02-13", "evento": "Bad Bunny", "lugar": "Monumental (Recital)"},
    {"fecha": "2026-02-14", "evento": "Bad Bunny", "lugar": "Monumental (Recital)"},
    {"fecha": "2026-02-15", "evento": "Bad Bunny", "lugar": "Monumental (Recital)"},
    {"fecha": "2026-03-23", "evento": "AC/DC", "lugar": "Monumental (Recital)"},
    {"fecha": "2026-03-27", "evento": "AC/DC", "lugar": "Monumental (Recital)"},
    {"fecha": "2026-03-31", "evento": "AC/DC", "lugar": "Monumental (Recital)"},
    {"fecha": "2026-06-06", "evento": "Lali", "lugar": "Monumental (Recital)"},
]
