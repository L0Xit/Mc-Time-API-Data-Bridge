"""
Rate Limiter - API Rate Limiting Handling
==========================================

Dieses Modul implementiert Rate Limiting für API-Anfragen.
Es schützt vor Überlastung der McTime API und verhindert
das Überschreiten von API-Limits.

Features:
    - Sliding Window Rate Limiting
    - Konfigurierbare Limits
    - Automatische Wartezeit-Berechnung
"""

import time
from collections import deque
from typing import Optional
from threading import Lock


class RateLimiter:
    """
    Rate Limiter mit Sliding Window Algorithmus.
    
    Verwendung:
        limiter = RateLimiter(max_requests=100, time_window=60)
        
        if limiter.check():
            # Request ausführen
            limiter.record_request()
        else:
            wait_time = limiter.get_wait_time()
            print(f"Warte {wait_time} Sekunden")
    """
    
    def __init__(
        self,
        max_requests: int = 100,
        time_window: int = 60,
        enabled: bool = True
    ):
        """
        Initialisiert den Rate Limiter.
        
        Args:
            max_requests: Maximale Anzahl Requests im Zeitfenster
            time_window: Zeitfenster in Sekunden
            enabled: Ob Rate Limiting aktiv ist
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.enabled = enabled
        
        # Speichert Timestamps der Requests
        self._requests = deque()
        self._lock = Lock()
    
    def check(self) -> bool:
        """
        Prüft ob ein neuer Request erlaubt ist.
        
        Returns:
            True wenn Request erlaubt, False wenn Limit erreicht
        """
        if not self.enabled:
            return True
        
        with self._lock:
            self._cleanup_old_requests()
            return len(self._requests) < self.max_requests
    
    def record_request(self):
        """
        Zeichnet einen neuen Request auf.
        Sollte nach jedem erfolgreichen Request aufgerufen werden.
        """
        if not self.enabled:
            return
        
        with self._lock:
            self._requests.append(time.time())
    
    def get_remaining(self) -> int:
        """
        Gibt die Anzahl verbleibender Requests zurück.
        
        Returns:
            Anzahl verbleibender Requests im aktuellen Fenster
        """
        if not self.enabled:
            return self.max_requests
        
        with self._lock:
            self._cleanup_old_requests()
            return max(0, self.max_requests - len(self._requests))
    
    def get_wait_time(self) -> float:
        """
        Gibt die Wartezeit bis zum nächsten erlaubten Request zurück.
        
        Returns:
            Wartezeit in Sekunden (0 wenn kein Warten nötig)
        """
        if not self.enabled:
            return 0
        
        with self._lock:
            self._cleanup_old_requests()
            
            if len(self._requests) < self.max_requests:
                return 0
            
            # Ältester Request + Zeitfenster = wann er abläuft
            oldest = self._requests[0]
            expiry = oldest + self.time_window
            wait = expiry - time.time()
            
            return max(0, wait)
    
    def reset(self):
        """
        Setzt den Rate Limiter zurück.
        Löscht alle aufgezeichneten Requests.
        """
        with self._lock:
            self._requests.clear()
    
    def get_status(self) -> dict:
        """
        Gibt den aktuellen Status des Rate Limiters zurück.
        
        Returns:
            Dict mit Status-Informationen
        """
        with self._lock:
            self._cleanup_old_requests()
            
            return {
                'enabled': self.enabled,
                'max_requests': self.max_requests,
                'time_window': self.time_window,
                'current_requests': len(self._requests),
                'remaining': max(0, self.max_requests - len(self._requests)),
                'wait_time': self.get_wait_time()
            }
    
    def _cleanup_old_requests(self):
        """
        Entfernt abgelaufene Requests aus dem Fenster.
        Muss innerhalb eines Locks aufgerufen werden.
        """
        current_time = time.time()
        cutoff = current_time - self.time_window
        
        # Entferne alle Requests die älter sind als das Zeitfenster
        while self._requests and self._requests[0] < cutoff:
            self._requests.popleft()


class AdaptiveRateLimiter(RateLimiter):
    """
    Erweiterter Rate Limiter mit adaptiver Anpassung.
    
    Passt das Rate Limit automatisch basierend auf API-Antworten an.
    Bei 429-Fehlern wird das Limit reduziert.
    """
    
    def __init__(
        self,
        max_requests: int = 100,
        time_window: int = 60,
        min_requests: int = 10,
        reduction_factor: float = 0.5,
        recovery_factor: float = 1.1,
        recovery_period: int = 300
    ):
        """
        Initialisiert den adaptiven Rate Limiter.
        
        Args:
            max_requests: Maximale Anzahl Requests
            time_window: Zeitfenster in Sekunden
            min_requests: Minimales Limit (wird nie unterschritten)
            reduction_factor: Faktor bei Rate-Limit-Fehler (0.5 = halbieren)
            recovery_factor: Faktor bei Erholung (1.1 = 10% erhöhen)
            recovery_period: Sekunden bis zur Erholung
        """
        super().__init__(max_requests, time_window)
        
        self.original_max = max_requests
        self.min_requests = min_requests
        self.reduction_factor = reduction_factor
        self.recovery_factor = recovery_factor
        self.recovery_period = recovery_period
        
        self._last_reduction = None
        self._consecutive_successes = 0
    
    def record_rate_limit_error(self):
        """
        Wird aufgerufen wenn die API einen Rate-Limit-Fehler (429) zurückgibt.
        Reduziert das Limit automatisch.
        """
        with self._lock:
            new_max = int(self.max_requests * self.reduction_factor)
            self.max_requests = max(self.min_requests, new_max)
            self._last_reduction = time.time()
            self._consecutive_successes = 0
            
            print(f"Rate Limit reduziert auf {self.max_requests} Requests")
    
    def record_success(self):
        """
        Wird nach einem erfolgreichen Request aufgerufen.
        Erhöht das Limit nach einer Erholungsphase.
        """
        self.record_request()
        
        with self._lock:
            self._consecutive_successes += 1
            
            # Prüfen ob Erholung möglich ist
            if (self._last_reduction and 
                time.time() - self._last_reduction > self.recovery_period and
                self._consecutive_successes > 10):
                
                new_max = int(self.max_requests * self.recovery_factor)
                self.max_requests = min(self.original_max, new_max)
                self._consecutive_successes = 0
                
                print(f"Rate Limit erhöht auf {self.max_requests} Requests")
