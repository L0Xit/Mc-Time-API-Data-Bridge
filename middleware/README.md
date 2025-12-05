# Adapter Middleware - Dokumentation

## Übersicht

Die **Adapter Middleware** ist die Zwischenschicht zwischen dem Backend (McTime API) und dem Frontend (Flask-Anwendung). Sie wurde so entwickelt, dass weder Backend noch Frontend geändert werden müssen.

```
┌─────────────────┐     ┌─────────────────────┐     ┌─────────────────┐
│                 │     │                     │     │                 │
│    Frontend     │◄───►│  Adapter Middleware │◄───►│    Backend      │
│    (Flask)      │     │                     │     │   (McTime API)  │
│                 │     │                     │     │                 │
└─────────────────┘     └─────────────────────┘     └─────────────────┘
```

## Funktionen

### 1. API-Key Authentifizierung
- Sichere Verwaltung des API-Keys über Umgebungsvariablen
- Validierung der Authentifizierung

### 2. Stabiler Request-Ablauf & Fehlerhandling
- Einheitliches Error-Handling für alle API-Aufrufe
- Spezifische Fehlerklassen für verschiedene Szenarien
- Logging aller Fehler

### 3. JSON → CSV Verarbeitung
- Transformation von API-Daten für das Frontend
- CSV-Export für Zeiteinträge
- Flexible Formatierungsoptionen

### 4. Zeit- & Abwesenheitsdaten abrufen
- Zeiteinträge mit Filteroptionen
- Automatische Stundenberechnung
- Pausenformatierung

### 5. McTime Login & Mitarbeiterverwaltung
- Mitarbeiterliste abrufen
- E-Mail-Adressen abfragen
- Organisationen verwalten

### 6. Rate Limiting
- Schutz vor API-Überlastung
- Konfigurierbares Limit
- Automatische Wartezeit-Berechnung

## Installation

Die Middleware ist bereits im Projekt integriert. Keine zusätzliche Installation nötig.

## Verwendung

### Option 1: Direkte Verwendung der Middleware

```python
from middleware import AdapterMiddleware

# Initialisierung
middleware = AdapterMiddleware()

# Mitarbeiter abrufen
employees = middleware.get_employees()

# Zeitdaten abrufen
time_entries = middleware.get_time_entries(
    employee_id="123",
    date_from="01.01.2025",
    date_to="31.01.2025"
)

# Als CSV exportieren
csv_data = middleware.export_to_csv(time_entries)
```

### Option 2: Verwendung der Integration (für Flask)

```python
from middleware.integration import MiddlewareIntegration

integration = MiddlewareIntegration()

# Formulardaten holen (kompatibel mit backend_service)
form_data = integration.get_form_data()

# Formular-Anfrage verarbeiten
result = integration.process_form_request({
    "firma": "org_id",
    "mitarbeiter": "emp_id",
    "von": "01.01.2025",
    "bis": "31.01.2025"
})
```

### Option 3: Singleton-Pattern

```python
from middleware import get_middleware
from middleware.integration import get_integration

# Middleware Singleton
middleware = get_middleware()

# Integration Singleton
integration = get_integration()
```

## Dateistruktur

```
middleware/
├── __init__.py          # Modul-Exports
├── adapter.py           # Hauptklasse AdapterMiddleware
├── transformer.py       # Daten-Transformation (JSON ↔ CSV)
├── rate_limiter.py      # Rate Limiting
├── error_handler.py     # Fehlerbehandlung
├── integration.py       # Frontend-Integration
└── README.md           # Diese Dokumentation
```

## Komponenten

### AdapterMiddleware (adapter.py)
Die Hauptklasse die alle Funktionen bereitstellt:
- `get_organizations()` - Firmen abrufen
- `get_employees()` - Mitarbeiter abrufen
- `get_time_entries()` - Zeiteinträge abrufen
- `export_to_csv()` - CSV-Export
- `get_form_data()` - Formulardaten
- `process_form_request()` - Formular verarbeiten

### DataTransformer (transformer.py)
Transformiert Daten zwischen Formaten:
- `transform_organizations()` - Organisationen formatieren
- `transform_employees()` - Mitarbeiter formatieren
- `transform_time_entries()` - Zeiteinträge formatieren
- `to_csv()` - In CSV konvertieren
- `from_csv()` - Aus CSV konvertieren

### RateLimiter (rate_limiter.py)
Begrenzt API-Anfragen:
- `check()` - Prüft ob Request erlaubt
- `record_request()` - Zeichnet Request auf
- `get_remaining()` - Verbleibende Requests
- `get_wait_time()` - Wartezeit

### ErrorHandler (error_handler.py)
Einheitliches Fehlerhandling:
- `handle_error()` - Fehler behandeln
- `log_error()` - Fehler loggen
- `create_error_response()` - Response erstellen

## Fehler-Codes

| Code | Beschreibung |
|------|-------------|
| API_KEY_MISSING | API-Key nicht konfiguriert |
| API_KEY_INVALID | API-Key ungültig |
| RATE_LIMIT_EXCEEDED | Rate Limit erreicht |
| INVALID_DATE_FORMAT | Ungültiges Datumsformat |
| API_CONNECTION_ERROR | Verbindung zur API fehlgeschlagen |
| INTERNAL_ERROR | Interner Fehler |

## Konfiguration

Die Middleware liest folgende Umgebungsvariablen:

```env
# .env Datei
MCTIME_API_KEY=your-api-key-here
```

## Beispiel: Kompletter Workflow

```python
from middleware import AdapterMiddleware

# 1. Middleware initialisieren
middleware = AdapterMiddleware()

# 2. Verbindung prüfen
status = middleware.get_connection_status()
print(f"Verbunden: {status['connected']}")

# 3. Organisationen laden
orgs = middleware.get_organizations()
print(f"Gefundene Firmen: {len(orgs)}")

# 4. Mitarbeiter laden
employees = middleware.get_employees()
print(f"Gefundene Mitarbeiter: {len(employees)}")

# 5. Zeiteinträge abrufen
entries = middleware.get_time_entries(
    employee_id=employees[0]['id'],
    date_from="01.12.2025",
    date_to="05.12.2025"
)
print(f"Zeiteinträge: {len(entries)}")

# 6. Als CSV exportieren
csv_output = middleware.export_to_csv(entries)
print(csv_output)
```

## Wichtige Herausforderungen

### Rate Limits
- Die McTime API hat ein Rate Limit
- Die Middleware handhabt dies automatisch
- Bei Überschreitung wird eine Warnung ausgegeben

### Komplexe Zeiteintragsstrukturen
- Die API liefert verschachtelte JSON-Strukturen
- Der DataTransformer flacht diese für das Frontend ab
- Pausenzeiten werden automatisch berechnet

## Kompatibilität

Die Middleware ist so entwickelt, dass:
- ✅ Backend (api_handler.py) unverändert bleibt
- ✅ Frontend (app.py) unverändert bleibt
- ✅ Optional als Zwischenschicht verwendet werden kann
- ✅ Fallback zum Original-Backend bei Fehlern
