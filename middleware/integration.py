"""
Middleware Integration - Anbindung an Frontend & Backend
=========================================================

Dieses Modul stellt die Integration zwischen der Adapter Middleware
und dem bestehenden Frontend (Flask) sowie Backend (McTime API) her.

WICHTIG: 
- Das Backend (api_handler.py) bleibt UNVERÄNDERT
- Das Frontend (app.py) bleibt UNVERÄNDERT
- Diese Integration kann OPTIONAL verwendet werden

Verwendung:
    1. Direkter Import der Middleware im Frontend
    2. Oder Nutzung dieser Integrations-Klasse als Wrapper
"""

import os
import sys
from typing import Dict, List, Optional, Any
from functools import wraps

# Backend-Pfad zur Laufzeit hinzufügen
_backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
if _backend_path not in sys.path:
    sys.path.insert(0, _backend_path)

from .adapter import AdapterMiddleware, get_middleware
from .transformer import DataTransformer
from .error_handler import MiddlewareError, ErrorHandler


class MiddlewareIntegration:
    """
    Integrations-Schicht die als Brücke zwischen Frontend und Middleware dient.
    
    Diese Klasse kann in app.py verwendet werden, um die Middleware zu nutzen,
    ohne den bestehenden Code zu ändern.
    
    Beispiel in app.py:
        from middleware.integration import MiddlewareIntegration
        
        integration = MiddlewareIntegration()
        
        # Statt backend_service.get_form_data()
        form_data = integration.get_form_data()
    """
    
    def __init__(self, api_key: str = None):
        """
        Initialisiert die Integration.
        
        Args:
            api_key: McTime API Key (aus Umgebungsvariable empfohlen)
        """
        self.api_key = api_key or os.getenv('MCTIME_API_KEY')
        self._middleware = None
        self._backend_fallback = None
    
    @property
    def middleware(self) -> AdapterMiddleware:
        """Lazy Loading der Middleware"""
        if self._middleware is None:
            self._middleware = get_middleware(self.api_key)
        return self._middleware
    
    @property
    def backend_fallback(self):
        """Fallback zum Original-Backend falls Middleware fehlschlägt"""
        if self._backend_fallback is None:
            try:
                # Import erfolgt hier da sys.path bereits konfiguriert ist
                import api_handler
                if self.api_key:
                    self._backend_fallback = api_handler.BackendService(self.api_key)
            except ImportError:
                pass
        return self._backend_fallback
    
    def with_fallback(self, middleware_func, backend_func):
        """
        Führt Middleware-Funktion aus mit Backend-Fallback.
        
        Args:
            middleware_func: Callable für Middleware
            backend_func: Callable für Backend-Fallback
            
        Returns:
            Ergebnis der Funktion
        """
        try:
            return middleware_func()
        except Exception as e:
            print(f"Middleware Fehler: {e}. Verwende Backend-Fallback...")
            if self.backend_fallback:
                return backend_func()
            raise
    
    # =========================================================================
    # FORM DATA METHODEN (kompatibel mit app.py)
    # =========================================================================
    
    def get_form_data(self) -> Dict:
        """
        Holt Formulardaten (Organisationen, Mitarbeiter).
        Kompatibel mit backend_service.get_form_data()
        
        Returns:
            Dict mit organizations, employees, status
        """
        return self.with_fallback(
            lambda: self.middleware.get_form_data(),
            lambda: self.backend_fallback.get_form_data()
        )
    
    def process_form_request(self, form_data: Dict) -> Dict:
        """
        Verarbeitet Formular-Anfrage.
        Kompatibel mit backend_service.process_form_request()
        
        Args:
            form_data: Dict mit firma, mitarbeiter, von, bis
            
        Returns:
            Dict mit status und data
        """
        return self.with_fallback(
            lambda: self.middleware.process_form_request(form_data),
            lambda: self.backend_fallback.process_form_request(form_data)
        )
    
    # =========================================================================
    # MITARBEITER METHODEN
    # =========================================================================
    
    def get_employees(self, organization_id: Optional[str] = None) -> List[Dict]:
        """
        Holt Mitarbeiterliste.
        
        Args:
            organization_id: Optional - Filter nach Organisation
            
        Returns:
            Liste von Mitarbeitern
        """
        return self.middleware.get_employees(organization_id)
    
    def get_employee_email(self, employee_id: str) -> Optional[str]:
        """
        Holt E-Mail eines Mitarbeiters.
        
        Args:
            employee_id: ID des Mitarbeiters
            
        Returns:
            E-Mail-Adresse oder None
        """
        return self.middleware.get_employee_email(employee_id)
    
    # =========================================================================
    # ZEITDATEN METHODEN
    # =========================================================================
    
    def get_time_entries(
        self,
        employee_id: str,
        date_from: str,
        date_to: str,
        organization_id: Optional[str] = None
    ) -> List[Dict]:
        """
        Holt Zeiteinträge für einen Mitarbeiter.
        
        Args:
            employee_id: ID des Mitarbeiters
            date_from: Startdatum (dd.mm.yyyy oder yyyy-mm-dd)
            date_to: Enddatum
            organization_id: Optional - Organisation
            
        Returns:
            Liste von Zeiteinträgen
        """
        return self.middleware.get_time_entries(
            employee_id=employee_id,
            date_from=date_from,
            date_to=date_to,
            organization_id=organization_id
        )
    
    # =========================================================================
    # CSV EXPORT
    # =========================================================================
    
    def export_to_csv(self, time_entries: List[Dict]) -> str:
        """
        Exportiert Zeiteinträge als CSV.
        
        Args:
            time_entries: Liste von Zeiteinträgen
            
        Returns:
            CSV-String
        """
        return self.middleware.export_to_csv(time_entries)
    
    def get_time_data_csv(
        self,
        employee_id: str,
        date_from: str,
        date_to: str,
        organization_id: Optional[str] = None
    ) -> str:
        """
        Holt Zeitdaten und exportiert sie direkt als CSV.
        
        Args:
            employee_id: ID des Mitarbeiters
            date_from: Startdatum
            date_to: Enddatum
            organization_id: Optional - Organisation
            
        Returns:
            CSV-String
        """
        return self.middleware.export_time_data_csv(
            employee_id=employee_id,
            date_from=date_from,
            date_to=date_to,
            organization_id=organization_id
        )
    
    # =========================================================================
    # STATUS & VERBINDUNG
    # =========================================================================
    
    def get_connection_status(self) -> Dict:
        """
        Gibt den Verbindungsstatus zurück.
        
        Returns:
            Dict mit Status-Informationen
        """
        return self.middleware.get_connection_status()
    
    def validate_connection(self) -> bool:
        """
        Prüft ob die Verbindung zur API funktioniert.
        
        Returns:
            True wenn verbunden, False sonst
        """
        return self.middleware.validate_api_key()


# =========================================================================
# FLASK DECORATOR FÜR MIDDLEWARE-ROUTES
# =========================================================================

def middleware_route(func):
    """
    Decorator für Flask-Routes die die Middleware nutzen.
    Fügt automatisches Error-Handling hinzu.
    
    Verwendung:
        @app.route('/api/data')
        @middleware_route
        def get_data():
            integration = MiddlewareIntegration()
            return integration.get_time_entries(...)
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except MiddlewareError as e:
            from flask import jsonify
            return jsonify(e.to_dict()), 400
        except Exception as e:
            from flask import jsonify
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    return wrapper


# =========================================================================
# GLOBALE INSTANZ
# =========================================================================

_integration_instance = None

def get_integration(api_key: str = None) -> MiddlewareIntegration:
    """
    Gibt die Singleton-Instanz der Integration zurück.
    
    Args:
        api_key: Optional - API-Key
        
    Returns:
        MiddlewareIntegration Instanz
    """
    global _integration_instance
    
    if _integration_instance is None:
        _integration_instance = MiddlewareIntegration(api_key)
    
    return _integration_instance
