"""
Adapter Middleware für Mc-Time API Data Bridge
==============================================

Dieses Modul stellt die Middleware-Schicht bereit, die als Adapter zwischen
dem Backend (McTime API) und dem Frontend (Flask-Anwendung) fungiert.

Architektur:
    Frontend (Flask) <--> Adapter Middleware <--> Backend (McTime API)

Hauptkomponenten:
    - AdapterMiddleware: Hauptklasse für Datenverarbeitung und Transformation
    - DataTransformer: JSON zu CSV/Frontend-Format Konvertierung
    - RateLimiter: API Rate Limiting Handling
    - ErrorHandler: Einheitliches Fehlerhandling

Autor: Adapter Middleware Team
Version: 1.0.0
"""

from .adapter import AdapterMiddleware
from .transformer import DataTransformer
from .rate_limiter import RateLimiter
from .error_handler import MiddlewareError, ErrorHandler

__all__ = [
    'AdapterMiddleware',
    'DataTransformer', 
    'RateLimiter',
    'MiddlewareError',
    'ErrorHandler'
]

__version__ = '1.0.0'
