from flask import Flask, render_template, jsonify, request, Response
import os
import io
import csv
import sys
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
API_KEY = "bvtA7WVi52MBmu69bRSEEWYSOggNSRKRXJxQc5bPmBPqBXhS"
backend_service = BackendService(API_KEY)

@app.route('/')
def home():
    # Get data from McTime API via backend service
    try:
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
    """Send time tracking report via email using various methods"""
    import smtplib
    import requests
    import json
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from datetime import datetime
    
    try:
        # Email method configuration
        email_method = os.environ.get('EMAIL_METHOD', 'simulate')  # smtp, sendgrid, mailgun, webhook, simulate
        
        # Create email content first (used by all methods)
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
            <p>Diese E-Mail wurde automatisch vom Mc-Time API Data Bridge System generiert.</p>
        </body>
        </html>
        """
        
        # Choose email sending method
        if email_method == 'sendgrid':
            return send_email_sendgrid(email, subject, html_body)
        elif email_method == 'mailgun':
            return send_email_mailgun(email, subject, html_body)
        elif email_method == 'webhook':
            return send_email_webhook(email, subject, html_body, employee_name, time_entries, date_from, date_to)
        elif email_method == 'smtp':
            return send_email_smtp(email, subject, html_body)
        else:  # simulate
            return simulate_email_sending(email, subject, html_body, total_work_hours, total_entries)
        
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def send_email_sendgrid(email, subject, html_body):
    """Send email using SendGrid API"""
    try:
        import requests
        
        api_key = os.environ.get('SENDGRID_API_KEY')
        sender_email = os.environ.get('SENDER_EMAIL', 'noreply@company.com')
        
        if not api_key:
            print("SendGrid API key not configured")
            return False
            
        url = "https://api.sendgrid.com/v3/mail/send"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "personalizations": [{
                "to": [{"email": email}],
                "subject": subject
            }],
            "from": {"email": sender_email},
            "content": [{
                "type": "text/html",
                "value": html_body
            }]
        }
        
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 202:
            print(f"Email sent successfully via SendGrid to: {email}")
            return True
        else:
            print(f"SendGrid error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"SendGrid error: {e}")
        return False

def send_email_mailgun(email, subject, html_body):
    """Send email using Mailgun API"""
    try:
        import requests
        
        api_key = os.environ.get('MAILGUN_API_KEY')
        domain = os.environ.get('MAILGUN_DOMAIN')
        sender_email = os.environ.get('SENDER_EMAIL', f'noreply@{domain}')
        
        if not api_key or not domain:
            print("Mailgun API key or domain not configured")
            return False
            
        url = f"https://api.mailgun.net/v3/{domain}/messages"
        
        response = requests.post(
            url,
            auth=("api", api_key),
            data={
                "from": sender_email,
                "to": email,
                "subject": subject,
                "html": html_body
            }
        )
        
        if response.status_code == 200:
            print(f"Email sent successfully via Mailgun to: {email}")
            return True
        else:
            print(f"Mailgun error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"Mailgun error: {e}")
        return False

def send_email_webhook(email, subject, html_body, employee_name, time_entries, date_from, date_to):
    """Send email using custom webhook"""
    try:
        import requests
        
        webhook_url = os.environ.get('EMAIL_WEBHOOK_URL')
        webhook_token = os.environ.get('EMAIL_WEBHOOK_TOKEN', '')
        
        if not webhook_url:
            print("Webhook URL not configured")
            return False
            
        # Prepare webhook payload
        payload = {
            "to": email,
            "subject": subject,
            "html_body": html_body,
            "employee_name": employee_name,
            "date_from": date_from,
            "date_to": date_to,
            "time_entries": time_entries,
            "token": webhook_token
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        if webhook_token:
            headers["Authorization"] = f"Bearer {webhook_token}"
            
        response = requests.post(webhook_url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            print(f"Email sent successfully via webhook to: {email}")
            return True
        else:
            print(f"Webhook error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"Webhook error: {e}")
        return False

def send_email_smtp(email, subject, html_body):
    """Send email using traditional SMTP"""
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        # SMTP configuration
        smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        sender_email = os.environ.get('SENDER_EMAIL')
        sender_password = os.environ.get('SENDER_PASSWORD')
        
        if not sender_email or not sender_password:
            print("SMTP credentials not configured")
            return False
        
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = sender_email
        message["To"] = email
        
        # Add HTML content
        html_part = MIMEText(html_body, "html")
        message.attach(html_part)
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(message)
        
        print(f"Email sent successfully via SMTP to: {email}")
        return True
        
    except Exception as e:
        print(f"SMTP error: {e}")
        return False

def simulate_email_sending(email, subject, html_body, total_work_hours, total_entries):
    """Simulate email sending for testing"""
    print(f"=== SIMULATED EMAIL ===")
    print(f"To: {email}")
    print(f"Subject: {subject}")
    print(f"Content length: {len(html_body)} characters")
    print(f"Total work hours: {total_work_hours:.2f}h")
    print(f"Entries: {total_entries}")
    print("=== EMAIL SIMULATION COMPLETE ===")
    return True

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
