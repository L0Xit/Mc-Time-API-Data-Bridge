"""
Employee Manager - Modul für McTime Login & Mitarbeiterverwaltung
"""

from typing import Dict, List, Optional


class EmployeeManager:
    """
    Verwaltet Mitarbeiter und Organisationen
    """
    
    def __init__(self, request_handler):
        """
        Initialisiert Employee Manager
        
        Args:
            request_handler: RequestHandler für API-Kommunikation
        """
        self.request_handler = request_handler
        
        # Cache für Mitarbeiterdaten
        self._employees_cache = None
        self._organizations_cache = None
    
    def get_organizations(self) -> List[Dict]:
        """
        Holt Liste aller Organisationen/Firmen
        
        Returns:
            Liste der Organisationen mit id und name
        """
        response = self.request_handler.get("/organizations")
        
        if not response:
            return []
        
        try:
            # Parse komplexe Struktur
            organizations_data = (
                response.get("items", [{}])[0]
                .get("data", {})
                .get("organizations", [])
            )
            
            organizations = []
            for org in organizations_data:
                organizations.append({
                    "id": org.get("id"),
                    "name": org.get("organizationName")
                })
            
            # Cache aktualisieren
            self._organizations_cache = organizations
            
            return organizations
            
        except Exception as e:
            print(f"Fehler beim Parsen der Organisationen: {e}")
            return []
    
    def get_employees(self, organization_id: str = None) -> List[Dict]:
        """
        Holt Liste aller Mitarbeiter
        
        Args:
            organization_id: Optional - Filter nach Organisation
            
        Returns:
            Liste der Mitarbeiter mit id, name, firstName, lastName, email
        """
        params = {"roles": "employee"}
        
        if organization_id:
            params["organizationId"] = organization_id
        
        response = self.request_handler.get("/users", params=params)
        
        if not response:
            return []
        
        try:
            # Parse komplexe Struktur
            users_data = (
                response.get("items", [{}])[0]
                .get("data", {})
                .get("users", [])
            )
            
            employees = []
            for user in users_data:
                first_name = user.get("firstName", "")
                last_name = user.get("lastName", "")
                full_name = f"{first_name} {last_name}".strip()
                
                if not full_name:
                    full_name = "Unbekannter Benutzer"
                
                employees.append({
                    "id": user.get("id"),
                    "name": full_name,
                    "firstName": first_name,
                    "lastName": last_name,
                    "email": user.get("email")
                })
            
            # Sortiere nach Name
            employees = sorted(employees, key=lambda x: x["name"])
            
            # Cache aktualisieren
            self._employees_cache = employees
            
            return employees
            
        except Exception as e:
            print(f"Fehler beim Parsen der Mitarbeiter: {e}")
            return []
    
    def get_employee_by_id(self, employee_id: str) -> Optional[Dict]:
        """
        Holt Mitarbeiter-Details nach ID
        
        Args:
            employee_id: ID des Mitarbeiters
            
        Returns:
            Mitarbeiter-Dict oder None
        """
        # Prüfe Cache
        if self._employees_cache:
            for emp in self._employees_cache:
                if emp.get("id") == employee_id:
                    return emp
        
        # Cache nicht vorhanden - hole alle Mitarbeiter
        employees = self.get_employees()
        
        for emp in employees:
            if emp.get("id") == employee_id:
                return emp
        
        return None
    
    def get_employee_name(self, employee_id: str) -> str:
        """
        Holt Namen eines Mitarbeiters nach ID
        
        Args:
            employee_id: ID des Mitarbeiters
            
        Returns:
            Name oder "Unbekannter Benutzer"
        """
        employee = self.get_employee_by_id(employee_id)
        
        if employee:
            return employee.get("name", "Unbekannter Benutzer")
        
        return "Unbekannter Benutzer"
    
    def get_employee_email(self, employee_id: str) -> str:
        """
        Holt E-Mail-Adresse eines Mitarbeiters
        
        Args:
            employee_id: ID des Mitarbeiters
            
        Returns:
            E-Mail oder leerer String
        """
        employee = self.get_employee_by_id(employee_id)
        
        if employee:
            return employee.get("email", "")
        
        return ""
    
    def search_employees(self, query: str) -> List[Dict]:
        """
        Sucht Mitarbeiter nach Name
        
        Args:
            query: Suchbegriff
            
        Returns:
            Liste der passenden Mitarbeiter
        """
        employees = self.get_employees()
        
        if not query:
            return employees
        
        query_lower = query.lower()
        
        return [
            emp for emp in employees
            if query_lower in emp.get("name", "").lower()
            or query_lower in emp.get("firstName", "").lower()
            or query_lower in emp.get("lastName", "").lower()
        ]
    
    def clear_cache(self):
        """Löscht den Cache"""
        self._employees_cache = None
        self._organizations_cache = None
