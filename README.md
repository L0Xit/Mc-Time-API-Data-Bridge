# TGM-Adapter

Ein 3-Komponenten System mit Flask Frontend, TGM-Adapter Middleware und Backend API.

## Architektur

```
Frontend (Flask UI) → Middleware (TGM-Adapter) → Backend (API)
     Port 8080              Port 5000            Port 5001
```

## Komponenten

### 1. Frontend (`frontend.py`)
- Flask Web-Interface mit deutschsprachiger Benutzeroberfläche
- Kommuniziert über HTTP-Anfragen mit dem Middleware
- Bietet Funktionen für Benutzerverwaltung und Datenverarbeitung
- Läuft auf Port 8080

### 2. Middleware (`middleware.py`) 
- TGM-Adapter der als Proxy zwischen Frontend und Backend fungiert
- Protokolliert alle Anfragen und fügt Metadaten hinzu
- Behandelt Fehler und Timeouts
- Läuft auf Port 5000

### 3. Backend (`backend.py`)
- Flask API die Datenendpunkte bereitstellt
- Verwaltet Benutzer und verarbeitet Daten
- Läuft auf Port 5001

## Installation

1. Abhängigkeiten installieren:
```bash
pip install -r requirements.txt
```

2. Alle Komponenten starten:
```bash
./start_system.sh
```

Oder manuell einzeln starten:
```bash
# Terminal 1 - Backend
python3 backend.py

# Terminal 2 - Middleware  
python3 middleware.py

# Terminal 3 - Frontend
python3 frontend.py
```

## Verwendung

Nach dem Start können Sie die Anwendung über folgende URLs erreichen:

- **Frontend Web-Interface**: http://localhost:8080
- **Middleware API**: http://localhost:5000/adapter/status
- **Backend API**: http://localhost:5001/api/health

### Frontend Funktionen

- **Dashboard**: Systemübersicht und Status
- **Benutzer**: Anzeigen und Erstellen von Benutzern
- **Daten verarbeiten**: Senden von Daten zur Verarbeitung
- **System Status**: Detaillierte Statusinformationen

## API Endpunkte

### Middleware (Port 5000)
- `GET /adapter/status` - Adapter Status
- `GET /adapter/health` - Health Check (proxied)
- `GET /adapter/users` - Benutzer abrufen (proxied)
- `POST /adapter/users` - Benutzer erstellen (proxied)
- `POST /adapter/data` - Daten verarbeiten (proxied)

### Backend (Port 5001)
- `GET /api/health` - Health Check
- `GET /api/users` - Alle Benutzer
- `POST /api/users` - Neuen Benutzer erstellen
- `GET /api/system` - Systeminformationen
- `POST /api/data` - Daten verarbeiten

## Datenfluss

1. Benutzer interagiert mit dem Frontend (Port 8080)
2. Frontend sendet HTTP-Anfrage an Middleware (Port 5000)
3. Middleware protokolliert Anfrage und leitet sie an Backend weiter (Port 5001)
4. Backend verarbeitet Anfrage und sendet Antwort zurück
5. Middleware fügt Metadaten hinzu und leitet Antwort an Frontend weiter
6. Frontend zeigt Ergebnis dem Benutzer an

## Entwicklung

Jede Komponente kann einzeln entwickelt und getestet werden. Die Middleware fungiert als entkoppelnde Schicht zwischen Frontend und Backend.