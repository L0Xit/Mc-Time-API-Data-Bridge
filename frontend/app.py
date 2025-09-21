from flask import Flask, render_template, jsonify, request, Response
import os
import io
import csv
from api_connector import middleware_connector

app = Flask(__name__, template_folder='templates', static_folder='static')

@app.route('/')
def home():
    # Daten von Middleware Connector holen
    companies = middleware_connector.get_companies()
    employees = [emp['name'] for emp in middleware_connector.get_employees()]
    
    # Middleware-Verbindungsstatus
    connection_status = middleware_connector.get_connection_status()
    
    return render_template('index.html', 
                         companies=companies, 
                         employees=employees,
                         db_status=connection_status['connected'])

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

@app.route('/api/data')
def get_data():
    """Holt gefilterte Daten von der Middleware"""
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
