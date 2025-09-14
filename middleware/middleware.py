#!/usr/bin/env python3
"""
TGM-Adapter Middleware Component
Handles communication between frontend and backend.
"""

import time
import sys

def main():
    """Main middleware function"""
    print("Starting TGM-Adapter Middleware...")
    print("Middleware is running and managing communications.")
    
    try:
        # Simple keep-alive loop for demonstration
        while True:
            print("Middleware: Routing requests... (Press Ctrl+C to stop)")
            time.sleep(4)
    except KeyboardInterrupt:
        print("\nMiddleware: Shutting down gracefully...")
        sys.exit(0)

if __name__ == "__main__":
    main()