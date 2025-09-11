#!/usr/bin/env python3
"""
Frontend Flask Application - Web interface that communicates through TGM-Adapter middleware
"""

from flask import Flask, render_template_string, request, jsonify, flash, redirect, url_for
import requests
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'tgm-adapter-frontend-secret-key'

# Middleware configuration
MIDDLEWARE_URL = "http://localhost:5000"

def call_middleware(method, endpoint, data=None):
    """Make API calls to the middleware"""
    try:
        url = f"{MIDDLEWARE_URL}{endpoint}"
        
        if method.upper() == 'GET':
            response = requests.get(url, timeout=10)
        elif method.upper() == 'POST':
            response = requests.post(url, json=data, timeout=10)
        else:
            return None, f"Unsupported method: {method}"
        
        return response.json(), None
    except requests.exceptions.ConnectionError:
        return None, "Middleware is not available"
    except requests.exceptions.Timeout:
        return None, "Request timeout"
    except Exception as e:
        return None, f"Error: {str(e)}"

# HTML Templates
BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TGM-Adapter Frontend</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .header {
            background: #2c3e50;
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .nav {
            margin: 20px 0;
        }
        .nav a {
            display: inline-block;
            padding: 10px 20px;
            margin-right: 10px;
            background: #3498db;
            color: white;
            text-decoration: none;
            border-radius: 4px;
        }
        .nav a:hover {
            background: #2980b9;
        }
        .nav a.active {
            background: #e74c3c;
        }
        .form-group {
            margin-bottom: 15px;
        }
        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        .form-group input, .form-group select, .form-group textarea {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            box-sizing: border-box;
        }
        .btn {
            background: #27ae60;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        .btn:hover {
            background: #219a52;
        }
        .btn-secondary {
            background: #95a5a6;
        }
        .btn-secondary:hover {
            background: #7f8c8d;
        }
        .alert {
            padding: 15px;
            margin-bottom: 20px;
            border: 1px solid transparent;
            border-radius: 4px;
        }
        .alert-success {
            color: #155724;
            background-color: #d4edda;
            border-color: #c3e6cb;
        }
        .alert-error {
            color: #721c24;
            background-color: #f8d7da;
            border-color: #f5c6cb;
        }
        .status-info {
            background: #e8f4f8;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 20px;
        }
        .user-card {
            border: 1px solid #ddd;
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 4px;
            background: #f9f9f9;
        }
        .json-display {
            background: #2c3e50;
            color: #ecf0f1;
            padding: 15px;
            border-radius: 4px;
            overflow-x: auto;
            font-family: monospace;
            white-space: pre-wrap;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>TGM-Adapter Frontend</h1>
        <p>Flask Frontend → TGM-Adapter Middleware → Backend API</p>
    </div>
    
    <div class="nav">
        <a href="/" {% if request.endpoint == 'index' %}class="active"{% endif %}>Dashboard</a>
        <a href="/users" {% if request.endpoint == 'users' %}class="active"{% endif %}>Benutzer</a>
        <a href="/data" {% if request.endpoint == 'data_processor' %}class="active"{% endif %}>Daten verarbeiten</a>
        <a href="/status" {% if request.endpoint == 'status' %}class="active"{% endif %}>System Status</a>
    </div>
    
    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            {% for category, message in messages %}
                <div class="alert alert-{{ category }}">{{ message }}</div>
            {% endfor %}
        {% endif %}
    {% endwith %}
    
    {{ content }}
</body>
</html>
"""

@app.route('/')
def index():
    """Dashboard page"""
    # Get system status from middleware
    status_data, error = call_middleware('GET', '/adapter/status')
    health_data, health_error = call_middleware('GET', '/adapter/health')
    
    content = f"""
    <div class="container">
        <h2>Dashboard</h2>
        <p>Willkommen beim TGM-Adapter Frontend. Diese Anwendung kommuniziert über das Middleware-System mit dem Backend.</p>
        
        <div class="status-info">
            <h3>System Status</h3>
            {'<p>Middleware: ✅ Verfügbar</p>' if status_data else '<p>Middleware: ❌ Nicht verfügbar</p>'}
            {'<p>Backend: ✅ Verfügbar</p>' if health_data and health_data.get('success') else '<p>Backend: ❌ Nicht verfügbar</p>'}
        </div>
        
        <div class="container">
            <h3>Verfügbare Funktionen</h3>
            <ul>
                <li><strong>Benutzer:</strong> Anzeigen, Erstellen und Verwalten von Benutzern</li>
                <li><strong>Daten verarbeiten:</strong> Senden von Daten zur Verarbeitung an das Backend</li>
                <li><strong>System Status:</strong> Anzeigen von System- und Middleware-Informationen</li>
            </ul>
        </div>
        
        {'<div class="json-display">' + json.dumps(status_data, indent=2, ensure_ascii=False) + '</div>' if status_data else ''}
    </div>
    """
    
    return render_template_string(BASE_TEMPLATE, content=content)

@app.route('/users')
def users():
    """Users management page"""
    users_data, error = call_middleware('GET', '/adapter/users')
    
    if error:
        flash(f'Fehler beim Laden der Benutzer: {error}', 'error')
        users_list = []
    else:
        users_list = users_data.get('data', []) if users_data and users_data.get('success') else []
    
    content = f"""
    <div class="container">
        <h2>Benutzerverwaltung</h2>
        
        <h3>Neuen Benutzer erstellen</h3>
        <form method="POST" action="/users/create">
            <div class="form-group">
                <label for="name">Name:</label>
                <input type="text" id="name" name="name" required>
            </div>
            <div class="form-group">
                <label for="email">E-Mail:</label>
                <input type="email" id="email" name="email" required>
            </div>
            <div class="form-group">
                <label for="role">Rolle:</label>
                <select id="role" name="role">
                    <option value="user">Benutzer</option>
                    <option value="admin">Administrator</option>
                </select>
            </div>
            <button type="submit" class="btn">Benutzer erstellen</button>
        </form>
    </div>
    
    <div class="container">
        <h3>Vorhandene Benutzer ({len(users_list)})</h3>
        {''.join([f'''
        <div class="user-card">
            <strong>{user["name"]}</strong> ({user["role"]})<br>
            <small>ID: {user["id"]} | E-Mail: {user["email"]}</small>
        </div>
        ''' for user in users_list])}
        
        {f'<div class="json-display">{json.dumps(users_data, indent=2, ensure_ascii=False)}</div>' if users_data else ''}
    </div>
    """
    
    return render_template_string(BASE_TEMPLATE, content=content)

@app.route('/users/create', methods=['POST'])
def create_user():
    """Create new user"""
    user_data = {
        'name': request.form.get('name'),
        'email': request.form.get('email'),
        'role': request.form.get('role', 'user')
    }
    
    result, error = call_middleware('POST', '/adapter/users', user_data)
    
    if error:
        flash(f'Fehler beim Erstellen des Benutzers: {error}', 'error')
    elif result and result.get('success'):
        flash(f'Benutzer "{user_data["name"]}" wurde erfolgreich erstellt!', 'success')
    else:
        flash(f'Fehler: {result.get("error", "Unbekannter Fehler")}', 'error')
    
    return redirect(url_for('users'))

@app.route('/data')
def data_processor():
    """Data processing page"""
    content = """
    <div class="container">
        <h2>Daten verarbeiten</h2>
        <p>Senden Sie Daten zur Verarbeitung über das Middleware-System an das Backend.</p>
        
        <form method="POST" action="/data/process">
            <div class="form-group">
                <label for="data_type">Datentyp:</label>
                <select id="data_type" name="data_type">
                    <option value="text">Text</option>
                    <option value="json">JSON</option>
                    <option value="number">Zahl</option>
                </select>
            </div>
            <div class="form-group">
                <label for="data_content">Dateninhalt:</label>
                <textarea id="data_content" name="data_content" rows="5" placeholder="Geben Sie hier Ihre Daten ein..."></textarea>
            </div>
            <div class="form-group">
                <label for="priority">Priorität:</label>
                <select id="priority" name="priority">
                    <option value="low">Niedrig</option>
                    <option value="normal" selected>Normal</option>
                    <option value="high">Hoch</option>
                </select>
            </div>
            <button type="submit" class="btn">Daten verarbeiten</button>
        </form>
    </div>
    """
    
    return render_template_string(BASE_TEMPLATE, content=content)

@app.route('/data/process', methods=['POST'])
def process_data():
    """Process data through middleware"""
    data_to_process = {
        'type': request.form.get('data_type'),
        'content': request.form.get('data_content'),
        'priority': request.form.get('priority'),
        'submitted_at': datetime.now().isoformat(),
        'frontend': 'TGM-Adapter Frontend'
    }
    
    result, error = call_middleware('POST', '/adapter/data', data_to_process)
    
    if error:
        flash(f'Fehler bei der Datenverarbeitung: {error}', 'error')
        return redirect(url_for('data_processor'))
    
    content = f"""
    <div class="container">
        <h2>Datenverarbeitung - Ergebnis</h2>
        <div class="alert alert-success">
            Daten wurden erfolgreich verarbeitet!
        </div>
        
        <h3>Verarbeitungsresultat:</h3>
        <div class="json-display">{json.dumps(result, indent=2, ensure_ascii=False)}</div>
        
        <a href="/data" class="btn btn-secondary">Weitere Daten verarbeiten</a>
    </div>
    """
    
    return render_template_string(BASE_TEMPLATE, content=content)

@app.route('/status')
def status():
    """System status page"""
    adapter_status, adapter_error = call_middleware('GET', '/adapter/status')
    system_info, system_error = call_middleware('GET', '/adapter/system')
    health_check, health_error = call_middleware('GET', '/adapter/health')
    
    content = f"""
    <div class="container">
        <h2>System Status</h2>
        
        <div class="container">
            <h3>TGM-Adapter Middleware Status</h3>
            {f'<div class="json-display">{json.dumps(adapter_status, indent=2, ensure_ascii=False)}</div>' if adapter_status else f'<div class="alert alert-error">Fehler: {adapter_error}</div>'}
        </div>
        
        <div class="container">
            <h3>Backend System Info</h3>
            {f'<div class="json-display">{json.dumps(system_info, indent=2, ensure_ascii=False)}</div>' if system_info else f'<div class="alert alert-error">Fehler: {system_error}</div>'}
        </div>
        
        <div class="container">
            <h3>Backend Health Check</h3>
            {f'<div class="json-display">{json.dumps(health_check, indent=2, ensure_ascii=False)}</div>' if health_check else f'<div class="alert alert-error">Fehler: {health_error}</div>'}
        </div>
    </div>
    """
    
    return render_template_string(BASE_TEMPLATE, content=content)

@app.route('/api/test')
def api_test():
    """Test endpoint for direct API access"""
    return jsonify({
        "service": "Frontend API",
        "status": "running", 
        "timestamp": datetime.now().isoformat(),
        "middleware_url": MIDDLEWARE_URL
    })

if __name__ == '__main__':
    print("Starting Frontend Flask Application...")
    print("Middleware URL:", MIDDLEWARE_URL)
    print("Available pages:")
    print("  / - Dashboard")
    print("  /users - User management")
    print("  /data - Data processing")
    print("  /status - System status")
    print("  /api/test - API test endpoint")
    app.run(host='0.0.0.0', port=8080, debug=True)