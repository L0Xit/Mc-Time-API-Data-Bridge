from flask import Flask, render_template, jsonify, request, Response
import os
import io
import csv
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime

# Pfade für Middleware und Backend hinzufügen
_middleware_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'middleware'))
_backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
sys.path.insert(0, _middleware_path)
sys.path.insert(0, _backend_path)

# Middleware importieren - zentrale Schnittstelle
from adapter import AdapterMiddleware

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
except ImportError:
    print("python-dotenv not installed. Install with: pip install python-dotenv")
    print("Using environment variables directly.")

app = Flask(__name__, template_folder='templates', static_folder='static')

# ============================================================================
# MIDDLEWARE INITIALISIERUNG
# ============================================================================
# Alle API-Calls gehen durch die Middleware:
# Frontend (app.py) → Middleware (adapter.py) → Backend (api_handler.py) → McTime API

API_KEY = os.getenv('MCTIME_API_KEY')
if not API_KEY:
    print("WARNING: MCTIME_API_KEY environment variable not set!")
    print("Please configure your .env file with MCTIME_API_KEY")

# Middleware als zentrale Schnittstelle
middleware = AdapterMiddleware(api_key=API_KEY)
print("=" * 60)
print("✅ Middleware initialisiert")
print(f"   API-Key konfiguriert: {'Ja' if API_KEY else 'Nein'}")
print("   Datenfluss: Frontend → Middleware → Backend → McTime API")
print("=" * 60)

@app.route('/')
def home():
    # Get data from McTime API via Middleware
    try:
        form_data = middleware.get_form_data()
        companies = form_data.get('organizations', [])
        employees = form_data.get('employees', [])
        connection_status = form_data.get('status') == 'success'
    except Exception as e:
        print(f"Middleware error: {e}")
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

@app.route('/api/middleware/status')
def middleware_status():
    """Gibt den Status der Middleware-Verbindung zurück"""
    return jsonify(middleware.get_connection_status())

@app.route('/api/middleware/ping')
def ping_middleware():
    """Testet die Verbindung zur Middleware"""
    is_valid = middleware.validate_api_key()
    return jsonify({
        'success': is_valid,
        'message': 'Middleware verbunden' if is_valid else 'Verbindung fehlgeschlagen'
    })

@app.route('/api/load-data', methods=['POST'])
def load_data():
    """
    Lädt Zeitdaten über die Middleware
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
        print("=== MIDDLEWARE API CALL ===")
        print(f"Received form_data: {form_data}")
        
        if not form_data:
            print("ERROR: No JSON data provided")
            return jsonify({
                "status": "error",
                "message": "No JSON data provided"
            }), 400
        
        # Extrahiere Parameter
        employee_id = form_data.get('mitarbeiter')
        date_from = form_data.get('von')
        date_to = form_data.get('bis')
        organization_id = form_data.get('firma')
        
        if not all([employee_id, date_from, date_to]):
            return jsonify({
                "status": "error",
                "message": "Mitarbeiter, Von und Bis Datum erforderlich"
            }), 400
        
        # Hole Daten über Middleware
        time_entries = middleware.get_time_entries(
            employee_id=employee_id,
            date_from=date_from,
            date_to=date_to,
            organization_id=organization_id
        )
        
        print(f"Success! Returning {len(time_entries)} time entries")
        
        return jsonify({
            "status": "success",
            "data": {
                "timeEntries": time_entries
            }
        })
        
    except Exception as e:
        print(f"Middleware error: {e}")
        return jsonify({
            "status": "error",
            "message": f"Middleware-Fehler: {str(e)}"
        }), 500

@app.route('/api/data')
def get_data():
    """Holt gefilterte Daten von der Middleware"""
    employee = request.args.get('employee')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    organization = request.args.get('company')
    
    if not all([employee, date_from, date_to]):
        return jsonify([])
    
    data = middleware.get_time_entries(
        employee_id=employee,
        date_from=date_from,
        date_to=date_to,
        organization_id=organization
    )
    return jsonify(data)

@app.route('/api/send-email', methods=['POST'])
def send_email():
    """Send time tracking data via email with custom recipient, subject and message"""
    try:
        # Get form data - neue Felder
        email_to = request.form.get('email_to')
        email_subject = request.form.get('email_subject', 'McTime Zeitdaten Export')
        email_message = request.form.get('email_message', '')
        attach_csv = request.form.get('attach_csv', 'true').lower() == 'true'
        
        # Alte Felder für CSV-Daten
        employee_id = request.form.get('employee_id')
        employee_name = request.form.get('employee_name', '')
        date_from = request.form.get('date_from')
        date_to = request.form.get('date_to')
        
        # Validierung: E-Mail-Adresse erforderlich
        if not email_to:
            return jsonify({
                'status': 'error',
                'message': 'Bitte geben Sie eine Empfänger E-Mail-Adresse ein'
            })

        # CSV-Inhalt erstellen wenn gewünscht
        csv_content = None
        if attach_csv:
            if not all([employee_id, date_from, date_to]):
                return jsonify({
                    'status': 'error',
                    'message': 'Für CSV-Anhang: Mitarbeiter und Zeitraum erforderlich'
                })
            
            # Hole Zeitdaten über Middleware
            time_entries = middleware.get_time_entries(
                employee_id=employee_id, 
                date_from=date_from, 
                date_to=date_to
            )
            
            if time_entries:
                csv_content = create_csv_content(time_entries, employee_name)
        
        # HTML-Body erstellen
        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #333;">McTime API Data Bridge</h2>
            <div style="margin: 20px 0; padding: 15px; background-color: #f5f5f5; border-radius: 5px;">
                <p>{email_message.replace(chr(10), '<br>')}</p>
            </div>
            <hr style="border: 1px solid #ddd;">
            <p style="font-size: 12px; color: #666;">
                Diese E-Mail wurde automatisch von der McTime API Data Bridge gesendet.
            </p>
        </body>
        </html>
        """
        
        # E-Mail senden
        success = send_real_email_smtp(
            to_email=email_to,
            subject=email_subject,
            body_html=body_html,
            csv_content=csv_content,
            employee_name=employee_name
        )
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'E-Mail erfolgreich gesendet',
                'email': email_to
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Fehler beim Senden der E-Mail. Prüfen Sie die SMTP-Konfiguration.'
            })
            
    except Exception as e:
        print(f"Error in send_email: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Server-Fehler: {str(e)}'
        })

def send_time_report_email(email, employee_name, time_entries, date_from, date_to):
    """Send time tracking report via email using SMTP with CSV attachment"""
    
    try:
        # Create email content
        subject = f"Zeiterfassung für {employee_name} ({date_from} bis {date_to})"
        
        # Calculate totals
        total_work_hours = sum(entry.get('actual_work_hours', 0) for entry in time_entries)
        total_entries = len(time_entries)
        
        # Create CSV content for attachment
        csv_content = create_csv_content(time_entries, employee_name)
        
        # Create HTML email body with WorkExpert format
        html_body = f"""
        <html>
        <body>
            <h2>Zeiterfassung - {employee_name}</h2>
            <p><strong>Zeitraum:</strong> {date_from} bis {date_to}</p>
            <p><strong>Gesamtanzahl Einträge:</strong> {total_entries}</p>
            <p><strong>Gesamte Arbeitsstunden:</strong> {total_work_hours:.2f}h</p>
            <p><em>Die detaillierte Aufstellung finden Sie in der angehängten CSV-Datei.</em></p>
            
            <h3>Detaillierte Aufstellung:</h3>
            <table border="1" style="border-collapse: collapse; width: 100%;">
                <tr style="background-color: #f0f0f0;">
                    <th style="padding: 8px;">Datum</th>
                    <th style="padding: 8px;">Type</th>
                    <th style="padding: 8px;">Beginn</th>
                    <th style="padding: 8px;">Ende</th>
                    <th style="padding: 8px;">Pause</th>
                    <th style="padding: 8px;">Mit Pause</th>
                    <th style="padding: 8px;">Ohne Pause</th>
                    <th style="padding: 8px;">Projekt</th>
                </tr>
        """
        
        for entry in time_entries:
            html_body += f"""
                <tr>
                    <td style="padding: 8px;">{entry.get('date_formatted', 'N/A')}</td>
                    <td style="padding: 8px;">{entry.get('type', 'Arbeitszeit')}</td>
                    <td style="padding: 8px;">{entry.get('start_time', 'N/A')}</td>
                    <td style="padding: 8px;">{entry.get('end_time', 'N/A')}</td>
                    <td style="padding: 8px;">{entry.get('pause', '')}</td>
                    <td style="padding: 8px;">{entry.get('summe_mit_pause', '')}</td>
                    <td style="padding: 8px;">{entry.get('summe_ohne_pause', '')}</td>
                    <td style="padding: 8px;">{entry.get('project', 'N/A')}</td>
                </tr>
            """
        
        html_body += """
            </table>
            <br>
            <p>Diese E-Mail wurde automatisch vom McTime System generiert.</p>
        </body>
        </html>
        """
        
        # Send email via SMTP with TLS and CSV attachment
        print("Sending email via SMTP with TLS and CSV attachment...")
        success = send_real_email_smtp(to_email=email, subject=subject, body_html=html_body, csv_content=csv_content, employee_name=employee_name)
        
        return success
        
    except Exception as e:
        print(f"Error sending email: {e}")
        import traceback
        traceback.print_exc()
        return False


def create_csv_content(time_entries, employee_name):
    """Create CSV content from time entries in WorkExpert format"""
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    
    # Header
    writer.writerow([
        'Personalnummer',
        'Vorname',
        'Nachname',
        'Datum',
        'Type',
        'Zeit Beginn',
        'Zeit Ende',
        'Pause',
        'Summe mit Pause',
        'Summe ohne Pause',
        'Projektnummer',
        'Auftragsnummer',
        'Projekt / Gruppenname',
        'Kommentar'
    ])
    
    # Data rows
    for entry in time_entries:
        writer.writerow([
            entry.get('personalnummer', entry.get('id', '')),
            entry.get('firstName', ''),
            entry.get('lastName', ''),
            entry.get('date_formatted', ''),
            entry.get('type', 'Arbeitszeit'),
            entry.get('start_time', ''),
            entry.get('end_time', ''),
            entry.get('pause', ''),
            entry.get('summe_mit_pause', ''),
            entry.get('summe_ohne_pause', ''),
            entry.get('projektnummer', ''),
            entry.get('auftragsnummer', ''),
            entry.get('project', ''),
            entry.get('kommentar', '')
        ])
    
    return output.getvalue()


def send_real_email_smtp(to_email, subject, body_html, csv_content=None, employee_name=None):
    """Send email using SMTP with TLS and optional CSV attachment"""
    try:
        # SECURITY: All credentials MUST come from environment variables
        smtp_server = os.getenv('SMTP_SERVER')
        smtp_port = int(os.getenv('SMTP_PORT', 587))
        smtp_username = os.getenv('SMTP_USERNAME')
        smtp_password = os.getenv('SMTP_PASSWORD')
        from_email = os.getenv('SENDER_EMAIL')
        use_tls = os.getenv('USE_TLS', 'true').lower() == 'true'
        
        # Validate required credentials
        if not all([smtp_server, smtp_username, smtp_password, from_email]):
            print("ERROR: Missing required SMTP environment variables!")
            print("Please configure: SMTP_SERVER, SMTP_USERNAME, SMTP_PASSWORD, SENDER_EMAIL")
            return False
        
        print("=== SENDING REAL EMAIL ===")
        print(f"SMTP Server: {smtp_server}:{smtp_port}")
        print(f"From: {from_email}")
        print(f"To: {to_email}")
        print(f"Subject: {subject}")
        print(f"Username: {smtp_username}")
        print(f"Password: {'***'}")
        print(f"CSV Attachment: {'Yes' if csv_content else 'No'}")
        
        # Create message with mixed type for attachments
        msg = MIMEMultipart('mixed')
        msg['Subject'] = subject
        msg['From'] = from_email
        msg['To'] = to_email
        
        # Add HTML body
        html_part = MIMEText(body_html, 'html', 'utf-8')
        msg.attach(html_part)
        
        # Add CSV attachment if provided
        if csv_content:
            # Create CSV attachment
            csv_attachment = MIMEBase('text', 'csv')
            csv_attachment.set_payload(csv_content.encode('utf-8'))
            encoders.encode_base64(csv_attachment)
            
            # Generate filename with employee name and date
            filename = f"zeiterfassung_{employee_name.replace(' ', '_') if employee_name else 'export'}_{datetime.now().strftime('%Y%m%d')}.csv"
            csv_attachment.add_header(
                'Content-Disposition',
                'attachment',
                filename=filename
            )
            msg.attach(csv_attachment)
            print(f"CSV attachment added: {filename}")
        
        print(f"TLS: {use_tls}")
        
        print("Connecting to SMTP server with TLS...")
        
        # Use TLS connection (as specified)
        server = smtplib.SMTP(smtp_server, smtp_port)
        if use_tls:
            print("Enabling TLS encryption...")
            server.starttls()
        
        print("Connected. Attempting login...")
        server.login(smtp_username, smtp_password)
        
        print("Logged in. Sending email...")
        server.send_message(msg)
        server.quit()
        
        print("✅ Email sent successfully with CSV attachment!")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"SMTP Authentication Error: {e}")
        print("Tip: AWS SES may require proper SES SMTP credentials, not API credentials")
        return False
    except smtplib.SMTPException as e:
        print(f"SMTP Error: {e}")
        return False
    except Exception as e:
        print(f"Email sending error: {e}")
        return False





@app.route('/download_csv')
def download_csv():
    """CSV Download im WorkExpert Format"""
    # Filter aus Request-Parametern holen
    company = request.args.get('company')
    employee = request.args.get('employee')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    print(f"=== CSV DOWNLOAD (via Middleware) ===")
    print(f"Company: {company}")
    print(f"Employee: {employee}")
    print(f"Date From: {date_from}")
    print(f"Date To: {date_to}")
    
    data = []
    
    # Zeitdaten über Middleware abrufen
    if employee and date_from and date_to:
        try:
            # Datum konvertieren von YYYY-MM-DD zu DD.MM.YYYY
            date_from_formatted = datetime.strptime(date_from, '%Y-%m-%d').strftime('%d.%m.%Y')
            date_to_formatted = datetime.strptime(date_to, '%Y-%m-%d').strftime('%d.%m.%Y')
            
            print(f"Formatted dates: {date_from_formatted} - {date_to_formatted}")
            
            # Daten über Middleware holen
            data = middleware.get_time_entries(
                employee_id=employee,
                date_from=date_from_formatted,
                date_to=date_to_formatted,
                organization_id=company if company else None
            )
            
            print(f"Got {len(data)} time entries from middleware")
            
        except Exception as e:
            print(f"Error getting data for CSV: {e}")
            import traceback
            traceback.print_exc()
            data = []
    else:
        print("Missing required fields for CSV export")
        data = []
    
    print(f"Total data entries for CSV: {len(data)}")
    
    # CSV-Header im WorkExpert Format erstellen
    csv_data = [[
        'Personalnummer',
        'Vorname',
        'Nachname',
        'Datum',
        'Type',
        'Zeit Beginn',
        'Zeit Ende',
        'Pause',
        'Summe mit Pause',
        'Summe ohne Pause',
        'Projektnummer',
        'Auftragsnummer',
        'Projekt / Gruppenname',
        'Kommentar'
    ]]
    
    # Daten im WorkExpert Format hinzufügen
    for row in data:
        csv_data.append([
            row.get('personalnummer', row.get('id', '')),
            row.get('firstName', ''),
            row.get('lastName', ''),
            row.get('date_formatted', row.get('date', '')),
            row.get('type', 'Arbeitszeit'),
            row.get('start_time', ''),
            row.get('end_time', ''),
            row.get('pause', ''),
            row.get('summe_mit_pause', ''),
            row.get('summe_ohne_pause', ''),
            row.get('projektnummer', ''),
            row.get('auftragsnummer', ''),
            row.get('project', row.get('organizationName', '')),
            row.get('kommentar', row.get('description', ''))
        ])
    
    # CSV in Memory erstellen (mit Semikolon als Trennzeichen für Excel)
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    writer.writerows(csv_data)
    
    # Response erstellen
    response = Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={"Content-disposition": "attachment; filename=zeiterfassung_export.csv"}
    )
    
    return response

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, port=port)
