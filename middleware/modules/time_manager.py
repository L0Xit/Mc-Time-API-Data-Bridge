"""
Time Manager - Modul für Zeit- und Abwesenheitsdaten
Verarbeitet komplexe Zeiteintragsstrukturen von McTime API
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta


class TimeManager:
    """
    Verwaltet Zeit- und Abwesenheitsdaten
    Behandelt komplexe Zeiteintragsstrukturen
    """
    
    def __init__(self, request_handler):
        """
        Initialisiert Time Manager
        
        Args:
            request_handler: RequestHandler für API-Kommunikation
        """
        self.request_handler = request_handler
    
    def get_time_entries(
        self,
        employee_id: str,
        date_from: str,
        date_to: str,
        organization_id: str = None
    ) -> List[Dict]:
        """
        Holt Zeiteinträge für einen Mitarbeiter
        
        Args:
            employee_id: ID des Mitarbeiters
            date_from: Startdatum (yyyy-mm-dd)
            date_to: Enddatum (yyyy-mm-dd)
            organization_id: Optional - Filter nach Organisation
            
        Returns:
            Liste der Zeiteinträge mit berechneten Feldern
        """
        # Konvertiere Datum zu ISO-Format mit Timezone
        from_datetime = f"{date_from}T00:00:00+02:00"
        to_datetime = f"{date_to}T23:59:59+02:00"
        
        params = {
            "userIds": employee_id,
            "from": from_datetime,
            "to": to_datetime
        }
        
        if organization_id:
            params["organizationId"] = organization_id
        
        # API-Request
        response = self.request_handler.get("/times", params=params)
        
        if not response:
            return []
        
        # Verarbeite komplexe Struktur
        return self._parse_time_entries(response, employee_id)
    
    def _parse_time_entries(self, response: Dict, employee_id: str) -> List[Dict]:
        """
        Parst die komplexe Zeiteintragsstruktur von McTime
        
        Args:
            response: API-Response
            employee_id: ID des Mitarbeiters (für Namensauflösung)
            
        Returns:
            Flache Liste der Zeiteinträge
        """
        all_entries = []
        
        time_items = response.get("items", [])
        
        for item in time_items:
            if item.get("message") != "Success":
                continue
            
            item_data = item.get("data", {})
            
            if "timeEntries" not in item_data:
                continue
            
            for time_entry in item_data["timeEntries"]:
                if "times" not in time_entry:
                    continue
                
                for time_record in time_entry["times"]:
                    # Erweitere Zeiteintrag mit berechneten Feldern
                    enhanced_record = self._enhance_time_record(time_record)
                    enhanced_record["employee_id"] = employee_id
                    all_entries.append(enhanced_record)
        
        return all_entries
    
    def _enhance_time_record(self, time_record: Dict) -> Dict:
        """
        Erweitert Zeiteintrag mit berechneten Feldern
        
        Args:
            time_record: Roher Zeiteintrag von API
            
        Returns:
            Erweiterter Zeiteintrag mit:
            - project: Projektname
            - total_hours: Gesamtstunden
            - break_hours: Pausenstunden
            - actual_work_hours: Effektive Arbeitsstunden
            - breaks_formatted: Formatierte Pausenzeiten
            - date_formatted: Formatiertes Datum
            - time_formatted: Formatierte Arbeitszeit
        """
        enhanced = time_record.copy()
        
        try:
            # Parse Start- und Endzeit
            start_time = datetime.fromisoformat(
                time_record["from"].replace("Z", "+00:00")
            )
            end_time = datetime.fromisoformat(
                time_record["to"].replace("Z", "+00:00")
            )
            
            # Berechne Gesamtzeit
            total_time = end_time - start_time
            total_hours = total_time.total_seconds() / 3600
            
            # Berechne Pausenzeit
            total_break_time = timedelta()
            break_list = []
            
            # Handle None breaks
            breaks = time_record.get("breaks") or []
            
            for break_item in breaks:
                try:
                    break_start = datetime.fromisoformat(
                        break_item["from"].replace("Z", "+00:00")
                    )
                    break_end = datetime.fromisoformat(
                        break_item["to"].replace("Z", "+00:00")
                    )
                    break_duration = break_end - break_start
                    total_break_time += break_duration
                    
                    # Format für CSV: "09:00-09:30" (ohne Stunden-Angabe, wie im Original)
                    break_str = f"{break_start.strftime('%H:%M')}-{break_end.strftime('%H:%M')}"
                    break_list.append(break_str)
                    
                except Exception as e:
                    print(f"Fehler beim Verarbeiten der Pause: {e}")
            
            # Berechne effektive Arbeitsstunden
            break_hours = total_break_time.total_seconds() / 3600
            actual_work_hours = total_hours - break_hours
            
            # Füge berechnete Felder hinzu (CSV-kompatibel)
            enhanced["project"] = time_record.get("organizationName", "Unbekanntes Projekt")
            enhanced["total_hours"] = round(total_hours, 2)
            enhanced["break_hours"] = round(break_hours, 2)
            enhanced["actual_work_hours"] = round(actual_work_hours, 2)
            
            # Pausenformat: "09:00-09:30;16:00-16:30" (wie im Original)
            pause_formatted = ";".join(break_list) if break_list else ""
            enhanced["breaks_formatted"] = pause_formatted
            
            # Datumsformat: "01.10.25" (wie im Original)
            enhanced["date_formatted"] = start_time.strftime("%d.%m.%y")
            
            # Zeitformat: "05:00" und "18:00" (wie im Original)
            enhanced["time_start"] = start_time.strftime("%H:%M")
            enhanced["time_end"] = end_time.strftime("%H:%M")
            enhanced["time_formatted"] = f"{start_time.strftime('%H:%M')}-{end_time.strftime('%H:%M')}"
            
            # Summen im Format "13:00" (Stunden:Minuten, wie im Original)
            total_hours_int = int(total_hours)
            total_minutes = int((total_hours - total_hours_int) * 60)
            enhanced["total_hours_formatted"] = f"{total_hours_int:02d}:{total_minutes:02d}"
            
            actual_hours_int = int(actual_work_hours)
            actual_minutes = int((actual_work_hours - actual_hours_int) * 60)
            enhanced["actual_hours_formatted"] = f"{actual_hours_int:02d}:{actual_minutes:02d}"
            
        except Exception as e:
            print(f"Fehler beim Erweitern des Zeiteintrags: {e}")
            # Default-Werte bei Fehler
            enhanced["project"] = time_record.get("organizationName", "Unbekanntes Projekt")
            enhanced["total_hours"] = 0.0
            enhanced["break_hours"] = 0.0
            enhanced["actual_work_hours"] = 0.0
            enhanced["breaks_formatted"] = ""
            enhanced["date_formatted"] = "Unbekannt"
            enhanced["time_formatted"] = "Unbekannt"
            enhanced["time_start"] = "00:00"
            enhanced["time_end"] = "00:00"
            enhanced["total_hours_formatted"] = "00:00"
            enhanced["actual_hours_formatted"] = "00:00"
        
        return enhanced
    
    def get_absence_data(
        self,
        employee_id: str,
        date_from: str,
        date_to: str
    ) -> List[Dict]:
        """
        Holt Abwesenheitsdaten für einen Mitarbeiter
        
        Args:
            employee_id: ID des Mitarbeiters
            date_from: Startdatum (yyyy-mm-dd)
            date_to: Enddatum (yyyy-mm-dd)
            
        Returns:
            Liste der Abwesenheiten
        """
        # Konvertiere Datum zu ISO-Format
        from_datetime = f"{date_from}T00:00:00+02:00"
        to_datetime = f"{date_to}T23:59:59+02:00"
        
        params = {
            "userIds": employee_id,
            "from": from_datetime,
            "to": to_datetime
        }
        
        # Versuche Abwesenheits-Endpoint
        response = self.request_handler.get("/absences", params=params)
        
        if not response:
            return []
        
        return self._parse_absence_data(response)
    
    def _parse_absence_data(self, response: Dict) -> List[Dict]:
        """
        Parst Abwesenheitsdaten
        
        Args:
            response: API-Response
            
        Returns:
            Liste der Abwesenheiten
        """
        absences = []
        
        items = response.get("items", [])
        
        for item in items:
            if item.get("message") != "Success":
                continue
            
            item_data = item.get("data", {})
            absence_list = item_data.get("absences", [])
            
            for absence in absence_list:
                absences.append({
                    "type": absence.get("type", "Unbekannt"),
                    "from": absence.get("from"),
                    "to": absence.get("to"),
                    "status": absence.get("status", ""),
                    "comment": absence.get("comment", "")
                })
        
        return absences
    
    def calculate_summary(self, time_entries: List[Dict]) -> Dict:
        """
        Berechnet Zusammenfassung für Zeiteinträge
        
        Args:
            time_entries: Liste der Zeiteinträge
            
        Returns:
            Dict mit Zusammenfassung
        """
        if not time_entries:
            return {
                "total_days": 0,
                "total_hours": 0.0,
                "total_breaks": 0.0,
                "actual_work_hours": 0.0,
                "average_daily_hours": 0.0
            }
        
        total_hours = sum(e.get("total_hours", 0) for e in time_entries)
        total_breaks = sum(e.get("break_hours", 0) for e in time_entries)
        actual_work = sum(e.get("actual_work_hours", 0) for e in time_entries)
        total_days = len(time_entries)
        
        return {
            "total_days": total_days,
            "total_hours": round(total_hours, 2),
            "total_breaks": round(total_breaks, 2),
            "actual_work_hours": round(actual_work, 2),
            "average_daily_hours": round(actual_work / total_days, 2) if total_days > 0 else 0.0
        }
