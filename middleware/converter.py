"""
Middleware / Adapter:
- Holt Daten aus modules/GET_USERID & GET_TIMES
- Wandelt sie ins Frontend-Format
- Logging, Fehlerhandling, Caching (mit Ablaufzeit), Validation & Konsistenz
- CSV Export
"""

import csv
import io
from datetime import datetime, timedelta
from backend.modules import GET_USERID, GET_TIMES

# --- Cache mit Ablaufzeit ---
cache = {
    "users": {"data": None, "expires": None},
    "times": {}  # key = (user_id, from_iso, to_iso) -> {"data":..., "expires":...}
}
CACHE_TTL = timedelta(minutes=5)


# --- Custom Error ---
class MiddlewareError(Exception):
    def __init__(self, message, details=None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


# ------------------ Public Funktionen ------------------
def get_users(force_refresh=False):
    """Hole Benutzer aus API (mit Cache, Validation, Fehler)."""
    now = datetime.now()
    entry = cache["users"]

    if entry["data"] is not None and entry["expires"] > now and not force_refresh:
        print("[CACHE] User aus Cache")
        return entry["data"]

    try:
        print("[INFO] Hole User von API...")
        raw = GET_USERID.fetch_users()
        users = convert_users_to_frontend(raw)
        users = validate_users(users)
        cache["users"] = {"data": users, "expires": now + CACHE_TTL}
        print(f"[INFO] {len(users)} User geladen und gecached")
        return users
    except Exception as e:
        print("[ERROR] User konnten nicht geladen werden:", e)
        raise MiddlewareError("Fehler beim Laden der Benutzer", {"cause": str(e)})


def get_times(user_id, from_iso, to_iso, force_refresh=False):
    """Hole Zeiten eines Users (mit Cache, Validation, Fehler)."""
    if not user_id:
        raise MiddlewareError("Ungültige User-ID")

    try:
        from_dt = datetime.fromisoformat(from_iso)
        to_dt = datetime.fromisoformat(to_iso)
        if from_dt >= to_dt:
            raise MiddlewareError("Ungültiger Zeitraum: from >= to", {"from": from_iso, "to": to_iso})
    except ValueError:
        raise MiddlewareError("Ungültiges Datumsformat", {"from": from_iso, "to": to_iso})

    now = datetime.now()
    key = (user_id, from_iso, to_iso)
    if key in cache["times"]:
        entry = cache["times"][key]
        if entry["expires"] > now and not force_refresh:
            print(f"[CACHE] Zeiten für {user_id} aus Cache")
            return entry["data"]

    try:
        print(f"[INFO] Hole Zeiten für User={user_id}, von={from_iso} bis={to_iso}")
        raw = GET_TIMES.fetch_times(user_id, from_iso, to_iso)
        times = convert_times_to_frontend(raw)
        times = validate_times(times)
        cache["times"][key] = {"data": times, "expires": now + CACHE_TTL}
        print(f"[INFO] {len(times)} Zeit-Einträge geladen und gecached")
        return times
    except Exception as e:
        print("[ERROR] Zeiten konnten nicht geladen werden:", e)
        raise MiddlewareError("Fehler beim Laden der Zeiten", {"cause": str(e)})


def times_to_csv(times):
    """Exportiere Zeiten als CSV-Text."""
    try:
        print(f"[INFO] Exportiere {len(times)} Einträge nach CSV...")
        output = io.StringIO()
        fieldnames = ["date", "employee", "hours", "project", "company", "description", "start_time", "end_time"]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for row in times:
            writer.writerow({k: row.get(k, "") if row.get(k) is not None else "" for k in fieldnames})
        return output.getvalue()
    except Exception as e:
        print("[ERROR] CSV Export fehlgeschlagen:", e)
        raise MiddlewareError("Fehler beim CSV Export", {"cause": str(e)})


# ------------------ Converter ------------------
def convert_users_to_frontend(raw_users):
    out = []
    for u in raw_users:
        try:
            uid = u.get("id") or u.get("userId")
            name = u.get("name") or f"{u.get('firstName','')} {u.get('lastName','')}".strip()
            company = u.get("company") or u.get("companyName")
            out.append({"id": uid, "name": name, "company": company})
        except Exception as e:
            print("[WARN] Fehler beim Konvertieren eines Users:", e, u)
    return out


def convert_times_to_frontend(raw_times):
    out = []
    for t in raw_times:
        try:
            date = t.get("date") or t.get("dateTime") or t.get("day")
            if date and "T" in str(date):
                try:
                    date = datetime.fromisoformat(str(date)).date().isoformat()
                except:
                    pass
            out.append({
                "date": date,
                "employee": t.get("employee") or t.get("user") or t.get("name"),
                "hours": float(t["hours"]) if t.get("hours") is not None else None,
                "project": t.get("project") or t.get("task"),
                "company": t.get("company"),
                "description": t.get("description") or t.get("note"),
                "start_time": t.get("start_time") or t.get("start"),
                "end_time": t.get("end_time") or t.get("end"),
            })
        except Exception as e:
            print("[WARN] Fehler beim Konvertieren eines Time-Eintrags:", e, t)
    return out

# ------------------ Validation ------------------
def validate_users(users):
    """Validiere User-Liste (ID und Name dürfen nicht leer sein)."""
    valid = []
    for u in users:
        if not u.get("id") or not u.get("name"):
            print("[WARN] Ungültiger User entfernt:", u)
            continue
        valid.append(u)
    return valid


def validate_times(times):
    """Validiere Zeiten (Stunden >= 0, Start < Ende wenn beides da ist)."""
    valid = []
    for t in times:
        if t.get("hours") is not None and t["hours"] < 0:
            print("[WARN] Negative Stunden, Eintrag entfernt:", t)
            continue
        start = t.get("start_time")
        end = t.get("end_time")
        if start and end and start >= end:
            print("[WARN] Start >= Ende, Eintrag entfernt:", t)
            continue
        valid.append(t)
    return valid
