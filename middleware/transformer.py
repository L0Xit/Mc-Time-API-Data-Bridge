"""
Data Transformer - JSON zu CSV und Frontend-Format Konvertierung
================================================================

Dieses Modul ist verantwortlich für die Transformation von Daten
zwischen verschiedenen Formaten:
    - API JSON Response -> Frontend-geeignetes Format
    - Zeiteinträge -> CSV Export
    - Komplexe Zeiteintragsstrukturen -> Flache Darstellung
"""

import io
import csv
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta


class DataTransformer:
    """
    Transformiert Daten zwischen API-Format und Frontend-Format.
    
    Hauptfunktionen:
        - JSON zu CSV Konvertierung
        - Zeiteinträge formatieren
        - Komplexe Strukturen vereinfachen
    
    CSV-Struktur basierend auf WorkExpert Vorlage:
        Personalnummer;Vorname;Nachname;Datum;Type;Zeit Beginn;Zeit Ende;
        Pause;Summe mit Pause;Summe ohne Pause;Projektnummer;Auftragsnummer;
        Projekt / Gruppenname;Kommentar
    """
    
    # CSV Spalten-Definitionen (WorkExpert Format)
    CSV_HEADERS = [
        'Personalnummer',
        'Vorname',
        'Nachname',
        'Datum',
        'Type',
        'Zeit Beginn',
        'Zeit Ende',
        'Pause',
        'Summe mit Pause',
        'Summe ohne Pause',
        'Projektnummer',
        'Auftragsnummer',
        'Projekt / Gruppenname',
        'Kommentar'
    ]
    
    # Mapping von API-Feldern zu CSV-Spalten
    FIELD_MAPPING = {
        'personalnummer': 'Personalnummer',
        'firstName': 'Vorname',
        'lastName': 'Nachname',
        'date_formatted': 'Datum',
        'type': 'Type',
        'start_time': 'Zeit Beginn',
        'end_time': 'Zeit Ende',
        'pause': 'Pause',
        'summe_mit_pause': 'Summe mit Pause',
        'summe_ohne_pause': 'Summe ohne Pause',
        'projektnummer': 'Projektnummer',
        'auftragsnummer': 'Auftragsnummer',
        'project': 'Projekt / Gruppenname',
        'kommentar': 'Kommentar'
    }
    
    def __init__(self, config: Dict = None):
        """
        Initialisiert den DataTransformer.
        
        Args:
            config: Optionale Konfiguration
        """
        self.config = config or {}
        self.date_format_display = self.config.get('date_format', '%d.%m.%Y')
        self.time_format_display = self.config.get('time_format', '%H:%M')
    
    # =========================================================================
    # ORGANISATIONS-TRANSFORMATION
    # =========================================================================
    
    def transform_organizations(self, organizations: List[Dict]) -> List[Dict]:
        """
        Transformiert Organisationen für das Frontend.
        
        Args:
            organizations: Liste von Organisationen aus der API
            
        Returns:
            Transformierte Liste mit id und name
        """
        if not organizations:
            return []
        
        result = []
        for org in organizations:
            result.append({
                'id': org.get('id', ''),
                'name': org.get('name', org.get('organizationName', 'Unbekannt')),
                'display_name': org.get('name', org.get('organizationName', 'Unbekannt'))
            })
        
        # Nach Name sortieren
        return sorted(result, key=lambda x: x.get('name', '').lower())
    
    # =========================================================================
    # MITARBEITER-TRANSFORMATION
    # =========================================================================
    
    def transform_employees(self, employees: List[Dict]) -> List[Dict]:
        """
        Transformiert Mitarbeiter für das Frontend.
        
        Args:
            employees: Liste von Mitarbeitern aus der API
            
        Returns:
            Transformierte Liste mit id, name, email, display_name
        """
        if not employees:
            return []
        
        result = []
        for emp in employees:
            full_name = emp.get('name', '')
            if not full_name:
                first_name = emp.get('firstName', '')
                last_name = emp.get('lastName', '')
                full_name = f"{first_name} {last_name}".strip() or 'Unbekannt'
            
            result.append({
                'id': emp.get('id', ''),
                'name': full_name,
                'firstName': emp.get('firstName', ''),
                'lastName': emp.get('lastName', ''),
                'email': emp.get('email', ''),
                'display_name': full_name
            })
        
        # Nach Name sortieren
        return sorted(result, key=lambda x: x.get('name', '').lower())
    
    # =========================================================================
    # ZEITEINTRÄGE-TRANSFORMATION
    # =========================================================================
    
    def transform_time_entries(self, entries: List[Dict]) -> List[Dict]:
        """
        Transformiert Zeiteinträge für das Frontend.
        
        Args:
            entries: Liste von Zeiteinträgen aus der API
            
        Returns:
            Transformierte Liste mit formatierten Feldern
        """
        if not entries:
            return []
        
        result = []
        for entry in entries:
            transformed = self._transform_single_entry(entry)
            result.append(transformed)
        
        # Nach Datum sortieren (neueste zuerst)
        return sorted(
            result,
            key=lambda x: x.get('sort_date', ''),
            reverse=True
        )
    
    def _transform_single_entry(self, entry: Dict) -> Dict:
        """
        Transformiert einen einzelnen Zeiteintrag.
        
        Args:
            entry: Zeiteintrag aus der API
            
        Returns:
            Transformierter Eintrag im WorkExpert Format
        """
        # Basis-Transformation (behält originale Felder)
        result = dict(entry)
        
        # Personalnummer (aus ID oder separatem Feld)
        result['personalnummer'] = entry.get('personalnummer', entry.get('id', ''))
        
        # Vorname und Nachname
        result['firstName'] = entry.get('firstName', '')
        result['lastName'] = entry.get('lastName', '')
        
        # Falls nur 'name' vorhanden, aufteilen
        if not result['firstName'] and entry.get('name'):
            name_parts = entry.get('name', '').split(' ', 1)
            result['firstName'] = name_parts[0] if name_parts else ''
            result['lastName'] = name_parts[1] if len(name_parts) > 1 else ''
        
        # Datum formatieren
        if 'from' in entry:
            try:
                start_dt = datetime.fromisoformat(entry['from'].replace('Z', '+00:00'))
                result['date_formatted'] = start_dt.strftime('%d.%m.%y')  # Format: dd.mm.yy
                result['sort_date'] = start_dt.strftime('%Y-%m-%d')
                result['start_time'] = start_dt.strftime('%H:%M')
            except Exception:
                result['date_formatted'] = entry.get('date_formatted', 'N/A')
                result['sort_date'] = ''
                result['start_time'] = ''
        
        if 'to' in entry:
            try:
                end_dt = datetime.fromisoformat(entry['to'].replace('Z', '+00:00'))
                result['end_time'] = end_dt.strftime('%H:%M')
            except Exception:
                result['end_time'] = ''
        
        # Type (Arbeitszeit als Standard)
        result['type'] = entry.get('type', 'Arbeitszeit')
        
        # Pause formatieren (Format: HH:MM-HH:MM)
        result['pause'] = self._format_pause_workexpert(entry.get('breaks', []))
        
        # Projekt-Name
        if not result.get('project'):
            result['project'] = entry.get('organizationName', '')
        
        # Projektnummer und Auftragsnummer
        result['projektnummer'] = entry.get('projektnummer', '')
        result['auftragsnummer'] = entry.get('auftragsnummer', '')
        
        # Kommentar
        result['kommentar'] = entry.get('kommentar', entry.get('description', ''))
        
        # Stunden berechnen
        result = self._calculate_hours_workexpert(result, entry)
        
        return result
    
    def _format_pause_workexpert(self, breaks: List[Dict]) -> str:
        """
        Formatiert Pausen im WorkExpert-Format (HH:MM-HH:MM).
        
        Args:
            breaks: Liste von Pauseneinträgen
            
        Returns:
            Formatierter String (z.B. "11:30-12:00")
        """
        if not breaks:
            return ''
        
        formatted = []
        for brk in breaks or []:
            try:
                start = datetime.fromisoformat(brk['from'].replace('Z', '+00:00'))
                end = datetime.fromisoformat(brk['to'].replace('Z', '+00:00'))
                formatted.append(f"{start.strftime('%H:%M')}-{end.strftime('%H:%M')}")
            except Exception:
                pass
        
        return ';'.join(formatted) if formatted else ''
    
    def _calculate_hours_workexpert(self, result: Dict, entry: Dict) -> Dict:
        """
        Berechnet Arbeitsstunden im WorkExpert-Format.
        
        Args:
            result: Bisheriges Ergebnis
            entry: Original-Eintrag
            
        Returns:
            Ergebnis mit berechneten Stunden (HH:MM Format)
        """
        try:
            if 'from' in entry and 'to' in entry:
                start = datetime.fromisoformat(entry['from'].replace('Z', '+00:00'))
                end = datetime.fromisoformat(entry['to'].replace('Z', '+00:00'))
                
                total_time = end - start
                total_minutes = int(total_time.total_seconds() / 60)
                
                # Pausen abziehen
                break_minutes = 0
                for brk in entry.get('breaks', []) or []:
                    try:
                        brk_start = datetime.fromisoformat(brk['from'].replace('Z', '+00:00'))
                        brk_end = datetime.fromisoformat(brk['to'].replace('Z', '+00:00'))
                        break_minutes += int((brk_end - brk_start).total_seconds() / 60)
                    except Exception:
                        pass
                
                # Format: HH:MM
                summe_mit_pause_h = total_minutes // 60
                summe_mit_pause_m = total_minutes % 60
                result['summe_mit_pause'] = f"{summe_mit_pause_h:02d}:{summe_mit_pause_m:02d}"
                
                work_minutes = total_minutes - break_minutes
                summe_ohne_pause_h = work_minutes // 60
                summe_ohne_pause_m = work_minutes % 60
                result['summe_ohne_pause'] = f"{summe_ohne_pause_h:02d}:{summe_ohne_pause_m:02d}"
                
                # Auch als Dezimalwert für Berechnungen
                result['total_hours'] = round(total_minutes / 60, 2)
                result['break_hours'] = round(break_minutes / 60, 2)
                result['actual_work_hours'] = round(work_minutes / 60, 2)
            else:
                result['summe_mit_pause'] = entry.get('summe_mit_pause', '')
                result['summe_ohne_pause'] = entry.get('summe_ohne_pause', '')
                result['total_hours'] = entry.get('total_hours', 0)
                result['break_hours'] = entry.get('break_hours', 0)
                result['actual_work_hours'] = entry.get('actual_work_hours', 0)
                
        except Exception as e:
            print(f"Fehler bei Stundenberechnung: {e}")
            result['summe_mit_pause'] = ''
            result['summe_ohne_pause'] = ''
            result['total_hours'] = 0
            result['break_hours'] = 0
            result['actual_work_hours'] = 0
        
        return result
    
    def _calculate_hours(self, result: Dict, entry: Dict) -> Dict:
        """
        Berechnet Arbeitsstunden für einen Eintrag.
        
        Args:
            result: Bisheriges Ergebnis
            entry: Original-Eintrag
            
        Returns:
            Ergebnis mit berechneten Stunden
        """
        try:
            if 'from' in entry and 'to' in entry:
                start = datetime.fromisoformat(entry['from'].replace('Z', '+00:00'))
                end = datetime.fromisoformat(entry['to'].replace('Z', '+00:00'))
                
                total_time = (end - start).total_seconds() / 3600
                
                # Pausen abziehen
                break_hours = 0
                for brk in entry.get('breaks', []) or []:
                    try:
                        brk_start = datetime.fromisoformat(brk['from'].replace('Z', '+00:00'))
                        brk_end = datetime.fromisoformat(brk['to'].replace('Z', '+00:00'))
                        break_hours += (brk_end - brk_start).total_seconds() / 3600
                    except Exception:
                        pass
                
                result['total_hours'] = round(total_time, 2)
                result['break_hours'] = round(break_hours, 2)
                result['actual_work_hours'] = round(total_time - break_hours, 2)
            else:
                result['total_hours'] = entry.get('total_hours', 0)
                result['break_hours'] = entry.get('break_hours', 0)
                result['actual_work_hours'] = entry.get('actual_work_hours', 0)
                
        except Exception as e:
            print(f"Fehler bei Stundenberechnung: {e}")
            result['total_hours'] = 0
            result['break_hours'] = 0
            result['actual_work_hours'] = 0
        
        return result
    
    def _format_breaks(self, breaks: List[Dict]) -> str:
        """
        Formatiert Pausen für die Anzeige.
        
        Args:
            breaks: Liste von Pauseneinträgen
            
        Returns:
            Formatierter String
        """
        if not breaks:
            return 'Keine Pausen'
        
        formatted = []
        for brk in breaks:
            try:
                start = datetime.fromisoformat(brk['from'].replace('Z', '+00:00'))
                end = datetime.fromisoformat(brk['to'].replace('Z', '+00:00'))
                duration = (end - start).total_seconds() / 3600
                
                formatted.append(
                    f"{start.strftime('%H:%M')}-{end.strftime('%H:%M')} ({duration:.1f}h)"
                )
            except Exception:
                pass
        
        return ', '.join(formatted) if formatted else 'Keine Pausen'
    
    # =========================================================================
    # CSV EXPORT
    # =========================================================================
    
    def to_csv(
        self,
        data: List[Dict],
        include_headers: bool = True,
        encoding: str = 'utf-8',
        delimiter: str = ';'
    ) -> str:
        """
        Konvertiert Daten zu CSV.
        
        Args:
            data: Liste von Daten-Dicts
            include_headers: Header-Zeile einfügen
            encoding: Zeichencodierung
            delimiter: Trennzeichen (Standard: ; für Excel)
            
        Returns:
            CSV-String
        """
        if not data:
            return ""
        
        output = io.StringIO()
        writer = csv.writer(output, delimiter=delimiter)
        
        # Header schreiben
        if include_headers:
            writer.writerow(self.CSV_HEADERS)
        
        # Daten schreiben
        for row in data:
            csv_row = self._dict_to_csv_row(row)
            writer.writerow(csv_row)
        
        return output.getvalue()
    
    def _dict_to_csv_row(self, data: Dict) -> List[str]:
        """
        Konvertiert ein Dict zu einer CSV-Zeile im WorkExpert-Format.
        
        Args:
            data: Daten-Dict
            
        Returns:
            Liste von Werten für CSV
        """
        return [
            str(data.get('personalnummer', '')),
            str(data.get('firstName', '')),
            str(data.get('lastName', '')),
            str(data.get('date_formatted', '')),
            str(data.get('type', 'Arbeitszeit')),
            str(data.get('start_time', '')),
            str(data.get('end_time', '')),
            str(data.get('pause', '')),
            str(data.get('summe_mit_pause', '')),
            str(data.get('summe_ohne_pause', '')),
            str(data.get('projektnummer', '')),
            str(data.get('auftragsnummer', '')),
            str(data.get('project', '')),
            str(data.get('kommentar', ''))
        ]
    
    def from_csv(self, csv_string: str, has_headers: bool = True) -> List[Dict]:
        """
        Konvertiert CSV zu Dict-Liste.
        
        Args:
            csv_string: CSV-String
            has_headers: Ob erste Zeile Header ist
            
        Returns:
            Liste von Dicts
        """
        if not csv_string:
            return []
        
        input_stream = io.StringIO(csv_string)
        reader = csv.reader(input_stream, delimiter=';')
        
        rows = list(reader)
        if not rows:
            return []
        
        if has_headers:
            headers = rows[0]
            data_rows = rows[1:]
        else:
            headers = self.CSV_HEADERS
            data_rows = rows
        
        result = []
        for row in data_rows:
            if len(row) >= len(headers):
                entry = dict(zip(headers, row))
                result.append(entry)
        
        return result
    
    # =========================================================================
    # HILFSMETHODEN
    # =========================================================================
    
    def summarize_time_entries(self, entries: List[Dict]) -> Dict:
        """
        Erstellt eine Zusammenfassung der Zeiteinträge.
        
        Args:
            entries: Liste von Zeiteinträgen
            
        Returns:
            Dict mit Zusammenfassung
        """
        if not entries:
            return {
                'total_entries': 0,
                'total_hours': 0,
                'total_break_hours': 0,
                'actual_work_hours': 0,
                'date_range': None
            }
        
        total_hours = sum(e.get('total_hours', 0) for e in entries)
        break_hours = sum(e.get('break_hours', 0) for e in entries)
        work_hours = sum(e.get('actual_work_hours', 0) for e in entries)
        
        dates = [e.get('sort_date') or e.get('date_formatted', '') for e in entries]
        dates = [d for d in dates if d]
        
        return {
            'total_entries': len(entries),
            'total_hours': round(total_hours, 2),
            'total_break_hours': round(break_hours, 2),
            'actual_work_hours': round(work_hours, 2),
            'date_range': {
                'from': min(dates) if dates else None,
                'to': max(dates) if dates else None
            }
        }
