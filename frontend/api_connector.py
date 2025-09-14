"""
Middleware Connector für Mc-Time API Data Bridge
Diese Klasse wird später mit der echten Middleware verbunden.
Aktuell arbeitet sie mit Dummy-Daten für die Frontend-Entwicklung.
"""

import requests
from typing import List, Dict, Optional
from datetime import datetime

class MiddlewareConnector:
    """
    Verbindung zur Middleware - bereit für echte Implementation
    """
    
    def __init__(self, middleware_base_url: str = None):
        # Später: echte Middleware URL
        self.middleware_url = middleware_base_url or "http://localhost:8080/api"
        self.is_connected = False
        
        # Dummy-Status für Frontend-Entwicklung
        self._use_dummy_data = True
    
    def connect(self) -> bool:
        """
        Stellt Verbindung zur Middleware her
        TODO: Implementierung wenn Middleware verfügbar ist
        """
        if self._use_dummy_data:
            # Dummy-Implementation für Frontend-Tests
            self.is_connected = True
            return True
        
        try:
            # Später: Echter Ping zur Middleware
            # response = requests.get(f"{self.middleware_url}/health")
            # self.is_connected = response.status_code == 200
            # return self.is_connected
            pass
        except Exception as e:
            print(f"Middleware-Verbindung fehlgeschlagen: {e}")
            self.is_connected = False
            return False
    
    def get_companies(self) -> List[str]:
        """
        Holt Firmenliste von der Middleware
        TODO: Ersetzen durch echten Middleware-Call
        """
        if self._use_dummy_data:
            return [
                "Mustermann GmbH",
                "Schmidt & Partner", 
                "Wagner Industries",
                "Müller Consulting",
                "Tech Solutions AG"
            ]
        
        # Später: Echter Middleware-Call
        # try:
        #     response = requests.get(f"{self.middleware_url}/companies")
        #     return response.json()
        # except Exception as e:
        #     print(f"Fehler beim Laden der Firmen: {e}")
        #     return []
    
    def get_employees(self, company_filter: str = None) -> List[Dict]:
        """
        Holt Mitarbeiterliste von der Middleware
        TODO: Ersetzen durch echten Middleware-Call
        """
        if self._use_dummy_data:
            dummy_employees = [
                {"id": 1, "name": "Max Mustermann", "company": "Mustermann GmbH"},
                {"id": 2, "name": "Anna Schmidt", "company": "Schmidt & Partner"},
                {"id": 3, "name": "Tom Wagner", "company": "Wagner Industries"},
                {"id": 4, "name": "Lisa Müller", "company": "Müller Consulting"},
                {"id": 5, "name": "Peter Koch", "company": "Tech Solutions AG"}
            ]
            
            if company_filter:
                return [emp for emp in dummy_employees if emp["company"] == company_filter]
            return dummy_employees
        
        # Später: Echter Middleware-Call
        # try:
        #     params = {"company": company_filter} if company_filter else {}
        #     response = requests.get(f"{self.middleware_url}/employees", params=params)
        #     return response.json()
        # except Exception as e:
        #     print(f"Fehler beim Laden der Mitarbeiter: {e}")
        #     return []
    
    def get_time_data(self, 
                     company: str = None,
                     employee: str = None, 
                     date_from: str = None,
                     date_to: str = None) -> List[Dict]:
        """
        Holt Zeiterfassungsdaten von der Middleware
        TODO: Ersetzen durch echten Middleware-Call
        """
        if self._use_dummy_data:
            dummy_data = [
                {
                    'date': '2025-01-01',
                    'employee': 'Max Mustermann',
                    'hours': 8.0,
                    'project': 'Projekt Alpha',
                    'company': 'Mustermann GmbH',
                    'description': 'Frontend Entwicklung',
                    'start_time': '09:00',
                    'end_time': '17:00'
                },
                {
                    'date': '2025-01-02',
                    'employee': 'Anna Schmidt',
                    'hours': 7.5,
                    'project': 'Projekt Beta',
                    'company': 'Schmidt & Partner',
                    'description': 'Backend API Development',
                    'start_time': '08:30',
                    'end_time': '16:00'
                },
                {
                    'date': '2025-01-03',
                    'employee': 'Tom Wagner',
                    'hours': 8.0,
                    'project': 'Projekt Alpha',
                    'company': 'Wagner Industries',
                    'description': 'Database Design',
                    'start_time': '09:00',
                    'end_time': '17:00'
                },
                {
                    'date': '2025-01-04',
                    'employee': 'Lisa Müller',
                    'hours': 6.0,
                    'project': 'Projekt Gamma',
                    'company': 'Müller Consulting',
                    'description': 'Testing & QA',
                    'start_time': '10:00',
                    'end_time': '16:00'
                }
            ]
            
            # Filter anwenden
            filtered_data = dummy_data
            
            if company:
                filtered_data = [d for d in filtered_data if d['company'] == company]
            
            if employee:
                filtered_data = [d for d in filtered_data if d['employee'] == employee]
            
            # Datumsfilter (vereinfacht für Demo)
            if date_from or date_to:
                # Hier würde später echte Datumslogik stehen
                pass
            
            return filtered_data
        
        # Später: Echter Middleware-Call
        # try:
        #     params = {}
        #     if company: params['company'] = company
        #     if employee: params['employee'] = employee
        #     if date_from: params['date_from'] = date_from
        #     if date_to: params['date_to'] = date_to
        #     
        #     response = requests.get(f"{self.middleware_url}/timedata", params=params)
        #     return response.json()
        # except Exception as e:
        #     print(f"Fehler beim Laden der Zeitdaten: {e}")
        #     return []
    
    def get_connection_status(self) -> Dict:
        """
        Gibt Status der Middleware-Verbindung zurück
        TODO: Echte Statusprüfung implementieren
        """
        return {
            'connected': self.is_connected,
            'middleware_url': self.middleware_url,
            'last_check': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'Dummy-Modus' if self._use_dummy_data else ('Verbunden' if self.is_connected else 'Getrennt')
        }
    
    def ping_middleware(self) -> Dict:
        """
        Testet die Verbindung zur Middleware
        TODO: Echter Ping implementieren
        """
        if self._use_dummy_data:
            return {
                'success': True,
                'message': 'Dummy-Verbindung erfolgreich',
                'response_time': '50ms',
                'timestamp': datetime.now().isoformat()
            }
        
        # Später: Echter Ping
        # try:
        #     start_time = time.time()
        #     response = requests.get(f"{self.middleware_url}/ping", timeout=5)
        #     response_time = (time.time() - start_time) * 1000
        #     
        #     return {
        #         'success': response.status_code == 200,
        #         'message': 'Verbindung erfolgreich' if response.status_code == 200 else 'Verbindung fehlgeschlagen',
        #         'response_time': f'{response_time:.0f}ms',
        #         'timestamp': datetime.now().isoformat()
        #     }
        # except Exception as e:
        #     return {
        #         'success': False,
        #         'message': f'Verbindungsfehler: {str(e)}',
        #         'response_time': None,
        #         'timestamp': datetime.now().isoformat()
        #     }

    def switch_to_production_mode(self, middleware_url: str):
        """
        Wechselt von Dummy-Daten zu echter Middleware
        Diese Methode wird aufgerufen, wenn die Middleware verfügbar ist
        """
        self.middleware_url = middleware_url
        self._use_dummy_data = False
        return self.connect()


# Globale Instanz für die Anwendung
middleware_connector = MiddlewareConnector()