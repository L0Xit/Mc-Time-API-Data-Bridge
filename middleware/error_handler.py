"""
Error Handler - Einheitliches Fehlerhandling
=============================================

Dieses Modul stellt einheitliches Fehlerhandling für die
Middleware bereit. Es definiert spezifische Fehlerklassen
und einen zentralen Error Handler.

Features:
    - Spezifische Fehlertypen für verschiedene Szenarien
    - Logging von Fehlern
    - Einheitliche Fehler-Responses für das Frontend
"""

import logging
import traceback
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum


# =========================================================================
# LOGGING SETUP
# =========================================================================

# Logger für die Middleware
logger = logging.getLogger('middleware')

# Falls noch kein Handler konfiguriert ist
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)


# =========================================================================
# FEHLER-CODES
# =========================================================================

class ErrorCode(Enum):
    """Definiert alle möglichen Fehler-Codes."""
    
    # Authentifizierung
    API_KEY_MISSING = "API_KEY_MISSING"
    API_KEY_INVALID = "API_KEY_INVALID"
    AUTH_FAILED = "AUTH_FAILED"
    
    # Rate Limiting
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    
    # API Fehler
    API_CONNECTION_ERROR = "API_CONNECTION_ERROR"
    API_TIMEOUT = "API_TIMEOUT"
    API_RESPONSE_ERROR = "API_RESPONSE_ERROR"
    
    # Daten-Fehler
    INVALID_DATE_FORMAT = "INVALID_DATE_FORMAT"
    INVALID_PARAMETER = "INVALID_PARAMETER"
    DATA_NOT_FOUND = "DATA_NOT_FOUND"
    DATA_PARSE_ERROR = "DATA_PARSE_ERROR"
    
    # System-Fehler
    BACKEND_IMPORT_ERROR = "BACKEND_IMPORT_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"


# =========================================================================
# FEHLER-KLASSEN
# =========================================================================

class MiddlewareError(Exception):
    """
    Basis-Fehlerklasse für alle Middleware-Fehler.
    
    Attributes:
        code: Fehler-Code
        message: Benutzerfreundliche Fehlermeldung
        details: Optionale zusätzliche Details
        timestamp: Zeitpunkt des Fehlers
    """
    
    def __init__(
        self,
        code: str,
        message: str,
        details: Dict = None,
        original_error: Exception = None
    ):
        """
        Initialisiert den Middleware-Fehler.
        
        Args:
            code: Fehler-Code (aus ErrorCode Enum)
            message: Benutzerfreundliche Fehlermeldung
            details: Optionale zusätzliche Details
            original_error: Original-Exception falls vorhanden
        """
        super().__init__(message)
        
        self.code = code
        self.message = message
        self.details = details or {}
        self.original_error = original_error
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict:
        """
        Konvertiert den Fehler zu einem Dict für JSON-Response.
        
        Returns:
            Dict mit Fehler-Informationen
        """
        return {
            'status': 'error',
            'code': self.code,
            'message': self.message,
            'details': self.details,
            'timestamp': self.timestamp.isoformat()
        }
    
    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"


class AuthenticationError(MiddlewareError):
    """Fehler bei der Authentifizierung."""
    
    def __init__(self, message: str = "Authentifizierung fehlgeschlagen"):
        super().__init__(
            code=ErrorCode.AUTH_FAILED.value,
            message=message
        )


class RateLimitError(MiddlewareError):
    """Fehler bei Rate Limit Überschreitung."""
    
    def __init__(self, wait_time: float = 0):
        super().__init__(
            code=ErrorCode.RATE_LIMIT_EXCEEDED.value,
            message=f"Rate Limit erreicht. Bitte warten Sie {wait_time:.0f} Sekunden.",
            details={'wait_time': wait_time}
        )


class ValidationError(MiddlewareError):
    """Fehler bei Eingabevalidierung."""
    
    def __init__(self, field: str, message: str):
        super().__init__(
            code=ErrorCode.INVALID_PARAMETER.value,
            message=message,
            details={'field': field}
        )


class ApiConnectionError(MiddlewareError):
    """Fehler bei API-Verbindung."""
    
    def __init__(self, message: str = "Verbindung zur API fehlgeschlagen"):
        super().__init__(
            code=ErrorCode.API_CONNECTION_ERROR.value,
            message=message
        )


# =========================================================================
# ERROR HANDLER
# =========================================================================

class ErrorHandler:
    """
    Zentraler Error Handler für die Middleware.
    
    Verantwortlich für:
        - Fehler-Logging
        - Fehler-Transformation
        - Einheitliche Fehler-Responses
    """
    
    def __init__(self, log_to_file: bool = False, log_path: str = None):
        """
        Initialisiert den Error Handler.
        
        Args:
            log_to_file: Ob Fehler in Datei geloggt werden sollen
            log_path: Pfad zur Log-Datei
        """
        self.logger = logger
        
        if log_to_file and log_path:
            file_handler = logging.FileHandler(log_path)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            ))
            self.logger.addHandler(file_handler)
    
    def handle_error(
        self,
        error: Exception,
        context: str = None,
        return_empty: bool = True
    ) -> Any:
        """
        Behandelt einen Fehler einheitlich.
        
        Args:
            error: Die aufgetretene Exception
            context: Kontext wo der Fehler auftrat
            return_empty: Ob leere Liste/Dict zurückgegeben werden soll
            
        Returns:
            Leere Liste, leeres Dict, oder re-raised Exception
        """
        # Logging
        self.log_error(error, context)
        
        # Bei MiddlewareError: Re-raise für spezielle Behandlung
        if isinstance(error, MiddlewareError):
            if return_empty:
                return error.to_dict()
            raise error
        
        # Standard-Fehler: Einheitliche Response
        if return_empty:
            return {
                'status': 'error',
                'code': ErrorCode.INTERNAL_ERROR.value,
                'message': str(error),
                'context': context
            }
        
        raise error
    
    def log_error(self, error: Exception, context: str = None):
        """
        Loggt einen Fehler.
        
        Args:
            error: Die Exception
            context: Kontext-Information
        """
        error_info = {
            'type': type(error).__name__,
            'message': str(error),
            'context': context,
            'timestamp': datetime.now().isoformat()
        }
        
        if isinstance(error, MiddlewareError):
            error_info['code'] = error.code
            error_info['details'] = error.details
        
        # Log-Level basierend auf Fehlertyp
        if isinstance(error, (RateLimitError, ValidationError)):
            self.logger.warning(f"Middleware Warning: {error_info}")
        else:
            self.logger.error(f"Middleware Error: {error_info}")
            self.logger.debug(traceback.format_exc())
    
    def create_error_response(
        self,
        error: Exception,
        include_trace: bool = False
    ) -> Dict:
        """
        Erstellt eine einheitliche Fehler-Response.
        
        Args:
            error: Die Exception
            include_trace: Ob Stacktrace inkludiert werden soll
            
        Returns:
            Dict für JSON-Response
        """
        if isinstance(error, MiddlewareError):
            response = error.to_dict()
        else:
            response = {
                'status': 'error',
                'code': ErrorCode.INTERNAL_ERROR.value,
                'message': str(error),
                'timestamp': datetime.now().isoformat()
            }
        
        if include_trace:
            response['trace'] = traceback.format_exc()
        
        return response
    
    @staticmethod
    def is_recoverable(error: Exception) -> bool:
        """
        Prüft ob ein Fehler wiederherstellbar ist.
        
        Args:
            error: Die Exception
            
        Returns:
            True wenn der Fehler wiederherstellbar ist
        """
        recoverable_codes = [
            ErrorCode.RATE_LIMIT_EXCEEDED.value,
            ErrorCode.API_TIMEOUT.value,
            ErrorCode.API_CONNECTION_ERROR.value
        ]
        
        if isinstance(error, MiddlewareError):
            return error.code in recoverable_codes
        
        return False


# =========================================================================
# GLOBALE ERROR HANDLER INSTANZ
# =========================================================================

error_handler = ErrorHandler()
