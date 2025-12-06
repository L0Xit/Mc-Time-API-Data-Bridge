"""
Mc-Time API Data Bridge - Middleware Layer
Zentrale Middleware-Schicht für alle API-Kommunikation

Architektur:
    Frontend → Middleware → McTime API
    
Die Middleware übernimmt:
    - API-Key Authentifizierung
    - Request/Response Handling
    - Rate Limiting
    - Fehlerbehandlung
    - JSON ↔ CSV Konvertierung
    - Caching (optional)
"""

from .core import Middleware
from .auth import AuthHandler
from .request_handler import RequestHandler

__all__ = ['Middleware', 'AuthHandler', 'RequestHandler']
