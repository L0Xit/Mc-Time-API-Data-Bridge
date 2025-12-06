"""
Request Handler - Stabiler Request-Ablauf mit Fehlerbehandlung & Rate Limiting
"""

import requests
import time
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from functools import wraps

from .auth import AuthHandler


class RateLimiter:
    """
    Einfacher Rate Limiter für API-Requests
    """
    
    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        """
        Initialisiert Rate Limiter
        
        Args:
            max_requests: Maximale Anzahl Requests pro Zeitfenster
            window_seconds: Größe des Zeitfensters in Sekunden
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = []
    
    def can_make_request(self) -> bool:
        """
        Prüft ob ein Request gemacht werden kann
        
        Returns:
            True wenn Request erlaubt
        """
        now = datetime.now()
        window_start = now - timedelta(seconds=self.window_seconds)
        
        # Entferne alte Requests
        self.requests = [r for r in self.requests if r > window_start]
        
        return len(self.requests) < self.max_requests
    
    def record_request(self):
        """Zeichnet einen Request auf"""
        self.requests.append(datetime.now())
    
    def wait_time(self) -> float:
        """
        Gibt Wartezeit bis zum nächsten erlaubten Request zurück
        
        Returns:
            Wartezeit in Sekunden
        """
        if self.can_make_request():
            return 0.0
        
        oldest = min(self.requests)
        wait = (oldest + timedelta(seconds=self.window_seconds) - datetime.now()).total_seconds()
        return max(0.0, wait)


class RequestHandler:
    """
    Zentraler Request Handler für alle API-Kommunikation
    Bietet:
    - Retry-Logik
    - Rate Limiting
    - Fehlerbehandlung
    - Logging
    """
    
    def __init__(self, auth: AuthHandler):
        """
        Initialisiert Request Handler
        
        Args:
            auth: AuthHandler für API-Authentifizierung
        """
        self.auth = auth
        self.base_url = "https://mctime.com/api/v2/auth"
        self.timeout = 30
        self.max_retries = 3
        self.retry_delay = 1.0
        
        # Rate Limiting
        self.rate_limiter = RateLimiter(max_requests=60, window_seconds=60)
        
        # Request-Statistiken
        self._stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "retried_requests": 0
        }
    
    def get(
        self,
        endpoint: str,
        params: Dict = None,
        retry: bool = True
    ) -> Optional[Dict]:
        """
        Führt GET-Request aus
        
        Args:
            endpoint: API-Endpoint (z.B. "/users")
            params: Query-Parameter
            retry: Wenn True, wird bei Fehler wiederholt
            
        Returns:
            Response-Daten oder None bei Fehler
        """
        return self._make_request("GET", endpoint, params=params, retry=retry)
    
    def post(
        self,
        endpoint: str,
        data: Dict = None,
        params: Dict = None,
        retry: bool = True
    ) -> Optional[Dict]:
        """
        Führt POST-Request aus
        
        Args:
            endpoint: API-Endpoint
            data: Request-Body
            params: Query-Parameter
            retry: Wenn True, wird bei Fehler wiederholt
            
        Returns:
            Response-Daten oder None bei Fehler
        """
        return self._make_request("POST", endpoint, data=data, params=params, retry=retry)
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Dict = None,
        params: Dict = None,
        retry: bool = True,
        attempt: int = 1
    ) -> Optional[Dict]:
        """
        Interne Methode für API-Requests
        
        Args:
            method: HTTP-Methode (GET, POST, etc.)
            endpoint: API-Endpoint
            data: Request-Body (für POST)
            params: Query-Parameter
            retry: Retry bei Fehler aktiviert
            attempt: Aktueller Versuch (für Retry)
            
        Returns:
            Response-Daten oder None
        """
        # Rate Limiting prüfen
        if not self.rate_limiter.can_make_request():
            wait_time = self.rate_limiter.wait_time()
            print(f"Rate Limit erreicht. Warte {wait_time:.1f}s...")
            time.sleep(wait_time)
        
        url = f"{self.base_url}{endpoint}"
        headers = self.auth.get_headers()
        
        self._stats["total_requests"] += 1
        
        try:
            print(f"[Request] {method} {url}")
            if params:
                print(f"[Params] {params}")
            
            self.rate_limiter.record_request()
            
            if method == "GET":
                response = requests.get(
                    url,
                    headers=headers,
                    params=params,
                    timeout=self.timeout
                )
            elif method == "POST":
                response = requests.post(
                    url,
                    headers=headers,
                    json=data,
                    params=params,
                    timeout=self.timeout
                )
            else:
                raise ValueError(f"Nicht unterstützte Methode: {method}")
            
            # Response verarbeiten
            return self._handle_response(response, method, endpoint, data, params, retry, attempt)
            
        except requests.exceptions.Timeout:
            print(f"[Timeout] Request nach {self.timeout}s abgebrochen")
            return self._handle_error("timeout", method, endpoint, data, params, retry, attempt)
            
        except requests.exceptions.ConnectionError as e:
            print(f"[Verbindungsfehler] {e}")
            return self._handle_error("connection", method, endpoint, data, params, retry, attempt)
            
        except requests.exceptions.RequestException as e:
            print(f"[Request-Fehler] {e}")
            return self._handle_error("request", method, endpoint, data, params, retry, attempt)
            
        except Exception as e:
            print(f"[Unbekannter Fehler] {e}")
            self._stats["failed_requests"] += 1
            return None
    
    def _handle_response(
        self,
        response: requests.Response,
        method: str,
        endpoint: str,
        data: Dict,
        params: Dict,
        retry: bool,
        attempt: int
    ) -> Optional[Dict]:
        """
        Verarbeitet API-Response
        """
        print(f"[Response] Status: {response.status_code}")
        
        if response.status_code == 200:
            self._stats["successful_requests"] += 1
            try:
                return response.json()
            except ValueError:
                print("[Warnung] Response ist kein gültiges JSON")
                return {"raw": response.text}
        
        elif response.status_code == 429:
            # Rate Limit
            print("[Rate Limit] Zu viele Requests")
            retry_after = int(response.headers.get("Retry-After", 60))
            if retry and attempt < self.max_retries:
                print(f"Warte {retry_after}s vor Retry...")
                time.sleep(retry_after)
                return self._make_request(method, endpoint, data, params, retry, attempt + 1)
            return None
        
        elif response.status_code == 401:
            print("[Auth-Fehler] API-Key ungültig oder abgelaufen")
            self._stats["failed_requests"] += 1
            return None
        
        elif response.status_code == 403:
            print("[Zugriffsfehler] Keine Berechtigung für diesen Endpoint")
            self._stats["failed_requests"] += 1
            return None
        
        elif response.status_code == 404:
            print("[Nicht gefunden] Endpoint oder Ressource existiert nicht")
            self._stats["failed_requests"] += 1
            return None
        
        elif response.status_code >= 500:
            # Server-Fehler - Retry möglich
            print(f"[Server-Fehler] Status {response.status_code}")
            return self._handle_error("server", method, endpoint, data, params, retry, attempt)
        
        else:
            print(f"[Unbekannter Status] {response.status_code}: {response.text}")
            self._stats["failed_requests"] += 1
            return None
    
    def _handle_error(
        self,
        error_type: str,
        method: str,
        endpoint: str,
        data: Dict,
        params: Dict,
        retry: bool,
        attempt: int
    ) -> Optional[Dict]:
        """
        Behandelt Fehler und führt ggf. Retry durch
        """
        if retry and attempt < self.max_retries:
            self._stats["retried_requests"] += 1
            delay = self.retry_delay * (2 ** (attempt - 1))  # Exponential Backoff
            print(f"[Retry] Versuch {attempt + 1}/{self.max_retries} in {delay:.1f}s...")
            time.sleep(delay)
            return self._make_request(method, endpoint, data, params, retry, attempt + 1)
        
        self._stats["failed_requests"] += 1
        print(f"[Fehler] Alle {self.max_retries} Versuche fehlgeschlagen")
        return None
    
    def get_stats(self) -> Dict:
        """
        Gibt Request-Statistiken zurück
        
        Returns:
            Dict mit Statistiken
        """
        return {
            **self._stats,
            "success_rate": (
                self._stats["successful_requests"] / self._stats["total_requests"] * 100
                if self._stats["total_requests"] > 0 else 0.0
            )
        }
    
    def reset_stats(self):
        """Setzt Statistiken zurück"""
        self._stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "retried_requests": 0
        }
