from flask import Flask, render_template, jsonify, request, Response
import os
import io
import csv
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from functools import lru_cache
import hashlib
import json
import logging

# Configure logging to handle UTF-8
logging.basicConfig(level=logging.INFO, format='[%(name)s] %(message)s')
logger = logging.getLogger(__name__)

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

# ==================== PERFORMANCE CACHE ====================
# Cache für API-Daten (TTL: 5 Minuten)
_cache = {}
_cache_ttl = 300  # 5 Minuten

# ==================== REQUEST TRACKING ====================
# Globale Request-Statistiken für das Dashboard
_request_stats = {
    "total_requests": 0,
    "successful_requests": 0,
    "failed_requests": 0,
    "response_times": [],  # Letzte 100 Response-Zeiten
    "start_time": time.time()
}

def track_request(success: bool, response_time_ms: float = 0):
    """Trackt einen API-Request für Statistiken"""
    _request_stats["total_requests"] += 1
    if success:
        _request_stats["successful_requests"] += 1
    else:
        _request_stats["failed_requests"] += 1

    # Response-Zeit speichern (max 100)
    _request_stats["response_times"].append(response_time_ms)
    if len(_request_stats["response_times"]) > 100:
        _request_stats["response_times"] = _request_stats["response_times"][-100:]

def get_request_stats():
    """Gibt aktuelle Request-Statistiken zurück"""
    avg_time = 0
    if _request_stats["response_times"]:
        avg_time = sum(_request_stats["response_times"]) / len(_request_stats["response_times"])

    return {
        "total_requests": _request_stats["total_requests"],
        "successful_requests": _request_stats["successful_requests"],
        "failed_requests": _request_stats["failed_requests"],
        "avg_response_time_ms": round(avg_time, 1)
    }

def get_cache_key(prefix, **kwargs):
    """Erstellt einen eindeutigen Cache-Key"""
    data = json.dumps(kwargs, sort_keys=True)
    return f"{prefix}_{hashlib.md5(data.encode()).hexdigest()}"

def get_cached(key):
    """Holt Daten aus Cache wenn noch gültig"""
    if key in _cache:
        data, timestamp = _cache[key]
        if time.time() - timestamp < _cache_ttl:
            return data
        del _cache[key]
    return None

def set_cached(key, data):
    """Speichert Daten im Cache"""
    _cache[key] = (data, time.time())

def clear_cache():
    """Leert den Cache"""
    global _cache
    _cache = {}

if not API_KEY:
    print("WARNING: MCTIME_API_KEY environment variable not set!")
    print("Please configure your .env file with MCTIME_API_KEY")

# Initialisiere Backend Service
try:
    backend_service = BackendService(API_KEY) if API_KEY else None
    if backend_service:
        print("[OK] Backend Service initialisiert")
except Exception as e:
    print(f"[FEHLER] Backend-Fehler: {e}")
    backend_service = None

# Initialisiere Middleware (für zusätzliche Features)
try:
    middleware = get_middleware(API_KEY) if API_KEY else None
    if middleware:
        print("[OK] Middleware initialisiert")
except Exception as e:
    print(f"[FEHLER] Middleware-Fehler: {e}")
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

@app.route('/api-config')
def api_config():
    """Middleware-Konfigurationsseite"""
    return render_template('api_config.html')

@app.route('/charts')
def charts():
    """Charts und Statistiken Seite"""
    return render_template('charts.html')

@app.route('/page_1')
def page_1():
    return render_template('321.html')

@app.route('/api/status')
def system_status():
    """Gibt den erweiterten Status von Backend und Middleware zurück"""

    # Middleware-Features prüfen
    middleware_features = {
        "authentication": {
            "name": "Authentifizierung",
            "status": False,
            "description": "API-Key basierte Authentifizierung"
        },
        "rate_limiting": {
            "name": "Rate Limiting",
            "status": False,
            "description": "Anfragenlimitierung zum Schutz der API"
        },
        "email_service": {
            "name": "E-Mail Service",
            "status": False,
            "description": "SMTP-basierter E-Mail-Versand"
        },
        "data_transformation": {
            "name": "Datentransformation",
            "status": False,
            "description": "JSON → CSV Konvertierung"
        },
        "multi_employee": {
            "name": "Multi-Mitarbeiter",
            "status": False,
            "description": "Mehrere Mitarbeiter gleichzeitig verarbeiten"
        },
        "csv_export": {
            "name": "CSV Export",
            "status": False,
            "description": "WorkExpert-kompatibles CSV-Format"
        },
        "caching": {
            "name": "Caching",
            "status": False,
            "description": "Performance-Cache für API-Daten"
        },
        "api_v2": {
            "name": "API v2 Kompatibilität",
            "status": False,
            "description": "McTime API Version 2 Support"
        }
    }

    # Health-Statistiken - nutze App-Level Tracking
    app_stats = get_request_stats()
    health_stats = {
        "uptime": "N/A",
        "requests_total": app_stats["total_requests"],
        "requests_success": app_stats["successful_requests"],
        "requests_failed": app_stats["failed_requests"],
        "avg_response_time": app_stats["avg_response_time_ms"],
        "cache_entries": len(_cache),
        "cache_hit_rate": "N/A"
    }

    if middleware:
        # Authentication ist aktiv wenn API-Key gesetzt
        middleware_features["authentication"]["status"] = bool(middleware.api_key)

        # Rate Limiting (Request-Handler prüfen)
        if hasattr(middleware, 'request_handler') and middleware.request_handler:
            middleware_features["rate_limiting"]["status"] = True

        # E-Mail Service aktiv wenn MailManager existiert
        if hasattr(middleware, 'mail') and middleware.mail:
            middleware_features["email_service"]["status"] = True

        # Datentransformation (immer aktiv wenn Middleware)
        middleware_features["data_transformation"]["status"] = True

        # Multi-Mitarbeiter (prüfe ob Methode existiert)
        if hasattr(middleware, 'send_multi_employee_report'):
            middleware_features["multi_employee"]["status"] = True

        # CSV Export
        if hasattr(middleware, 'convert_to_csv'):
            middleware_features["csv_export"]["status"] = True

        # Caching (aktiv wenn Cache existiert)
        middleware_features["caching"]["status"] = len(_cache) >= 0  # Immer True

        # API v2 Kompatibilität
        if hasattr(middleware, 'request_handler') and middleware.request_handler:
            if hasattr(middleware.request_handler, 'base_url'):
                middleware_features["api_v2"]["status"] = "v2" in middleware.request_handler.base_url

    status = {
        "backend": {
            "available": backend_service is not None,
            "api_configured": bool(API_KEY)
        },
        "middleware": {
            "available": middleware is not None,
            "status": middleware.get_connection_status() if middleware else None,
            "features": middleware_features
        },
        "health": health_stats
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

@app.route('/api/stats/reset', methods=['POST'])
def reset_stats():
    """Setzt die Request-Statistiken und den Cache zurück"""
    global _request_stats, _cache
    print("=== RESET STATS & CACHE CALLED ===")
    
    # Reset Request-Statistiken
    _request_stats = {
        "total_requests": 0,
        "successful_requests": 0,
        "failed_requests": 0,
        "response_times": [],
        "start_time": time.time()
    }
    
    # Reset Cache komplett
    _cache = {}
    
    print(f"[OK] Stats nach Reset: {_request_stats}")
    print(f"[OK] Cache geleert!")
    
    return jsonify({
        "status": "success", 
        "message": "Statistiken und Cache vollständig zurückgesetzt",
        "stats": _request_stats
    })

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
    start_time = time.time()
    try:
        form_data = request.get_json()
        print("=== HYBRID API CALL ===")
        print(f"Received form_data: {form_data}")

        if not form_data:
            print("ERROR: No JSON data provided")
            track_request(False, 0)
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
            track_request(False, (time.time() - start_time) * 1000)
            return jsonify({
                "status": "error",
                "message": "Weder Backend noch Middleware verfügbar"
            }), 500

        response_time = (time.time() - start_time) * 1000
        print(f"Result: {result}")

        if result.get("status") == "error":
            print(f"Service returned error: {result.get('message')}")
            track_request(False, response_time)
            return jsonify(result), 400

        print(f"Success! Returning {len(result.get('data', {}).get('timeEntries', []))} time entries")
        track_request(True, response_time)
        return jsonify(result)

    except Exception as e:
        track_request(False, (time.time() - start_time) * 1000)
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
    start_time = time.time()
    if not middleware:
        track_request(False, 0)
        return jsonify({"error": "Middleware nicht initialisiert"}), 500

    try:
        org_id = request.args.get('organization_id')
        org_name = request.args.get('organization_name')
        employees = middleware.get_employees(org_id, org_name)

        response_time = (time.time() - start_time) * 1000
        print(f"API /api/employees - org_id: {org_id}, org_name: {org_name}, gefunden: {len(employees)} Mitarbeiter")
        track_request(True, response_time)
        return jsonify(employees)
    except Exception as e:
        track_request(False, (time.time() - start_time) * 1000)
        return jsonify({"error": str(e)}), 500


@app.route('/api/organizations')
def get_organizations():
    """Holt Organisationsliste über Middleware"""
    start_time = time.time()
    if not middleware:
        track_request(False, 0)
        return jsonify({"error": "Middleware nicht initialisiert"}), 500

    try:
        organizations = middleware.get_organizations()
        track_request(True, (time.time() - start_time) * 1000)
        return jsonify(organizations)
    except Exception as e:
        track_request(False, (time.time() - start_time) * 1000)
        return jsonify({"error": str(e)}), 500


@app.route('/api/cache/clear', methods=['POST'])
def api_clear_cache():
    """Cache manuell leeren für frische Daten"""
    clear_cache()
    return jsonify({"status": "success", "message": "Cache geleert"})


@app.route('/api/cache/status')
def api_cache_status():
    """Zeigt Cache-Status"""
    entries = len(_cache)
    return jsonify({
        "entries": entries,
        "ttl_seconds": _cache_ttl,
        "keys": list(_cache.keys())[:20]  # Max 20 Keys anzeigen
    })


@app.route('/api/test', methods=['GET'])
def api_test():
    """Einfacher Test-Endpoint"""
    return jsonify({"status": "ok", "message": "API works!"})

@app.route('/api/chart-stats')
def get_chart_stats():
    """
    Holt aggregierte Statistiken für Charts
    
    Query-Parameter:
    - filter: 'month' | 'year' | 'alltime' | 'custom' (default: 'month')
    - month: 'YYYY-MM' Format für spezifischen Monat (nur wenn filter='month')
    - from: 'YYYY-MM-DD' Format für Start-Datum (nur wenn filter='custom')
    - to: 'YYYY-MM-DD' Format für End-Datum (nur wenn filter='custom')
    
    Gibt zurück: Statistiken für alle Mitarbeiter im gewählten Zeitraum
    """
    from datetime import datetime, timedelta
    from collections import defaultdict
    import calendar
    
    # Deutsche Monatsnamen
    german_months = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 
                     'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember']
    
    if not backend_service and not middleware:
        return jsonify({"error": "Kein Service verfügbar"}), 500
    
    # Filter auswerten
    time_filter = request.args.get('filter', 'month')
    month_param = request.args.get('month', None)  # YYYY-MM Format
    custom_from = request.args.get('from', None)  # YYYY-MM-DD Format
    custom_to = request.args.get('to', None)      # YYYY-MM-DD Format
    
    today = datetime.now()
    
    # Hilfsfunktion: Monatsbereiche generieren
    def generate_month_ranges(start_date, end_date):
        """Generiert eine Liste von (start, end) Tuples für jeden Monat im Bereich"""
        ranges = []
        current = start_date.replace(day=1)
        while current <= end_date:
            month_start = current.strftime('%Y-%m-%d')
            # Letzter Tag des Monats
            last_day = calendar.monthrange(current.year, current.month)[1]
            month_end_date = current.replace(day=last_day)
            if month_end_date > end_date:
                month_end_date = end_date
            month_end = month_end_date.strftime('%Y-%m-%d')
            ranges.append((month_start, month_end))
            
            # Nächster Monat
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)
        return ranges
    
    # Datumsbereich basierend auf Filter berechnen
    if time_filter == 'month':
        if month_param:
            # Spezifischer Monat aus Parameter
            try:
                year, month = map(int, month_param.split('-'))
                target_date = datetime(year, month, 1)
                date_from = target_date.strftime('%Y-%m-%d')
                last_day = calendar.monthrange(year, month)[1]
                date_to = target_date.replace(day=last_day).strftime('%Y-%m-%d')
                filter_label = f"{german_months[month-1]} {year}"
            except:
                # Fallback auf aktuellen Monat
                date_from = today.replace(day=1).strftime('%Y-%m-%d')
                last_day = calendar.monthrange(today.year, today.month)[1]
                date_to = today.replace(day=last_day).strftime('%Y-%m-%d')
                filter_label = f"{german_months[today.month-1]} {today.year}"
        else:
            # Aktueller Monat
            date_from = today.replace(day=1).strftime('%Y-%m-%d')
            last_day = calendar.monthrange(today.year, today.month)[1]
            date_to = today.replace(day=last_day).strftime('%Y-%m-%d')
            filter_label = f"{german_months[today.month-1]} {today.year}"
        month_ranges = [(date_from, date_to)]  # Nur ein Monat
        
    elif time_filter == 'custom':
        # Benutzerdefinierter Datumsbereich
        if not custom_from or not custom_to:
            print("[WARNING] Custom Filter ohne Datumsangaben - Fallback auf aktuellen Monat")
            # Fallback auf aktuellen Monat
            date_from = today.replace(day=1).strftime('%Y-%m-%d')
            last_day = calendar.monthrange(today.year, today.month)[1]
            date_to = today.replace(day=last_day).strftime('%Y-%m-%d')
            filter_label = f"{german_months[today.month-1]} {today.year}"
            month_ranges = [(date_from, date_to)]
        else:
            try:
                from_date = datetime.strptime(custom_from, '%Y-%m-%d')
                to_date = datetime.strptime(custom_to, '%Y-%m-%d')
                date_from = custom_from
                date_to = custom_to
                # Format: "01. Jan - 31. Dez 2025"
                from_label = from_date.strftime('%d.%m.%Y')
                to_label = to_date.strftime('%d.%m.%Y')
                filter_label = f"{from_label} bis {to_label}"
                print(f"[OK] Custom Filter: {date_from} bis {date_to}")
                
                # Monats-Bereiche aus dem benutzerdefinierten Bereich generieren
                month_ranges = generate_month_ranges(from_date, to_date)
            except Exception as e:
                print(f"[ERROR] Fehler beim Parsen von Custom-Daten: {e}")
                # Fallback
                date_from = today.replace(day=1).strftime('%Y-%m-%d')
                last_day = calendar.monthrange(today.year, today.month)[1]
                date_to = today.replace(day=last_day).strftime('%Y-%m-%d')
                filter_label = f"{german_months[today.month-1]} {today.year}"
                month_ranges = [(date_from, date_to)]
        
    elif time_filter == 'year':
        # Aktuelles Jahr - Monat für Monat abrufen (API-Limit umgehen)
        start_date = datetime(today.year, 1, 1)
        end_date = today
        date_from = start_date.strftime('%Y-%m-%d')
        date_to = end_date.strftime('%Y-%m-%d')
        filter_label = f"Jahr {today.year}"
        month_ranges = generate_month_ranges(start_date, end_date)
        
    else:  # alltime - September 2025 bis heute
        start_date = datetime(2025, 9, 1)
        end_date = today
        date_from = start_date.strftime('%Y-%m-%d')
        date_to = end_date.strftime('%Y-%m-%d')
        filter_label = "Alle Daten (ab Sep 2025)"
        month_ranges = generate_month_ranges(start_date, end_date)
    
    try:
        # Cache-Key für diese Anfrage
        cache_key = get_cache_key('chart_stats', filter=time_filter, month=month_param, date_from=date_from, date_to=date_to)
        cached_result = get_cached(cache_key)
        if cached_result:
            print(f"[CACHE] Chart-Stats aus Cache geladen!")
            return jsonify(cached_result)
        
        start_time = time.time()
        
        # Alle Mitarbeiter holen
        if backend_service:
            employees = backend_service.get_form_data().get('employees', [])
        elif middleware:
            employees = middleware.get_employees()
        else:
            employees = []
        
        print(f"[CHART-STATS] {len(employees)} Mitarbeiter, {len(month_ranges)} Monats-Bereiche", file=sys.stderr)
        
        # Statistiken sammeln
        total_hours = 0.0
        employee_stats = []
        weekday_hours = defaultdict(float)  # 0=Mo, 1=Di, ..., 6=So
        monthly_hours = defaultdict(float)  # "2024-09", "2024-10", etc.
        daily_hours = defaultdict(float)    # "2024-09-01", "2024-09-02", etc.
        all_time_entries = []
        
        # ==================== PARALLELE VERARBEITUNG ====================
        def fetch_employee_data(emp):
            """Holt Daten für einen Mitarbeiter (wird parallel ausgeführt)"""
            emp_id = emp.get('id') or emp.get('value')
            emp_name = emp.get('name') or emp.get('label', 'Unbekannt')
            
            if not emp_id:
                return None
            
            # Cache für einzelne Mitarbeiter
            emp_cache_key = get_cache_key('emp_data', emp_id=emp_id, date_from=date_from, date_to=date_to)
            cached_emp = get_cached(emp_cache_key)
            if cached_emp:
                return cached_emp
            
            time_entries = []
            for m_start, m_end in month_ranges:
                try:
                    if backend_service:
                        entries = backend_service.mctime_api.get_time_entries(
                            employee_id=emp_id,
                            date_from=m_start,
                            date_to=m_end
                        )
                    elif middleware:
                        entries = middleware.get_time_entries(
                            employee_id=emp_id,
                            date_from=m_start,
                            date_to=m_end
                        )
                    else:
                        entries = []
                    time_entries.extend(entries)
                except Exception as e:
                    continue
            
            result = {
                'emp_id': emp_id,
                'emp_name': emp_name,
                'time_entries': time_entries
            }
            
            # Ergebnis cachen
            set_cached(emp_cache_key, result)
            return result
        
        # Parallel ausführen mit ThreadPool (max 10 gleichzeitige Anfragen)
        max_workers = min(10, len(employees))  # Max 10 parallel, nicht mehr als MA-Anzahl
        
        print(f"[PARALLEL] Starte parallele Verarbeitung mit {max_workers} Workers...")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Alle Jobs einreichen
            future_to_emp = {executor.submit(fetch_employee_data, emp): emp for emp in employees}
            
            completed = 0
            for future in as_completed(future_to_emp):
                completed += 1
                result = future.result()
                
                if not result:
                    continue
                
                emp_name = result['emp_name']
                time_entries = result['time_entries']
                
                # Progress (alle 10 MA)
                if completed % 10 == 0:
                    elapsed = time.time() - start_time
                    print(f"  [PROGRESS] {completed}/{len(employees)} Mitarbeiter verarbeitet ({elapsed:.1f}s)", file=sys.stderr)
                
                emp_total = 0.0
                for entry in time_entries:
                    work_hours = entry.get('actual_work_hours', 0) or 0
                    emp_total += work_hours
                    
                    # Wochentag-Statistik und Tages-Statistik
                    try:
                        from_date = entry.get('from', '')
                        if from_date:
                            dt = datetime.fromisoformat(from_date.replace('Z', '+00:00'))
                            weekday_hours[dt.weekday()] += work_hours
                            
                            # Monats-Statistik
                            month_key = dt.strftime('%Y-%m')
                            monthly_hours[month_key] += work_hours
                            
                            # Tages-Statistik
                            day_key = dt.strftime('%Y-%m-%d')
                            daily_hours[day_key] += work_hours
                    except:
                        pass
                    
                    # Projekt aus comment extrahieren
                    comment = entry.get('comment', '') or ''
                    comment = comment.strip()
                    if comment:
                        project_name = comment.replace('\n', '').strip()
                    else:
                        project_name = entry.get('organizationName', 'Sonstiges') or 'Sonstiges'
                    
                    all_time_entries.append({
                        'name': emp_name,
                        'hours': work_hours,
                        'date': entry.get('date_formatted', ''),
                        'project': project_name
                    })
                
                total_hours += emp_total
                
                if emp_total > 0:
                    employee_stats.append({
                        'name': emp_name,
                        'hours': round(emp_total, 2),
                        'entries': len(time_entries)
                    })
        
        elapsed_total = time.time() - start_time
        print(f"[OK] Alle {len(employees)} Mitarbeiter in {elapsed_total:.1f}s verarbeitet!")
        
        # Wochentage formatieren
        weekday_data = [
            round(weekday_hours.get(0, 0), 1),  # Mo
            round(weekday_hours.get(1, 0), 1),  # Di
            round(weekday_hours.get(2, 0), 1),  # Mi
            round(weekday_hours.get(3, 0), 1),  # Do
            round(weekday_hours.get(4, 0), 1),  # Fr
            round(weekday_hours.get(5, 0), 1),  # Sa
            round(weekday_hours.get(6, 0), 1),  # So
        ]
        
        # Trend-Daten: Bei einzelnem Monat -> Tage anzeigen, sonst -> Monate
        trend_labels = []
        trend_values = []
        
        german_months_short = ['Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun', 
                               'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez']
        
        if time_filter == 'month' or len(monthly_hours) == 1:
            # Einzelner Monat: Zeige tägliche Daten
            sorted_days = sorted(daily_hours.keys())
            for day_key in sorted_days:
                # Format: "01", "02", etc.
                day_num = day_key.split('-')[2]
                trend_labels.append(day_num)
                trend_values.append(round(daily_hours[day_key], 1))
        else:
            # Mehrere Monate: Zeige monatliche Daten
            sorted_months = sorted(monthly_hours.keys())
            for month_key in sorted_months:
                year, month = month_key.split('-')
                month_idx = int(month) - 1
                trend_labels.append(f"{german_months_short[month_idx]} {year[-2:]}")
                trend_values.append(round(monthly_hours[month_key], 1))
        
        # Projekt-Verteilung berechnen
        project_hours = defaultdict(float)
        for entry in all_time_entries:
            project_hours[entry.get('project', 'Sonstiges')] += entry.get('hours', 0)
        
        # Top 5 Projekte
        sorted_projects = sorted(project_hours.items(), key=lambda x: x[1], reverse=True)[:5]
        project_labels = [p[0] for p in sorted_projects]
        project_values = [round(p[1], 1) for p in sorted_projects]
        
        # Mitarbeiter nach Stunden sortieren - TOP 10 für Ranking
        employee_stats.sort(key=lambda x: x['hours'], reverse=True)
        top_employees = employee_stats[:10]  # Nur Top 10 für Chart anzeigen
        total_employees = len(employee_stats)  # Gesamtzahl merken
        
        result = {
            'status': 'success',
            'filter': time_filter,
            'filter_label': filter_label,
            'date_from': date_from,
            'date_to': date_to,
            'kpi': {
                'total_hours': round(total_hours, 1),
                'employee_count': len(employee_stats),
                'entry_count': len(all_time_entries),
                'avg_hours_per_employee': round(total_hours / len(employee_stats), 1) if employee_stats else 0
            },
            'weekday_data': {
                'labels': ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'],
                'values': weekday_data
            },
            'monthly_data': {
                'labels': trend_labels,
                'values': trend_values
            },
            'project_data': {
                'labels': project_labels,
                'values': project_values
            },
            'employee_data': {
                'labels': [e['name'].split()[0] + ' ' + e['name'].split()[-1][0] + '.' if ' ' in e['name'] else e['name'] for e in top_employees],
                'values': [e['hours'] for e in top_employees],
                'full_names': [e['name'] for e in top_employees],
                'total_count': total_employees,
                'showing': len(top_employees)
            }
        }
        
        # Ergebnis cachen für 5 Minuten
        set_cached(cache_key, result)
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error in chart-stats: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


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
        "email_to": "email1@example.com, email2@example.com",  # Mehrere mit Komma
        "email_cc": "cc1@example.com, cc2@example.com",        # Optional: CC Empfänger
        "email_subject": "Custom Subject",                      # Optional: benutzerdefinierter Betreff
        "attach_csv": true,                                     # Optional: CSV anhängen (default: true)
        "message": "Zusätzliche Nachricht",                    # Optional: persönliche Nachricht
        "employee_ids": ["uuid1", "uuid2"],                    # Optional: Multiple employee IDs
        "employee_names": ["Name1", "Name2"]                   # Optional: Multiple employee names
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
        date_from = data.get('date_from')  
        date_to = data.get('date_to')
        
        # Multi-Mitarbeiter Support
        employee_ids = data.get('employee_ids', [])
        employee_names = data.get('employee_names', [])
        
        # Fallback für einzelnen Mitarbeiter
        if not employee_ids:
            employee_id = data.get('employee_id')
            if employee_id:
                # Prüfe ob es komma-getrennte IDs sind
                if ',' in str(employee_id):
                    employee_ids = [e.strip() for e in employee_id.split(',')]
                else:
                    employee_ids = [employee_id]
        
        if not employee_names:
            employee_name = data.get('employee_name', 'Mitarbeiter')
            employee_names = [employee_name]
        
        if not employee_ids or not date_from or not date_to:
            return jsonify({
                'status': 'error',
                'message': 'Pflichtfelder: employee_id(s), date_from, date_to'
            }), 400
        
        # Optionale Felder
        custom_email = data.get('email_to')
        email_cc = data.get('email_cc', '')
        custom_subject = data.get('email_subject')
        attach_csv = data.get('attach_csv', True)
        custom_message = data.get('message', '')
        
        # Normalisiere Datums-Format
        date_from_normalized = middleware._normalize_date(date_from)
        date_to_normalized = middleware._normalize_date(date_to)
        
        print(f"=== MULTI-EMPLOYEE EMAIL REQUEST ===")
        print(f"Employees: {len(employee_ids)} selected")
        print(f"Names: {employee_names}")
        print(f"Period: {date_from_normalized} - {date_to_normalized}")
        print(f"Custom Email (To): {custom_email}")
        print(f"CC Recipients: {email_cc}")
        print(f"Attach CSV: {attach_csv}")
        
        # Sammle Daten für alle ausgewählten Mitarbeiter
        all_time_entries = []
        employee_data = []
        
        for idx, emp_id in enumerate(employee_ids):
            emp_name = employee_names[idx] if idx < len(employee_names) else f"Mitarbeiter {idx+1}"
            
            try:
                entries = middleware.get_time_entries(
                    employee_id=emp_id,
                    date_from=date_from_normalized,
                    date_to=date_to_normalized
                )
                
                # Füge Name zu jedem Eintrag hinzu
                for entry in entries:
                    entry['name'] = emp_name
                    entry['employee_id'] = emp_id
                
                all_time_entries.extend(entries)
                employee_data.append({
                    'id': emp_id,
                    'name': emp_name,
                    'entry_count': len(entries)
                })
                print(f"  {emp_name}: {len(entries)} Einträge")
            except Exception as e:
                print(f"  Fehler bei {emp_name}: {e}")
        
        if not all_time_entries:
            return jsonify({
                'status': 'error',
                'message': 'Keine Zeiteinträge für die ausgewählten Mitarbeiter gefunden'
            }), 400
        
        # Bestimme ob "Alle" ausgewählt sind
        all_employees = middleware.get_employees()
        is_all_selected = len(employee_ids) == len(all_employees)
        
        # Erstelle E-Mail mit Template
        result = middleware.send_multi_employee_report(
            employees=employee_data,
            time_entries=all_time_entries,
            date_from=date_from,
            date_to=date_to,
            custom_email=custom_email,
            email_cc=email_cc,
            custom_subject=custom_subject,
            attach_csv=attach_csv,
            custom_message=custom_message,
            is_all_employees=is_all_selected
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
    """CSV-Download - Daten über Middleware (unterstützt mehrere Mitarbeiter)"""
    if not middleware:
        return jsonify({"error": "Middleware nicht initialisiert"}), 500
    
    # Filter aus Request-Parametern holen
    company = request.args.get('company')
    employee = request.args.get('employee')  # Kann komma-getrennt sein
    employee_ids = request.args.get('employee_ids')  # JSON array
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    if not date_from or not date_to:
        return jsonify({"error": "Fehlende Parameter: date_from, date_to"}), 400
    
    # Normalisiere Datum
    date_from_normalized = middleware._normalize_date(date_from)
    date_to_normalized = middleware._normalize_date(date_to)
    
    # Multi-Mitarbeiter Support
    employees_to_fetch = []
    
    if employee_ids:
        # JSON array von IDs
        import json
        try:
            employees_to_fetch = json.loads(employee_ids)
        except:
            employees_to_fetch = [employee_ids]
    elif employee:
        # Komma-getrennte IDs oder einzelne ID
        if ',' in str(employee):
            employees_to_fetch = [e.strip() for e in employee.split(',')]
        else:
            employees_to_fetch = [employee]
    
    if not employees_to_fetch:
        return jsonify({"error": "Fehlende Parameter: employee oder employee_ids"}), 400
    
    # Sammle alle Daten
    all_data = []
    for emp_id in employees_to_fetch:
        try:
            data = middleware.get_time_entries(
                employee_id=emp_id,
                date_from=date_from_normalized,
                date_to=date_to_normalized,
                organization_id=company
            )
            # Füge employee_id zu jedem Eintrag hinzu falls nicht vorhanden
            for entry in data:
                if 'employee_id' not in entry:
                    entry['employee_id'] = emp_id
            all_data.extend(data)
        except Exception as e:
            print(f"Fehler beim Laden für {emp_id}: {e}")
    
    if not all_data:
        return jsonify({"error": "Keine Daten gefunden"}), 404
    
    # CSV-Header erstellen - Original McTime Format
    headers = [
        'Personalnummer', 'Vorname', 'Nachname', 'Datum', 'Type',
        'Zeit Beginn', 'Zeit Ende', 'Pause', 'Summe mit Pause', 
        'Summe ohne Pause', 'Projektnummer', 'Auftragsnummer',
        'Projekt / Gruppenname', 'Kommentar'
    ]
    csv_data = [headers]
    
    # Daten hinzufügen im korrekten Format (verwende all_data statt data)
    for row in all_data:
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
            row.get('comment', '')                  # Kommentar
        ])
    
    # CSV in Memory erstellen mit Semicolon-Delimiter (wie im Original)
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';')
    writer.writerows(csv_data)
    
    # Dateiname basierend auf Anzahl Mitarbeiter
    if len(employees_to_fetch) == 1:
        filename = "zeitdaten_export.csv"
    else:
        filename = f"zeitdaten_{len(employees_to_fetch)}_mitarbeiter_export.csv"
    
    # Response erstellen
    response = Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={"Content-disposition": f"attachment; filename={filename}"}
    )
    
    return response


@app.route('/api/test-chart-logic')
def test_chart_logic():
    """Nur zum Testen der internen Logik von get_chart_stats ohne echten API-Call."""
    from datetime import datetime
    
    try:
        # Simuliere einen einfachen Aufruf für den aktuellen Monat
        time_filter = 'month'
        month_param = datetime.now().strftime('%Y-%m')
        
        # Rufe die Logik auf (ohne den Request-Teil)
        # HINWEIS: Dies ist eine vereinfachte Version der Logik in get_chart_stats
        # um schnell Fehler zu finden.
        
        date_from = datetime.now().replace(day=1).strftime('%Y-%m-%d')
        date_to = datetime.now().strftime('%Y-%m-%d')

        if not backend_service:
            return jsonify({"error": "Backend Service nicht verfügbar"}), 500

        employees = backend_service.get_form_data().get('employees', [])
        if not employees:
            return jsonify({"error": "Keine Mitarbeiter gefunden"}), 500

        # Teste nur den ersten Mitarbeiter
        emp_id = employees[0].get('id')
        entries = backend_service.mctime_api.get_time_entries(
            employee_id=emp_id,
            date_from=date_from,
            date_to=date_to
        )

        return jsonify({
            "status": "success",
            "test_filter": time_filter,
            "test_month": month_param,
            "found_employees": len(employees),
            "first_employee_entries": len(entries),
            "first_employee_data": entries[:2] # zeige die ersten 2 Einträge
        })
    except Exception as e:
        import traceback
        return jsonify({
            "status": "error",
            "message": str(e),
            "trace": traceback.format_exc()
        }), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(debug=debug, host='0.0.0.0', port=port)
