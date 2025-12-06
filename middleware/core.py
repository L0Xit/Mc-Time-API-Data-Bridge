"""
Middleware Core - Middleware-Schicht für Backend-Integration
Frontend → Middleware → Backend → McTime API
"""

import os
import sys
from typing import Dict, List, Optional, Any
from datetime import datetime

# Backend Import
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
try:
    from backend.api_handler import BackendService
except ImportError:
    BackendService = None

from .auth import AuthHandler
from .request_handler import RequestHandler
from .modules.mail_manager import MailManager


class Middleware:
    """
    Middleware-Schicht für Backend-Integration
    Bietet zusätzliche Features: Rate Limiting, erweiterte E-Mail-Funktionen, etc.
    """
    
    def __init__(self, api_key: str = None):
        """
        Initialisiert die Middleware mit Backend-Integration
        
        Args:
            api_key: McTime API-Key (falls None, wird aus Umgebungsvariable geladen)
        """
        self.api_key = api_key or os.getenv('MCTIME_API_KEY')
        
        if not self.api_key:
            raise ValueError("MCTIME_API_KEY nicht gesetzt! Bitte in .env konfigurieren.")
        
        # Initialisiere Backend Service (Hauptdatenquelle)
        if BackendService:
            self.backend = BackendService(self.api_key)
            print("✅ Middleware nutzt Backend Service")
        else:
            self.backend = None
            print("⚠️ Backend nicht verfügbar - Middleware im Standalone-Modus")
        
        # Initialisiere Middleware-Features
        self.auth = AuthHandler(self.api_key)
        self.request_handler = RequestHandler(self.auth)
        self.mail = MailManager(self.request_handler)
        
        self._connected = False
    
    def connect(self) -> bool:
        """
        Testet die Verbindung über Backend oder direkt
        
        Returns:
            True wenn Verbindung erfolgreich
        """
        try:
            # Primär: Backend verwenden
            if self.backend:
                result = self.backend.get_form_data()
                self._connected = result.get('status') == 'success'
            else:
                # Fallback: Direkte API-Verbindung
                result = self.request_handler.get("/organizations")
                self._connected = result is not None
            
            return self._connected
        except Exception as e:
            print(f"Middleware Verbindungsfehler: {e}")
            self._connected = False
            return False
    
    @property
    def is_connected(self) -> bool:
        """Gibt Verbindungsstatus zurück"""
        return self._connected
    
    def get_connection_status(self) -> Dict:
        """
        Gibt detaillierten Verbindungsstatus zurück
        
        Returns:
            Dict mit Status-Informationen
        """
        return {
            "connected": self._connected,
            "api_configured": bool(self.api_key),
            "base_url": self.request_handler.base_url,
            "last_check": datetime.now().isoformat()
        }
    
    def health_check(self) -> Dict:
        """
        Führt Gesundheitscheck durch
        
        Returns:
            Dict mit Health-Status
        """
        try:
            connected = self.connect()
            return {
                "status": "healthy" if connected else "unhealthy",
                "connected": connected,
                "timestamp": datetime.now().isoformat(),
                "api_version": "v2"
            }
        except Exception as e:
            return {
                "status": "error",
                "connected": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    # ==================== MITARBEITER-OPERATIONEN ====================
    
    def get_organizations(self) -> List[Dict]:
        """Holt Liste aller Organisationen/Firmen - Backend primär"""
        if self.backend:
            return self.backend.mctime_api.get_organizations()
        else:
            # Fallback: Direkte API-Calls (nur wenn Backend nicht verfügbar)
            response = self.request_handler.get("/organizations")
            if response:
                orgs = response.get("items", [{}])[0].get("data", {}).get("organizations", [])
                return [{"id": org.get("id"), "name": org.get("organizationName")} for org in orgs]
            return []
    
    def get_employees(self, organization_id: str = None, organization_name: str = None) -> List[Dict]:
        """Holt Liste aller Mitarbeiter - Backend primär"""
        if self.backend:
            return self.backend.mctime_api.get_employees(organization_id, organization_name)
        else:
            # Fallback: Direkte API-Calls
            params = {"roles": "employee"}
            
            if organization_name:
                params["organizationName"] = organization_name
            elif organization_id:
                params["organizationId"] = organization_id
            
            response = self.request_handler.get("/users", params=params)
            if response:
                users = response.get("items", [{}])[0].get("data", {}).get("users", [])
                employees = []
                for user in users:
                    full_name = f"{user.get('firstName', '')} {user.get('lastName', '')}".strip()
                    if not full_name:
                        full_name = "Unbekannter Benutzer"
                    employees.append({
                        "id": user.get("id"),
                        "name": full_name,
                        "firstName": user.get("firstName", ""),
                        "lastName": user.get("lastName", ""),
                        "email": user.get("email")
                    })
                return sorted(employees, key=lambda x: x["name"])
            return []
    
    def get_employee_by_id(self, employee_id: str) -> Optional[Dict]:
        """Holt Mitarbeiter-Details nach ID"""
        return self.employees.get_employee_by_id(employee_id)
    
    def get_employee_email(self, employee_id: str) -> str:
        """Holt E-Mail-Adresse eines Mitarbeiters"""
        return self.employees.get_employee_email(employee_id)
    
    # ==================== ZEIT-OPERATIONEN ====================
    
    def get_time_entries(
        self,
        employee_id: str,
        date_from: str,
        date_to: str,
        organization_id: str = None
    ) -> List[Dict]:
        """
        Holt Zeiteinträge für einen Mitarbeiter - Backend primär
        
        Args:
            employee_id: ID des Mitarbeiters
            date_from: Startdatum (dd.mm.yyyy oder yyyy-mm-dd)
            date_to: Enddatum (dd.mm.yyyy oder yyyy-mm-dd)
            organization_id: Optional - Filter nach Organisation
            
        Returns:
            Liste der Zeiteinträge
        """
        # Normalisiere Datum
        date_from = self._normalize_date(date_from)
        date_to = self._normalize_date(date_to)
        
        if self.backend:
            # Backend verwenden (bewährte Logik)
            return self.backend.mctime_api.get_time_entries(
                employee_id=employee_id,
                date_from=date_from,
                date_to=date_to,
                organization_id=organization_id
            )
        else:
            # Fallback: Middleware Time Manager
            from .modules.time_manager import TimeManager
            time_manager = TimeManager(self.request_handler)
            return time_manager.get_time_entries(
                employee_id=employee_id,
                date_from=date_from,
                date_to=date_to,
                organization_id=organization_id
            )
    
    def get_absence_data(
        self,
        employee_id: str,
        date_from: str,
        date_to: str
    ) -> List[Dict]:
        """Holt Abwesenheitsdaten für einen Mitarbeiter"""
        return self.times.get_absence_data(employee_id, date_from, date_to)
    
    # ==================== FORM-VERARBEITUNG ====================
    
    def process_form_request(self, form_data: Dict) -> Dict:
        """
        Verarbeitet Frontend-Formular-Request - Backend primär
        
        Args:
            form_data: Dict mit:
                - firma: Organization ID
                - mitarbeiter: Employee ID
                - von: Startdatum (dd.mm.yyyy)
                - bis: Enddatum (dd.mm.yyyy)
                
        Returns:
            Dict mit Status und Zeitdaten
        """
        try:
            if self.backend:
                # Backend verwenden (bewährte Implementierung)
                return self.backend.process_form_request(form_data)
            else:
                # Fallback: Middleware-Implementation
                organization_id = form_data.get("firma")
                employee_id = form_data.get("mitarbeiter")
                date_from = form_data.get("von")
                date_to = form_data.get("bis")
                
                if not all([employee_id, date_from, date_to]):
                    return {
                        "status": "error",
                        "message": "Fehlende Pflichtfelder: mitarbeiter, von, bis"
                    }
                
                # Konvertiere Datumsformat falls nötig
                date_from = self._normalize_date(date_from)
                date_to = self._normalize_date(date_to)
                
                # Hole Zeiteinträge
                time_entries = self.get_time_entries(
                    employee_id=employee_id,
                    date_from=date_from,
                    date_to=date_to,
                    organization_id=organization_id
                )
                
                return {
                    "status": "success",
                    "data": {
                        "timeEntries": time_entries,
                        "employee_id": employee_id,
                        "organization_id": organization_id,
                        "date_range": {
                            "from": date_from,
                            "to": date_to
                        }
                    }
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Fehler bei der Verarbeitung: {str(e)}"
            }
    
    def get_form_data(self) -> Dict:
        """
        Holt initiale Formulardaten - Backend primär
        
        Returns:
            Dict mit organizations und employees
        """
        try:
            if self.backend:
                # Backend verwenden (bewährte Implementierung)
                return self.backend.get_form_data()
            else:
                # Fallback: Middleware-Implementation
                organizations = self.get_organizations()
                employees = self.get_employees()
                
                return {
                    "status": "success",
                    "organizations": organizations,
                    "employees": employees
                }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "organizations": [],
                "employees": []
            }
    
    # ==================== MAIL-OPERATIONEN ====================
    
    def send_time_report_email(
        self,
        employee_id: str,
        employee_name: str,
        date_from: str,
        date_to: str,
        custom_email: str = None,
        custom_subject: str = None,
        attach_csv: bool = True,
        custom_message: str = None
    ) -> Dict:
        """
        Sendet Zeitbericht per E-Mail an Mitarbeiter
        
        Args:
            employee_id: ID des Mitarbeiters
            employee_name: Name des Mitarbeiters
            date_from: Startdatum
            date_to: Enddatum
            custom_email: Benutzerdefinierte E-Mail-Adresse
            custom_subject: Benutzerdefinierter Betreff
            attach_csv: CSV anhängen
            custom_message: Benutzerdefinierte Nachricht
            
        Returns:
            Dict mit Status der E-Mail-Versendung
        """
        try:
            # Normalisiere Datum
            date_from_normalized = self._normalize_date(date_from)
            date_to_normalized = self._normalize_date(date_to)
            
            # Hole E-Mail-Adresse
            if custom_email:
                to_email = custom_email
            else:
                # Hole E-Mail vom Backend
                if self.backend:
                    to_email = self.backend.mctime_api.get_user_email_by_id(employee_id)
                else:
                    to_email = None
                
                if not to_email:
                    return {
                        "status": "error",
                        "message": f"Keine E-Mail-Adresse für {employee_name} gefunden"
                    }
            
            # Hole Zeiteinträge
            time_entries = self.get_time_entries(
                employee_id=employee_id,
                date_from=date_from_normalized,
                date_to=date_to_normalized
            )
            
            if not time_entries:
                return {
                    "status": "error",
                    "message": "Keine Zeiteinträge für den angegebenen Zeitraum gefunden"
                }
            
            # Erstelle Betreff
            if custom_subject:
                subject = custom_subject
            else:
                subject = f"Zeiterfassung für {employee_name} ({date_from} bis {date_to})"
            
            # Erstelle HTML-Body
            html_body = self.mail._create_report_html(
                employee_name=employee_name,
                time_entries=time_entries,
                date_from=date_from,
                date_to=date_to
            )
            
            # Füge benutzerdefinierte Nachricht hinzu falls vorhanden
            if custom_message:
                html_body = html_body.replace(
                    '<h2>Zeiterfassung',
                    f'<div style="background: #f0f9ff; padding: 15px; margin-bottom: 20px; border-radius: 5px;"><strong>Nachricht:</strong><br>{custom_message}</div><h2>Zeiterfassung'
                )
            
            # Erstelle CSV falls gewünscht
            csv_content = None
            csv_filename = None
            if attach_csv:
                csv_content = self.mail._create_csv_content(time_entries, employee_name)
                csv_filename = f"zeiterfassung_{employee_name}_{date_from}_{date_to}.csv".replace(" ", "_")
            
            # Sende E-Mail
            success = self.mail._send_email(
                to_email=to_email,
                subject=subject,
                html_body=html_body,
                csv_content=csv_content,
                csv_filename=csv_filename
            )
            
            if success:
                return {
                    "status": "success",
                    "message": "E-Mail erfolgreich gesendet",
                    "email": to_email
                }
            else:
                return {
                    "status": "error",
                    "message": "Fehler beim Senden der E-Mail - SMTP nicht konfiguriert oder Verbindungsfehler"
                }
                
        except Exception as e:
            print(f"Fehler in send_time_report_email: {e}")
            return {
                "status": "error",
                "message": f"Fehler: {str(e)}"
            }
    
    # ==================== HILFSFUNKTIONEN ====================
    
    def _normalize_date(self, date_str: str) -> str:
        """
        Normalisiert Datumsformat zu yyyy-mm-dd
        
        Args:
            date_str: Datum in dd.mm.yyyy oder yyyy-mm-dd
            
        Returns:
            Datum im Format yyyy-mm-dd
        """
        if not date_str:
            return ""
        
        # Wenn bereits im richtigen Format
        if '-' in date_str and len(date_str) == 10:
            return date_str
        
        # Konvertiere dd.mm.yyyy zu yyyy-mm-dd
        try:
            date_obj = datetime.strptime(date_str, "%d.%m.%Y")
            return date_obj.strftime("%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Ungültiges Datumsformat: {date_str}. Erwartet: dd.mm.yyyy")
    
    def convert_to_csv(self, data: List[Dict]) -> str:
        """
        Konvertiert JSON-Daten zu CSV-String
        
        Args:
            data: Liste von Dictionaries
            
        Returns:
            CSV-String
        """
        if not data:
            return ""
        
        import csv
        import io
        
        output = io.StringIO()
        
        # Bestimme Header aus erstem Eintrag
        headers = list(data[0].keys())
        
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data)
        
        return output.getvalue()


# Singleton-Instanz für einfachen Import
_middleware_instance = None


def get_middleware(api_key: str = None) -> Middleware:
    """
    Gibt Middleware-Singleton zurück
    
    Args:
        api_key: Optional - API-Key für erste Initialisierung
        
    Returns:
        Middleware-Instanz
    """
    global _middleware_instance
    
    if _middleware_instance is None:
        _middleware_instance = Middleware(api_key)
    
    return _middleware_instance
