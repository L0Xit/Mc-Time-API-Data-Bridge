# Middleware Integration Guide

Diese Datei beschreibt, wie das Frontend für die Middleware-Anbindung vorbereitet ist.

## Aktueller Status
Das Frontend läuft im **Dummy-Modus** mit Testdaten für die Entwicklung der Benutzeroberfläche.

## Middleware-Integration

### 1. Hauptkomponente: `MiddlewareConnector`
Datei: `api_connector.py`

Die Klasse `MiddlewareConnector` ist die zentrale Schnittstelle zur Middleware und bietet folgende Methoden:

#### Hauptmethoden:
- `get_companies()` - Holt Firmenliste
- `get_employees(company_filter)` - Holt Mitarbeiterliste  
- `get_time_data(company, employee, date_from, date_to)` - Holt Zeiterfassungsdaten
- `get_connection_status()` - Status der Middleware-Verbindung
- `ping_middleware()` - Testet die Verbindung

#### Produktions-Modus aktivieren:
```python
middleware_connector.switch_to_production_mode("http://your-middleware-url/api")
```

### 2. Benötigte Middleware-Endpunkte

Das Frontend erwartet folgende REST-Endpunkte von der Middleware:

#### Gesundheitscheck:
```
GET /api/health
GET /api/ping
```

#### Datenabfrage:
```
GET /api/companies
→ Rückgabe: ["Firma A", "Firma B", ...]

GET /api/employees?company=<firma>
→ Rückgabe: [{"id": 1, "name": "Max Mustermann", "company": "Firma A"}, ...]

GET /api/timedata?company=<firma>&employee=<name>&date_from=<datum>&date_to=<datum>
→ Rückgabe: [
    {
        "date": "2025-01-01",
        "employee": "Max Mustermann", 
        "hours": 8.0,
        "project": "Projekt Alpha",
        "company": "Firma A",
        "description": "Beschreibung",
        "start_time": "09:00",
        "end_time": "17:00"
    }
]
```

### 3. Integration Steps

#### Schritt 1: Middleware URL konfigurieren
```python
# In app.py oder als Umgebungsvariable
MIDDLEWARE_URL = "http://localhost:8080/api"
middleware_connector = MiddlewareConnector(MIDDLEWARE_URL)
```

#### Schritt 2: Produktions-Modus aktivieren
```python
# Wenn Middleware verfügbar ist
success = middleware_connector.switch_to_production_mode(MIDDLEWARE_URL)
if success:
    print("Middleware verbunden!")
else:
    print("Middleware-Verbindung fehlgeschlagen - verwende Dummy-Daten")
```

#### Schritt 3: Fehlerbehandlung implementieren
Die Methoden in `MiddlewareConnector` haben bereits Fallback-Mechanismen:
- Bei Verbindungsfehlern wird automatisch auf Dummy-Daten umgeschaltet
- Alle Methoden haben try/catch-Blöcke vorbereitet

### 4. Erweiterte Konfiguration

#### Umgebungsvariablen:
```bash
MIDDLEWARE_URL=http://localhost:8080/api
MIDDLEWARE_TIMEOUT=30
USE_DUMMY_DATA=false
```

#### Flask-Konfiguration:
```python
app.config['MIDDLEWARE_URL'] = os.environ.get('MIDDLEWARE_URL', 'http://localhost:8080/api')
app.config['MIDDLEWARE_TIMEOUT'] = int(os.environ.get('MIDDLEWARE_TIMEOUT', 30))
```

### 5. Testing

#### Dummy-Modus testen:
```bash
python app.py
# Gehe zu http://localhost:5000
# Alle Funktionen sollten mit Testdaten funktionieren
```

#### Middleware-Verbindung testen:
- Gehe zu http://localhost:5000/api_config
- Klicke auf "Middleware-Verbindung testen"

### 6. Frontend-Endpunkte

Das Frontend stellt folgende Endpunkte bereit:

- `/` - Hauptseite mit Datenfilterung
- `/api_config` - Middleware-Konfiguration
- `/api/middleware/status` - Middleware-Status (JSON)
- `/api/middleware/ping` - Verbindungstest (JSON)
- `/api/data` - Gefilterte Zeitdaten (JSON)
- `/download_csv` - CSV-Export

### 7. Anpassungen für neue Middleware

Falls die Middleware andere Datenstrukturen verwendet:

1. Passe die Methoden in `MiddlewareConnector` an
2. Aktualisiere die Frontend-Templates falls nötig
3. Erweitere die CSV-Export-Funktion bei Bedarf

Das Frontend ist flexibel gestaltet und kann einfach an verschiedene Middleware-Implementierungen angepasst werden.