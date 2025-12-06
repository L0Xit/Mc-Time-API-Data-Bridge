"""
Auth Handler - API-Key Authentifizierung für McTime API
"""

import os
from typing import Dict, Optional
from datetime import datetime, timedelta


class AuthHandler:
    """
    Verwaltet API-Key Authentifizierung für McTime API
    """
    
    def __init__(self, api_key: str = None):
        """
        Initialisiert Auth Handler
        
        Args:
            api_key: McTime API-Key
        """
        self._api_key = api_key or os.getenv('MCTIME_API_KEY')
        self._last_validation = None
        self._is_valid = False
    
    @property
    def api_key(self) -> str:
        """Gibt API-Key zurück"""
        return self._api_key
    
    @api_key.setter
    def api_key(self, value: str):
        """Setzt API-Key und invalidiert Cache"""
        self._api_key = value
        self._is_valid = False
        self._last_validation = None
    
    def get_headers(self) -> Dict[str, str]:
        """
        Erstellt Request-Headers mit API-Key Authentifizierung
        
        Returns:
            Dict mit HTTP-Headers
        """
        if not self._api_key:
            raise ValueError("API-Key nicht konfiguriert!")
        
        return {
            "content-type": "application/json",
            "API_KEY": self._api_key
        }
    
    def validate_key(self, force: bool = False) -> bool:
        """
        Validiert den API-Key (mit Caching)
        
        Args:
            force: Wenn True, Cache wird ignoriert
            
        Returns:
            True wenn API-Key gültig
        """
        # Prüfe Cache (5 Minuten gültig)
        if not force and self._last_validation:
            cache_duration = timedelta(minutes=5)
            if datetime.now() - self._last_validation < cache_duration:
                return self._is_valid
        
        # Validiere API-Key
        if not self._api_key:
            self._is_valid = False
            return False
        
        # API-Key Format-Validierung (optional)
        if len(self._api_key) < 10:
            self._is_valid = False
            return False
        
        # Für echte Validierung: Request an API senden
        # Hier nur Format-Check
        self._is_valid = True
        self._last_validation = datetime.now()
        
        return self._is_valid
    
    def is_configured(self) -> bool:
        """Prüft ob API-Key konfiguriert ist"""
        return bool(self._api_key)
    
    def get_auth_status(self) -> Dict:
        """
        Gibt Authentifizierungs-Status zurück
        
        Returns:
            Dict mit Status-Informationen
        """
        return {
            "configured": self.is_configured(),
            "valid": self._is_valid,
            "last_validation": self._last_validation.isoformat() if self._last_validation else None,
            "key_masked": self._mask_key()
        }
    
    def _mask_key(self) -> str:
        """Maskiert API-Key für sichere Anzeige"""
        if not self._api_key:
            return "Nicht konfiguriert"
        
        if len(self._api_key) <= 8:
            return "****"
        
        return f"{self._api_key[:4]}...{self._api_key[-4:]}"
