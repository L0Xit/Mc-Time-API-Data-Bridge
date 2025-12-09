# McTime API Data Bridge

> Ein modernes Dashboard zur Zeiterfassungsverwaltung mit McTime API Integration

## 🚀 Features

- **Zeiterfassung** - Automatischer Abruf und Anzeige von Arbeitszeitdaten
- **Multi-Mitarbeiter** - Unterstützt 500+ Mitarbeiter mit skalierbarer UI
- **Charts & Statistiken** - Visuelle Auswertungen mit interaktiven Diagrammen
- **E-Mail Export** - Zeitdaten direkt per E-Mail versenden
- **Performance** - Parallele API-Aufrufe und Caching für schnelle Ladezeiten

## 📁 Projektstruktur

```
Mc-Time-API-Data-Bridge/
├── backend/                    # Backend-Layer (McTime API Kommunikation)
│   ├── api_handler.py         # Haupt-API-Handler
│   ├── client.py              # HTTP Client
│   └── modules/               # API-Module
│       ├── employee_list.py   # Mitarbeiterliste
│       ├── mail.py            # E-Mail Funktionen
│       ├── times.py           # Zeiterfassung
│       └── user_id.py         # Benutzer-IDs
│
├── frontend/                   # Frontend-Layer (Flask Web-App)
│   ├── app.py                 # Flask Application
│   ├── api_connector.py       # Frontend API Connector
│   ├── static/                # CSS, JS, Assets
│   └── templates/             # HTML Templates
│
├── middleware/                 # Middleware-Layer (Business Logic)
│   ├── auth.py                # Authentifizierung
│   ├── core.py                # Kern-Middleware
│   ├── request_handler.py     # Request Processing
│   └── modules/               # Middleware-Module
│       ├── employee_manager.py
│       ├── mail_manager.py
│       └── time_manager.py
│
├── config/                     # Konfiguration (NEU)
│   ├── __init__.py
│   └── settings.py            # Zentrale Einstellungen
│
├── services/                   # Standalone Services (NEU)
│   ├── __init__.py
│   └── webhook_email.py       # E-Mail Webhook Service
│
├── tests/                      # Unit Tests (NEU)
│   ├── __init__.py
│   └── test_env.py            # Environment Tests
│
├── .env.example               # Beispiel-Umgebungsvariablen
├── requirements.txt           # Python Dependencies
├── QUICKSTART.md              # Schnellstart-Anleitung
└── README.md                  # Diese Datei
```

## 🛠️ Installation

1. **Repository klonen**
   ```bash
   git clone https://github.com/L0Xit/Mc-Time-API-Data-Bridge.git
   cd Mc-Time-API-Data-Bridge
   ```

2. **Virtual Environment erstellen**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   ```

3. **Dependencies installieren**
   ```bash
   pip install -r requirements.txt
   ```

4. **Umgebungsvariablen konfigurieren**
   ```bash
   copy .env.example .env
   # .env Datei mit eigenen Werten ausfüllen
   ```

5. **Server starten**
   ```bash
   cd frontend
   python app.py
   ```

6. **Browser öffnen**
   ```
   http://127.0.0.1:5000
   ```

## ⚙️ Konfiguration

Alle Einstellungen in `.env`:

| Variable | Beschreibung |
|----------|-------------|
| `MCTIME_API_KEY` | McTime API Schlüssel |
| `SMTP_SERVER` | SMTP Server Adresse |
| `SMTP_PORT` | SMTP Port (Standard: 587) |
| `SMTP_USERNAME` | SMTP Benutzername |
| `SMTP_PASSWORD` | SMTP Passwort |
| `SENDER_EMAIL` | Absender E-Mail |

## 🏗️ Architektur

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Frontend  │────▶│  Middleware  │────▶│   Backend   │
│   (Flask)   │     │  (Business)  │     │ (McTime API)│
└─────────────┘     └──────────────┘     └─────────────┘
```

- **Frontend**: Web-Interface, Templates, User Interaction
- **Middleware**: Geschäftslogik, Caching, Datenverarbeitung
- **Backend**: API-Kommunikation, Datenabfragen

## 📄 Lizenz

Proprietär - DiploTGM / Infocom GmbH

