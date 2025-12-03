from flask import Flask, render_template, jsonify, request, Response
import os
import io
import csv
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from api_connector import middleware_connector
from api_handler import BackendService

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
except ImportError:
    print("python-dotenv not installed. Install with: pip install python-dotenv")
    print("Using environment variables directly.")

app = Flask(__name__, template_folder='templates', static_folder='static')

# Initialize backend service for McTime API
# SECURITY: Load API key from environment variable, never hardcode it!
API_KEY = os.getenv('MCTIME_API_KEY')
if not API_KEY:
    print("WARNING: MCTIME_API_KEY environment variable not set!")
    print("Please configure your .env file with MCTIME_API_KEY")
    
backend_service = BackendService(API_KEY) if API_KEY else None

@app.route('/')
def home():
    # Get data from McTime API via backend service
    try:
        if not backend_service:
            raise Exception("Backend service not initialized - check MCTIME_API_KEY")
            
        form_data = backend_service.get_form_data()
        companies = form_data.get('organizations', [])
        employees = form_data.get('employees', [])
        connection_status = True if form_data.get('status') == 'success' else False
    except Exception as e:
        # Fallback to middleware connector if backend service fails
        companies = [{'name': comp, 'id': comp} for comp in middleware_connector.get_companies()]
        employees = middleware_connector.get_employees()
        connection_status = middleware_connector.get_connection_status()['connected']
    
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
    return jsonify(middleware_connector.get_connection_status())

@app.route('/api/middleware/ping')
def ping_middleware():
    """Testet die Verbindung zur Middleware"""
    result = middleware_connector.ping_middleware()
    return jsonify(result)

@app.route('/api/load-data', methods=['POST'])
def load_data():
    """
    New endpoint for McTime API data loading
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
        print("=== BACKEND API CALL ===")
        print(f"Received form_data: {form_data}")
        
        if not form_data:
            print("ERROR: No JSON data provided")
            return jsonify({
                "status": "error",
                "message": "No JSON data provided"
            }), 400
        
        print("Processing form request...")
        result = backend_service.process_form_request(form_data)
        print(f"Backend result: {result}")
        
        if result.get("status") == "error":
            print(f"Backend returned error: {result.get('message')}")
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
    """Holt gefilterte Daten von der Middleware (legacy endpoint)"""
    company = request.args.get('company')
    employee = request.args.get('employee')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    data = middleware_connector.get_time_data(
        company=company,
        employee=employee,
        date_from=date_from,
        date_to=date_to
    )
    return jsonify(data)

@app.route('/api/send-email', methods=['POST'])
def send_email():
    """Send time tracking data via email to employee"""
    try:
        # Get form data
        employee_id = request.form.get('employee_id')
        employee_name = request.form.get('employee_name')
        date_from = request.form.get('date_from')
        date_to = request.form.get('date_to')
        
        if not all([employee_id, date_from, date_to]):
            return jsonify({
                'status': 'error',
                'message': 'Fehlende Parameter: employee_id, date_from, date_to erforderlich'
            })

        # Convert date format from dd.mm.yyyy to yyyy-mm-dd if needed
        try:
            if '.' in date_from:
                date_from = backend_service._convert_date_format(date_from)
            if '.' in date_to:
                date_to = backend_service._convert_date_format(date_to)
        except Exception as e:
            print(f"Date conversion error: {e}")
        
        # Get employee email
        employee_email = backend_service.mctime_api.get_user_email_by_id(employee_id)
        if not employee_email:
            return jsonify({
                'status': 'error',
                'message': f'Keine E-Mail-Adresse für Mitarbeiter {employee_name} gefunden'
            })
        
        # Get time entries data
        time_entries = backend_service.mctime_api.get_time_entries(
            employee_id, 
            date_from, 
            date_to
        )
        
        if not time_entries:
            return jsonify({
                'status': 'error',
                'message': 'Keine Zeiteinträge für den angegebenen Zeitraum gefunden'
            })
        
        # Send email
        success = send_time_report_email(
            employee_email, 
            employee_name, 
            time_entries, 
            date_from, 
            date_to
        )
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'E-Mail erfolgreich gesendet',
                'email': employee_email
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Fehler beim Senden der E-Mail'
            })
            
    except Exception as e:
        print(f"Error in send_email: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Server-Fehler: {str(e)}'
        })

def send_time_report_email(email, employee_name, time_entries, date_from, date_to):
    """Send time tracking report via email using SMTP"""
    from datetime import datetime
    
    try:
        # Create email content
        subject = f"Zeiterfassung für {employee_name} ({date_from} bis {date_to})"
        
        # Calculate totals
        total_work_hours = sum(entry.get('actual_work_hours', 0) for entry in time_entries)
        total_entries = len(time_entries)
        
        # Create HTML email body
        html_body = f"""
        <html>
        <body>
            <h2>Zeiterfassung - {employee_name}</h2>
            <p><strong>Zeitraum:</strong> {date_from} bis {date_to}</p>
            <p><strong>Gesamtanzahl Einträge:</strong> {total_entries}</p>
            <p><strong>Gesamte Arbeitsstunden:</strong> {total_work_hours:.2f}h</p>
            
            <h3>Detaillierte Aufstellung:</h3>
            <table border="1" style="border-collapse: collapse; width: 100%;">
                <tr>
                    <th>Datum</th>
                    <th>Projekt</th>
                    <th>Arbeitszeit</th>
                    <th>Pausen</th>
                    <th>Effektive Stunden</th>
                </tr>
        """
        
        for entry in time_entries:
            html_body += f"""
                <tr>
                    <td>{entry.get('date_formatted', 'N/A')}</td>
                    <td>{entry.get('project', 'N/A')}</td>
                    <td>{entry.get('time_formatted', 'N/A')}</td>
                    <td>{entry.get('breaks_formatted', 'N/A')}</td>
                    <td>{entry.get('actual_work_hours', 0):.2f}h</td>
                </tr>
            """
        
        html_body += """
            </table>
            <br>
            <p>Diese E-Mail wurde automatisch vom McTime System generiert.</p>
        </body>
        </html>
        """
        
        # Send email via SMTP with TLS (as specified)
        print("Sending email via SMTP with TLS...")
        success = send_real_email_smtp(email, subject, html_body)
        
        return success
        
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def send_real_email_smtp(to_email, subject, body_html):
    """Send email using SMTP with TLS (exact user specifications)"""
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
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = from_email
        msg['To'] = to_email
        
        # Add HTML body
        html_part = MIMEText(body_html, 'html', 'utf-8')
        msg.attach(html_part)
        
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
        
        print("✅ Email sent successfully!")
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
    # Filter aus Request-Parametern holen
    company = request.args.get('company')
    employee = request.args.get('employee')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    # Daten von Middleware Connector holen
    data = middleware_connector.get_time_data(
        company=company,
        employee=employee,
        date_from=date_from,
        date_to=date_to
    )
    
    # CSV-Header erstellen
    csv_data = [['Datum', 'Mitarbeiter', 'Stunden', 'Projekt', 'Firma', 'Beschreibung', 'Start', 'Ende']]
    
    # Daten hinzufügen
    for row in data:
        csv_data.append([
            row.get('date', ''),
            row.get('employee', ''),
            row.get('hours', ''),
            row.get('project', ''),
            row.get('company', ''),
            row.get('description', ''),
            row.get('start_time', ''),
            row.get('end_time', '')
        ])
    
    # CSV in Memory erstellen
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerows(csv_data)
    
    # Response erstellen
    response = Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={"Content-disposition": "attachment; filename=daten_export.csv"}
    )
    
    return response

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, port=port)
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, port=port)
