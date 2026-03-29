# Mc-Time API Data Bridge

**Version 2.1 - Stabile Version mit erweitertem Charting und Bugfixes**

Ein modernes Dashboard zur Zeiterfassungsverwaltung, das direkt mit der McTime API integriert ist. Entwickelt für die HTL Spengergasse, 5. Jahrgang, als Abschlussprojekt.

## 🚀 Features

- **Dynamisches Dashboard**: Echtzeit-Überblick über Zeiterfassungsdaten.
- **Multi-Mitarbeiter-Unterstützung**: Skalierbare Architektur für die Verarbeitung von Daten von über 500 Mitarbeitern.
- **Interaktive Charts & Statistiken**: Detaillierte visuelle Auswertungen mit Chart.js, inklusive Filterung nach Monat, Quartal, Jahr und benutzerdefinierten Zeiträumen.
- **Asynchroner E-Mail-Export**: Versenden von Zeitdaten-Berichten per E-Mail, ohne die UI zu blockieren.
- **Performance-Optimierung**: Parallele API-Aufrufe und serverseitiges Caching zur Minimierung von Ladezeiten.
- **Hybride Architektur**: Nutzt einen robusten Backend-Service mit einem Middleware-Fallback für maximale Zuverlässigkeit.
- **Sicherheits-Features**: Schutz durch API-Key-Authentifizierung und Rate Limiting.

## 🛠️ Technische Dokumentation

### Architektur
Das Projekt folgt einer 3-Tier-Architektur:

1.  **Frontend (`/frontend`)**: Eine Flask-basierte Webanwendung, die das User Interface (UI) bereitstellt. Sie kommuniziert über API-Endpunkte mit dem Middleware-Layer.
    -   `app.py`: Hauptanwendung mit Routen-Definitionen.
    -   `templates/`: Jinja2-Templates für die HTML-Struktur.
    -   `static/`: CSS- und JavaScript-Dateien.

2.  **Middleware (`/middleware`)**: Das Herzstück der Anwendungslogik. Sie verarbeitet Anfragen vom Frontend, orchestriert die Datenbeschaffung und wendet Geschäftslogik an (z.B. Caching, Fehlerbehandlung).
    -   `core.py`: Kernkomponente, die Anfragen entgegennimmt.
    -   `request_handler.py`: Steuert die parallele Ausführung von API-Abfragen.
    -   `modules/`: Spezialisierte Manager für Zeit, E-Mail und Mitarbeiter.

3.  **Backend (`/backend`)**: Der Layer, der direkt mit der externen McTime API interagiert. Er ist für die reine Datenbeschaffung und -konvertierung zuständig.
    -   `api_handler.py`: Stellt eine saubere Schnittstelle zur McTime API bereit.
    -   `client.py`: Ein HTTP-Client für die API-Kommunikation.

### Installation & Inbetriebnahme

1.  **Repository klonen**:
    ```bash
    git clone https://github.com/L0Xit/Mc-Time-API-Data-Bridge.git
    cd Mc-Time-API-Data-Bridge
    ```

2.  **Python Virtual Environment erstellen**:
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **Abhängigkeiten installieren**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Umgebungsvariablen konfigurieren**:
    -   Kopieren Sie die Vorlagedatei: `copy .env.example .env` (Windows) oder `cp .env.example .env` (macOS/Linux).
    -   Öffnen Sie die `.env`-Datei und tragen Sie Ihre McTime API- und SMTP-Zugangsdaten ein. **Wichtig**: Diese Datei wird durch `.gitignore` ignoriert und darf niemals committet werden.

5.  **Server starten (Entwicklungsmodus)**:
    ```bash
    # PowerShell
    $env:FLASK_APP = "frontend/app.py"; $env:FLASK_DEBUG = "1"; flask run
    
    # Bash (macOS/Linux)
    export FLASK_APP=frontend/app.py
    export FLASK_DEBUG=1
    flask run
    ```

6.  **Anwendung im Browser öffnen**:
    [http://127.0.0.1:5000](http://127.0.0.1:5000)

### Security
Die Sicherheit wird durch mehrere Maßnahmen gewährleistet:
-   **Secrets Management**: Alle sensiblen Daten (API-Keys, Passwörter) werden ausschließlich über Umgebungsvariablen (`.env`-Datei) geladen und sind im Code-Repository nicht vorhanden.
-   **`.gitignore`**: Verhindert das versehentliche Hochladen der `.env`-Datei.
-   **Input Validierung**: Serverseitige Überprüfung von Eingabeparametern, um Injection-Angriffe zu verhindern.
-   Detaillierte Informationen finden Sie in der [SECURITY.md](SECURITY.md).

### Lizenz
Dieses Projekt steht unter der **MIT-Lizenz**. Details finden Sie in der `LICENSE`-Datei. Sie dürfen den Code frei verwenden, modifizieren und verteilen, solange der ursprüngliche Copyright-Hinweis beibehalten wird.

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

