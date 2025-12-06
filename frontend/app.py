from flask import Flask, render_template, jsonify, request, Response
import os
import io
import csv
import sys

# Füge Projekt-Root zum Pfad hinzu
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
except ImportError:
    print("python-dotenv not installed. Install with: pip install python-dotenv")
    print("Using environment variables directly.")

# Importiere Backend und Middleware
from middleware.core import Middleware, get_middleware
from backend.api_handler import BackendService

app = Flask(__name__, template_folder='templates', static_folder='static')

# ==================== HYBRID ARCHITEKTUR ====================
# Frontend → Middleware → Backend → McTime API
# Middleware: Authentifizierung, Rate Limiting, Fehlerbehandlung
# Backend: McTime API-Logik, Datenverarbeitung

API_KEY = os.getenv('MCTIME_API_KEY')
if not API_KEY:
    print("WARNING: MCTIME_API_KEY environment variable not set!")
    print("Please configure your .env file with MCTIME_API_KEY")

# Initialisiere Backend Service
try:
    backend_service = BackendService(API_KEY) if API_KEY else None
    if backend_service:
        print("✅ Backend Service initialisiert")
except Exception as e:
    print(f"❌ Backend-Fehler: {e}")
    backend_service = None

# Initialisiere Middleware (für zusätzliche Features)
try:
    middleware = get_middleware(API_KEY) if API_KEY else None
    if middleware:
        print("✅ Middleware initialisiert")
except Exception as e:
    print(f"❌ Middleware-Fehler: {e}")
    middleware = None

@app.route('/')
def home():
    """Hauptseite - Backend mit Middleware Fallback"""
    try:
        # Primär: Backend Service verwenden
        if backend_service:
            form_data = backend_service.get_form_data()
            companies = form_data.get('organizations', [])
            employees = form_data.get('employees', [])
            connection_status = form_data.get('status') == 'success'
        # Fallback: Middleware
        elif middleware:
            form_data = middleware.get_form_data()
            companies = form_data.get('organizations', [])
            employees = form_data.get('employees', [])
            connection_status = form_data.get('status') == 'success'
        else:
            raise Exception("Weder Backend noch Middleware initialisiert")
        
    except Exception as e:
        print(f"Fehler beim Laden der Daten: {e}")
        companies = []
        employees = []
        connection_status = False
    
    return render_template('index.html', 
                         companies=companies, 
                         employees=employees,
                         db_status=connection_status)

@app.route('/api_config')
def api_config():
    """Middleware-Konfigurationsseite"""
    return render_template('api_config.html')

@app.route('/page_1')
def page_1():
    return render_template('321.html')

@app.route('/api/status')
def system_status():
    """Gibt den Status von Backend und Middleware zurück"""
    status = {
        "backend": {
            "available": backend_service is not None,
            "api_configured": bool(API_KEY)
        },
        "middleware": {
            "available": middleware is not None,
            "status": middleware.get_connection_status() if middleware else None
        }
    }
    return jsonify(status)

@app.route('/api/middleware/ping')
def ping_middleware():
    """Testet die Verbindung zur Middleware/McTime API"""
    if not middleware:
        return jsonify({
            "status": "error",
            "message": "Middleware nicht initialisiert"
        })
    return jsonify(middleware.health_check())

@app.route('/api/middleware/stats')
def middleware_stats():
    """Gibt Middleware-Statistiken zurück"""
    if not middleware:
        return jsonify({"error": "Middleware nicht initialisiert"})
    return jsonify(middleware.request_handler.get_stats())

@app.route('/api/load-data', methods=['POST'])
def load_data():
    """
    Endpoint für McTime API Daten-Laden - BACKEND PRIMÄR
    Expected JSON payload:
    {
        "firma": "organization_id",
        "mitarbeiter": "employee_id",
        "von": "dd.mm.yyyy",
        "bis": "dd.mm.yyyy"
    }
    """
    try:
        form_data = request.get_json()
        print("=== HYBRID API CALL ===")
        print(f"Received form_data: {form_data}")
        
        if not form_data:
            print("ERROR: No JSON data provided")
            return jsonify({
                "status": "error",
                "message": "No JSON data provided"
            }), 400
        
        # Primär: Backend Service verwenden
        if backend_service:
            print("Using Backend Service...")
            result = backend_service.process_form_request(form_data)
        # Fallback: Middleware
        elif middleware:
            print("Fallback: Using Middleware...")
            result = middleware.process_form_request(form_data)
        else:
            return jsonify({
                "status": "error",
                "message": "Weder Backend noch Middleware verfügbar"
            }), 500
        
        print(f"Result: {result}")
        
        if result.get("status") == "error":
            print(f"Service returned error: {result.get('message')}")
            return jsonify(result), 400
        
        print(f"Success! Returning {len(result.get('data', {}).get('timeEntries', []))} time entries")
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to process request: {str(e)}"
        }), 500

@app.route('/api/data')
def get_data():
    """Holt gefilterte Daten - Backend primär, Middleware Fallback"""
    company = request.args.get('company')
    employee = request.args.get('employee')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    if not all([employee, date_from, date_to]):
        return jsonify({"error": "Fehlende Parameter: employee, date_from, date_to"}), 400
    
    try:
        # Primär: Backend verwenden
        if backend_service:
            # Konvertiere Format für Backend
            date_from = backend_service._convert_date_format(date_from) if '.' in date_from else date_from
            date_to = backend_service._convert_date_format(date_to) if '.' in date_to else date_to
            
            data = backend_service.mctime_api.get_time_entries(
                employee_id=employee,
                date_from=date_from,
                date_to=date_to,
                organization_id=company
            )
        # Fallback: Middleware
        elif middleware:
            data = middleware.get_time_entries(
                employee_id=employee,
                date_from=date_from,
                date_to=date_to,
                organization_id=company
            )
        else:
            return jsonify({"error": "Kein Service verfügbar"}), 500
        
        return jsonify(data)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/send-email', methods=['POST'])
def send_email():
    """Send time tracking data via email - HYBRID APPROACH"""
    try:
        # Get form data (JSON oder Form)
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        employee_id = data.get('employee_id')
        employee_name = data.get('employee_name')
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        
        if not all([employee_id, date_from, date_to]):
            return jsonify({
                'status': 'error',
                'message': 'Fehlende Parameter: employee_id, date_from, date_to erforderlich'
            })
        
        # Erweiterte Middleware-Features verfügbar?
        if middleware and hasattr(middleware, 'send_time_report_email'):
            # Neue optionale Parameter
            custom_email = data.get('email_to')
            custom_subject = data.get('email_subject')
            attach_csv = data.get('attach_csv', 'true').lower() == 'true'
            
            # Konvertiere Datum
            date_from = middleware._normalize_date(date_from)
            date_to = middleware._normalize_date(date_to)
            
            # Nutze erweiterte Middleware-Features
            result = middleware.send_time_report_email(
                employee_id=employee_id,
                employee_name=employee_name or "Mitarbeiter",
                date_from=date_from,
                date_to=date_to,
                custom_email=custom_email,
                custom_subject=custom_subject,
                attach_csv=attach_csv
            )
        
        elif backend_service:
            # Basic E-Mail über Backend (legacy)
            # Konvertiere Datum für Backend
            if '.' in date_from:
                date_from = backend_service._convert_date_format(date_from)
            if '.' in date_to:
                date_to = backend_service._convert_date_format(date_to)
            
            # Hole E-Mail und Zeitdaten über Backend
            employee_email = backend_service.mctime_api.get_user_email_by_id(employee_id)
            if not employee_email:
                return jsonify({
                    'status': 'error',
                    'message': f'Keine E-Mail-Adresse für {employee_name} gefunden'
                })
            
            time_entries = backend_service.mctime_api.get_time_entries(
                employee_id, date_from, date_to
            )
            
            if not time_entries:
                return jsonify({
                    'status': 'error',
                    'message': 'Keine Zeiteinträge gefunden'
                })
            
            # Basic E-Mail-Versand (ohne erweiterte Features)
            result = {
                'status': 'success',
                'message': 'Daten verfügbar - erweiterte E-Mail-Features benötigen Middleware',
                'email': employee_email,
                'entries_count': len(time_entries)
            }
        
        else:
            return jsonify({
                'status': 'error',
                'message': 'Weder Backend noch Middleware verfügbar'
            }), 500
        
        return jsonify(result)
            
    except Exception as e:
        print(f"Error in send_email: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Server-Fehler: {str(e)}'
        })


# ==================== ZUSÄTZLICHE MIDDLEWARE-ENDPOINTS ====================

@app.route('/api/employees')
def get_employees():
    """Holt Mitarbeiterliste über Middleware"""
    if not middleware:
        return jsonify({"error": "Middleware nicht initialisiert"}), 500
    
    org_id = request.args.get('organization_id')
    employees = middleware.get_employees(org_id)
    return jsonify(employees)


@app.route('/api/organizations')
def get_organizations():
    """Holt Organisationsliste über Middleware"""
    if not middleware:
        return jsonify({"error": "Middleware nicht initialisiert"}), 500
    
    organizations = middleware.get_organizations()
    return jsonify(organizations)


@app.route('/api/send-custom-email', methods=['POST'])
def send_custom_email():
    """
    Erweiterte E-Mail-Funktion mit benutzerdefinierten Optionen
    
    JSON Payload:
    {
        "employee_id": "uuid",
        "employee_name": "Name",
        "date_from": "dd.mm.yyyy",
        "date_to": "dd.mm.yyyy", 
        "email_to": "custom@email.com",       # Optional: benutzerdefinierte E-Mail
        "email_subject": "Custom Subject",     # Optional: benutzerdefinierter Betreff
        "attach_csv": true,                    # Optional: CSV anhängen (default: true)
        "message": "Zusätzliche Nachricht"    # Optional: persönliche Nachricht
    }
    """
    try:
        if not middleware:
            return jsonify({
                'status': 'error',
                'message': 'Middleware nicht initialisiert'
            }), 500
        
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error', 
                'message': 'JSON-Daten erforderlich'
            }), 400
        
        # Pflichtfelder
        employee_id = data.get('employee_id')
        date_from = data.get('date_from')  
        date_to = data.get('date_to')
        
        if not all([employee_id, date_from, date_to]):
            return jsonify({
                'status': 'error',
                'message': 'Pflichtfelder: employee_id, date_from, date_to'
            }), 400
        
        # Optionale Felder
        employee_name = data.get('employee_name', 'Mitarbeiter')
        custom_email = data.get('email_to')
        custom_subject = data.get('email_subject')
        attach_csv = data.get('attach_csv', True)
        custom_message = data.get('message', '')
        
        # Wenn kein custom_subject, aber custom_message vorhanden
        if custom_message and not custom_subject:
            custom_subject = f"Zeiterfassung - {custom_message}"
        
        # Normalisiere Datums-Format
        date_from = middleware._normalize_date(date_from)
        date_to = middleware._normalize_date(date_to)
        
        print(f"=== CUSTOM EMAIL REQUEST ===")
        print(f"Employee: {employee_name} ({employee_id})")
        print(f"Period: {date_from} - {date_to}")
        print(f"Custom Email: {custom_email}")
        print(f"Custom Subject: {custom_subject}")
        print(f"Attach CSV: {attach_csv}")
        print(f"Custom Message: {custom_message}")
        
        # Sende über Middleware
        result = middleware.send_time_report_email(
            employee_id=employee_id,
            employee_name=employee_name,
            date_from=date_from,
            date_to=date_to,
            custom_email=custom_email,
            custom_subject=custom_subject,
            attach_csv=attach_csv,
            custom_message=custom_message
        )
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error in send_custom_email: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Server-Fehler: {str(e)}'
        }), 500


@app.route('/api/test-csv/<employee_id>')
def test_csv_structure(employee_id):
    """Test-Route für CSV-Struktur Validierung"""
    if not middleware:
        return jsonify({"error": "Middleware nicht initialisiert"}), 500
    
    # Test-Daten holen
    date_from = "01.10.2025"
    date_to = "31.10.2025"
    
    try:
        data = middleware.get_time_entries(
            employee_id=employee_id,
            date_from=middleware._normalize_date(date_from),
            date_to=middleware._normalize_date(date_to)
        )
        
        # CSV-Content erstellen
        csv_content = middleware.mail._create_csv_content(data, "Test Benutzer")
        
        return Response(
            csv_content,
            mimetype='text/csv',
            headers={"Content-disposition": "attachment; filename=test_struktur.csv"}
        )
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/download_csv')
def download_csv():
    """CSV-Download - Daten über Middleware"""
    if not middleware:
        return jsonify({"error": "Middleware nicht initialisiert"}), 500
    
    # Filter aus Request-Parametern holen
    company = request.args.get('company')
    employee = request.args.get('employee')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    if not all([employee, date_from, date_to]):
        return jsonify({"error": "Fehlende Parameter"}), 400
    
    # Normalisiere Datum
    date_from = middleware._normalize_date(date_from)
    date_to = middleware._normalize_date(date_to)
    
    # Daten über Middleware holen
    data = middleware.get_time_entries(
        employee_id=employee,
        date_from=date_from,
        date_to=date_to,
        organization_id=company
    )
    
    # CSV-Header erstellen - Original McTime Format
    headers = [
        'Personalnummer', 'Vorname', 'Nachname', 'Datum', 'Type',
        'Zeit Beginn', 'Zeit Ende', 'Pause', 'Summe mit Pause', 
        'Summe ohne Pause', 'Projektnummer', 'Auftragsnummer',
        'Projekt / Gruppenname', 'Kommentar'
    ]
    csv_data = [headers]
    
    # Daten hinzufügen im korrekten Format
    for row in data:
        # Name aufteilen
        name_parts = (row.get('name', '') or '').split(' ', 1)
        first_name = name_parts[0] if len(name_parts) > 0 else ''
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        csv_data.append([
            row.get('employee_id', ''),             # Personalnummer (UUID)
            first_name,                             # Vorname
            last_name,                              # Nachname
            row.get('date_formatted', ''),          # Datum (01.10.25)
            'Arbeitszeit',                          # Type
            row.get('time_start', ''),              # Zeit Beginn (05:00)
            row.get('time_end', ''),                # Zeit Ende (18:00)
            f'"{row.get("breaks_formatted", "")}"' if row.get('breaks_formatted') else '', # Pause in Anführungszeichen
            row.get('total_hours_formatted', ''),   # Summe mit Pause (13:00)
            row.get('actual_hours_formatted', ''),  # Summe ohne Pause (12:00)
            '',                                     # Projektnummer
            '',                                     # Auftragsnummer
            row.get('project', ''),                 # Projekt / Gruppenname
            ''                                      # Kommentar
        ])
    
    # CSV in Memory erstellen mit Semicolon-Delimiter (wie im Original)
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    writer.writerows(csv_data)
    
    # Response erstellen
    response = Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={"Content-disposition": "attachment; filename=zeitdaten_export.csv"}
    )
    
    return response


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, port=port)
