"""
Adapter Middleware - Hauptmodul
===============================

Diese Klasse ist die zentrale Komponente der Middleware.
Sie vermittelt zwischen Backend (McTime API) und Frontend (Flask),
ohne dass eines der beiden angepasst werden muss.

Funktionen:
    - API-Key Authentifizierung
    - Request-Ablauf & Fehlerhandling
    - JSON -> CSV Verarbeitung
    - Zeit- & Abwesenheitsdaten abrufen
    - Mitarbeiterverwaltung
"""

import os
import sys
from typing import Dict, List, Optional, Any
from datetime import datetime

# Backend-Pfad zur Laufzeit hinzufügen
_backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
if _backend_path not in sys.path:
    sys.path.insert(0, _backend_path)

# Middleware-Pfad zur Laufzeit hinzufügen (für absolute Imports)
_middleware_path = os.path.dirname(os.path.abspath(__file__))
if _middleware_path not in sys.path:
    sys.path.insert(0, _middleware_path)

from transformer import DataTransformer
from rate_limiter import RateLimiter
from error_handler import MiddlewareError, ErrorHandler


class AdapterMiddleware:
    """
    Adapter Middleware für die McTime API Data Bridge.
    
    Diese Klasse abstrahiert die Kommunikation zwischen Frontend und Backend.
    Das Backend (McTime API) und Frontend (Flask) bleiben unverändert.
    
    Verwendung:
        middleware = AdapterMiddleware(api_key="your-api-key")
        
        # Mitarbeiter abrufen
        employees = middleware.get_employees()
        
        # Zeitdaten abrufen
        time_data = middleware.get_time_entries(
            employee_id="123",
            date_from="01.01.2025",
            date_to="31.01.2025"
        )
        
        # Als CSV exportieren
        csv_data = middleware.export_to_csv(time_data)
    """
    
    def __init__(self, api_key: str = None, config: Dict = None):
        """
        Initialisiert die Adapter Middleware.
        
        Args:
            api_key: McTime API-Key (aus Umgebungsvariable empfohlen)
            config: Optionale Konfigurationsoptionen
        """
        self.api_key = api_key or os.getenv('MCTIME_API_KEY')
        self.config = config or {}
        
        # Komponenten initialisieren
        self.transformer = DataTransformer()
        self.rate_limiter = RateLimiter(
            max_requests=self.config.get('rate_limit', 100),
            time_window=self.config.get('rate_window', 60)
        )
        self.error_handler = ErrorHandler()
        
        # Backend Service (lazy loading)
        self._backend_service = None
        
        # Status
        self._is_connected = False
        self._last_request_time = None
        
    @property
    def backend_service(self):
        """Lazy Loading des Backend Service"""
        if self._backend_service is None:
            try:
                # Import erfolgt hier da sys.path bereits konfiguriert ist
                import api_handler
                if self.api_key:
                    self._backend_service = api_handler.BackendService(self.api_key)
                    self._is_connected = True
                else:
                    raise MiddlewareError(
                        "API_KEY_MISSING",
                        "MCTIME_API_KEY nicht konfiguriert"
                    )
            except ImportError as e:
                raise MiddlewareError(
                    "BACKEND_IMPORT_ERROR",
                    f"Backend-Modul konnte nicht importiert werden: {e}"
                )
        return self._backend_service
    
    # =========================================================================
    # AUTHENTIFIZIERUNG
    # =========================================================================
    
    def validate_api_key(self) -> bool:
        """
        Prüft ob der API-Key gültig ist.
        
        Returns:
            bool: True wenn gültig, False sonst
        """
        if not self.api_key:
            return False
        
        try:
            # Test-Request um Key zu validieren
            orgs = self.backend_service.mctime_api.get_organizations()
            return len(orgs) > 0 or True  # Leere Liste ist auch OK
        except Exception:
            return False
    
    def get_connection_status(self) -> Dict:
        """
        Gibt den aktuellen Verbindungsstatus zurück.
        
        Returns:
            Dict mit Status-Informationen
        """
        return {
            'connected': self._is_connected,
            'api_key_configured': bool(self.api_key),
            'last_request': self._last_request_time.isoformat() if self._last_request_time else None,
            'rate_limit_remaining': self.rate_limiter.get_remaining(),
            'status': 'Verbunden' if self._is_connected else 'Nicht verbunden'
        }
    
    # =========================================================================
    # DATEN ABRUFEN - Mitarbeiter & Organisationen
    # =========================================================================
    
    def get_organizations(self) -> List[Dict]:
        """
        Ruft die Liste aller Organisationen/Firmen ab.
        
        Returns:
            Liste von Organisationen mit id und name
            
        Raises:
            MiddlewareError: Bei API-Fehlern
        """
        self._check_rate_limit()
        
        try:
            orgs = self.backend_service.mctime_api.get_organizations()
            self._update_request_time()
            return self.transformer.transform_organizations(orgs)
        except Exception as e:
            return self.error_handler.handle_error(e, "get_organizations")
    
    def get_employees(self, organization_id: Optional[str] = None) -> List[Dict]:
        """
        Ruft die Mitarbeiterliste ab.
        
        Args:
            organization_id: Optional - Filter nach Organisation
            
        Returns:
            Liste von Mitarbeitern mit id, name, email
        """
        self._check_rate_limit()
        
        try:
            employees = self.backend_service.mctime_api.get_employees(organization_id)
            self._update_request_time()
            return self.transformer.transform_employees(employees)
        except Exception as e:
            return self.error_handler.handle_error(e, "get_employees")
    
    def get_employee_by_id(self, employee_id: str) -> Optional[Dict]:
        """
        Ruft einen einzelnen Mitarbeiter ab.
        
        Args:
            employee_id: Die ID des Mitarbeiters
            
        Returns:
            Mitarbeiter-Dict oder None
        """
        employees = self.get_employees()
        for emp in employees:
            if emp.get('id') == employee_id:
                return emp
        return None
    
    def get_employee_email(self, employee_id: str) -> Optional[str]:
        """
        Ruft die E-Mail-Adresse eines Mitarbeiters ab.
        
        Args:
            employee_id: Die ID des Mitarbeiters
            
        Returns:
            E-Mail-Adresse oder None
        """
        self._check_rate_limit()
        
        try:
            email = self.backend_service.mctime_api.get_user_email_by_id(employee_id)
            self._update_request_time()
            return email if email else None
        except Exception as e:
            self.error_handler.log_error(e, "get_employee_email")
            return None
    
    # =========================================================================
    # ZEITDATEN ABRUFEN
    # =========================================================================
    
    def get_time_entries(
        self,
        employee_id: str,
        date_from: str,
        date_to: str,
        organization_id: Optional[str] = None,
        format_output: bool = True
    ) -> List[Dict]:
        """
        Ruft Zeiteinträge für einen Mitarbeiter ab.
        
        Args:
            employee_id: ID des Mitarbeiters
            date_from: Startdatum (Format: dd.mm.yyyy oder yyyy-mm-dd)
            date_to: Enddatum (Format: dd.mm.yyyy oder yyyy-mm-dd)
            organization_id: Optional - Filter nach Organisation
            format_output: Ob die Ausgabe formatiert werden soll
            
        Returns:
            Liste von Zeiteinträgen
        """
        self._check_rate_limit()
        
        try:
            # Datumsformat konvertieren falls nötig
            date_from_api = self._ensure_api_date_format(date_from)
            date_to_api = self._ensure_api_date_format(date_to)
            
            entries = self.backend_service.mctime_api.get_time_entries(
                employee_id=employee_id,
                date_from=date_from_api,
                date_to=date_to_api,
                organization_id=organization_id
            )
            
            self._update_request_time()
            
            if format_output:
                return self.transformer.transform_time_entries(entries)
            return entries
            
        except Exception as e:
            return self.error_handler.handle_error(e, "get_time_entries")
    
    def get_form_data(self) -> Dict:
        """
        Ruft alle Daten ab die für das Frontend-Formular benötigt werden.
        
        Returns:
            Dict mit organizations, employees und status
        """
        try:
            form_data = self.backend_service.get_form_data()
            return {
                'organizations': self.transformer.transform_organizations(
                    form_data.get('organizations', [])
                ),
                'employees': self.transformer.transform_employees(
                    form_data.get('employees', [])
                ),
                'status': form_data.get('status', 'error')
            }
        except Exception as e:
            return self.error_handler.handle_error(e, "get_form_data")
    
    def process_form_request(self, form_data: Dict) -> Dict:
        """
        Verarbeitet eine Formular-Anfrage vom Frontend.
        
        Args:
            form_data: Dict mit firma, mitarbeiter, von, bis
            
        Returns:
            Dict mit status und data
        """
        self._check_rate_limit()
        
        try:
            result = self.backend_service.process_form_request(form_data)
            self._update_request_time()
            
            # Zeiteinträge transformieren wenn erfolgreich
            if result.get('status') == 'success':
                entries = result.get('data', {}).get('timeEntries', [])
                result['data']['timeEntries'] = self.transformer.transform_time_entries(entries)
            
            return result
            
        except Exception as e:
            return self.error_handler.handle_error(e, "process_form_request")
    
    # =========================================================================
    # DATEN EXPORT - CSV Verarbeitung
    # =========================================================================
    
    def export_to_csv(
        self,
        time_entries: List[Dict],
        include_headers: bool = True,
        encoding: str = 'utf-8'
    ) -> str:
        """
        Exportiert Zeiteinträge als CSV.
        
        Args:
            time_entries: Liste von Zeiteinträgen
            include_headers: Ob Header-Zeile eingefügt werden soll
            encoding: Zeichencodierung
            
        Returns:
            CSV-String
        """
        return self.transformer.to_csv(
            time_entries,
            include_headers=include_headers,
            encoding=encoding
        )
    
    def export_time_data_csv(
        self,
        employee_id: str,
        date_from: str,
        date_to: str,
        organization_id: Optional[str] = None
    ) -> str:
        """
        Ruft Zeitdaten ab und exportiert sie direkt als CSV.
        
        Args:
            employee_id: ID des Mitarbeiters
            date_from: Startdatum
            date_to: Enddatum
            organization_id: Optional - Organisation
            
        Returns:
            CSV-String der Zeiteinträge
        """
        entries = self.get_time_entries(
            employee_id=employee_id,
            date_from=date_from,
            date_to=date_to,
            organization_id=organization_id
        )
        return self.export_to_csv(entries)
    
    # =========================================================================
    # HILFSMETHODEN
    # =========================================================================
    
    def _check_rate_limit(self):
        """Prüft ob Rate Limit erreicht ist"""
        if not self.rate_limiter.check():
            raise MiddlewareError(
                "RATE_LIMIT_EXCEEDED",
                f"Rate Limit erreicht. Bitte warten Sie {self.rate_limiter.get_wait_time()} Sekunden."
            )
    
    def _update_request_time(self):
        """Aktualisiert die letzte Request-Zeit"""
        self._last_request_time = datetime.now()
        self.rate_limiter.record_request()
    
    def _ensure_api_date_format(self, date_str: str) -> str:
        """
        Konvertiert Datum in API-Format (yyyy-mm-dd).
        
        Args:
            date_str: Datum als String (dd.mm.yyyy oder yyyy-mm-dd)
            
        Returns:
            Datum im Format yyyy-mm-dd
        """
        if not date_str:
            return ""
        
        # Bereits im richtigen Format
        if '-' in date_str and len(date_str) == 10:
            return date_str
        
        # Von dd.mm.yyyy konvertieren
        if '.' in date_str:
            try:
                date_obj = datetime.strptime(date_str, "%d.%m.%Y")
                return date_obj.strftime("%Y-%m-%d")
            except ValueError:
                raise MiddlewareError(
                    "INVALID_DATE_FORMAT",
                    f"Ungültiges Datumsformat: {date_str}. Erwartet: dd.mm.yyyy"
                )
        
        raise MiddlewareError(
            "INVALID_DATE_FORMAT",
            f"Unbekanntes Datumsformat: {date_str}"
        )
    
    def _ensure_display_date_format(self, date_str: str) -> str:
        """
        Konvertiert Datum in Anzeigeformat (dd.mm.yyyy).
        
        Args:
            date_str: Datum als String
            
        Returns:
            Datum im Format dd.mm.yyyy
        """
        if not date_str:
            return ""
        
        # Bereits im Anzeigeformat
        if '.' in date_str:
            return date_str
        
        # Von yyyy-mm-dd konvertieren
        if '-' in date_str:
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                return date_obj.strftime("%d.%m.%Y")
            except ValueError:
                return date_str
        
        return date_str


# =========================================================================
# SINGLETON INSTANZ für einfache Verwendung
# =========================================================================

_middleware_instance = None

def get_middleware(api_key: str = None) -> AdapterMiddleware:
    """
    Gibt die Singleton-Instanz der Middleware zurück.
    
    Args:
        api_key: Optional - API-Key (nur beim ersten Aufruf relevant)
        
    Returns:
        AdapterMiddleware Instanz
    """
    global _middleware_instance
    
    if _middleware_instance is None:
        _middleware_instance = AdapterMiddleware(api_key)
    
    return _middleware_instance
