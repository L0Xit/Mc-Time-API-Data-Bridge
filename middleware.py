#!/usr/bin/env python3
"""
TGM-Adapter Middleware - Acts as an adapter/proxy between frontend and backend
"""

from flask import Flask, jsonify, request, make_response
import requests
import json
from datetime import datetime
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Backend configuration
BACKEND_URL = "http://localhost:5001"

class TGMAdapter:
    """TGM Adapter class for handling communication between frontend and backend"""
    
    def __init__(self, backend_url):
        self.backend_url = backend_url
        self.request_count = 0
        self.start_time = datetime.now()
    
    def log_request(self, method, endpoint, data=None):
        """Log incoming requests"""
        self.request_count += 1
        logger.info(f"[{self.request_count}] {method} {endpoint} - Data: {data}")
    
    def forward_request(self, method, endpoint, data=None, params=None):
        """Forward request to backend and handle response"""
        try:
            url = f"{self.backend_url}{endpoint}"
            
            if method.upper() == 'GET':
                response = requests.get(url, params=params, timeout=10)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, timeout=10)
            elif method.upper() == 'PUT':
                response = requests.put(url, json=data, timeout=10)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, timeout=10)
            else:
                return {
                    "success": False,
                    "error": f"Unsupported HTTP method: {method}"
                }, 400
            
            # Add adapter metadata to response
            try:
                response_data = response.json()
                response_data["adapter_info"] = {
                    "processed_by": "TGM-Adapter",
                    "timestamp": datetime.now().isoformat(),
                    "request_id": self.request_count,
                    "backend_status": response.status_code
                }
            except:
                response_data = {
                    "success": False,
                    "error": "Invalid JSON response from backend",
                    "adapter_info": {
                        "processed_by": "TGM-Adapter",
                        "timestamp": datetime.now().isoformat(),
                        "request_id": self.request_count,
                        "backend_status": response.status_code
                    }
                }
            
            return response_data, response.status_code
            
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error": "Backend service unavailable",
                "adapter_info": {
                    "processed_by": "TGM-Adapter",
                    "timestamp": datetime.now().isoformat(),
                    "request_id": self.request_count,
                    "backend_status": "connection_error"
                }
            }, 503
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "Backend request timeout",
                "adapter_info": {
                    "processed_by": "TGM-Adapter",
                    "timestamp": datetime.now().isoformat(),
                    "request_id": self.request_count,
                    "backend_status": "timeout"
                }
            }, 504
        except Exception as e:
            return {
                "success": False,
                "error": f"Adapter error: {str(e)}",
                "adapter_info": {
                    "processed_by": "TGM-Adapter",
                    "timestamp": datetime.now().isoformat(),
                    "request_id": self.request_count,
                    "backend_status": "error"
                }
            }, 500

# Initialize the adapter
adapter = TGMAdapter(BACKEND_URL)

@app.route('/adapter/status', methods=['GET'])
def adapter_status():
    """Get adapter status and statistics"""
    uptime = datetime.now() - adapter.start_time
    return jsonify({
        "service": "TGM-Adapter",
        "status": "running",
        "version": "1.0.0",
        "uptime_seconds": uptime.total_seconds(),
        "requests_processed": adapter.request_count,
        "backend_url": BACKEND_URL,
        "timestamp": datetime.now().isoformat()
    })

# Proxy endpoints for backend API

@app.route('/adapter/health', methods=['GET'])
def health():
    """Proxy health check to backend"""
    adapter.log_request('GET', '/api/health')
    data, status_code = adapter.forward_request('GET', '/api/health')
    return jsonify(data), status_code

@app.route('/adapter/users', methods=['GET', 'POST'])
def users():
    """Proxy users endpoint to backend"""
    if request.method == 'GET':
        adapter.log_request('GET', '/api/users')
        data, status_code = adapter.forward_request('GET', '/api/users')
    else:  # POST
        request_data = request.get_json()
        adapter.log_request('POST', '/api/users', request_data)
        data, status_code = adapter.forward_request('POST', '/api/users', request_data)
    
    return jsonify(data), status_code

@app.route('/adapter/users/<int:user_id>', methods=['GET'])
def user_detail(user_id):
    """Proxy specific user endpoint to backend"""
    adapter.log_request('GET', f'/api/users/{user_id}')
    data, status_code = adapter.forward_request('GET', f'/api/users/{user_id}')
    return jsonify(data), status_code

@app.route('/adapter/system', methods=['GET'])
def system():
    """Proxy system info endpoint to backend"""
    adapter.log_request('GET', '/api/system')
    data, status_code = adapter.forward_request('GET', '/api/system')
    return jsonify(data), status_code

@app.route('/adapter/data', methods=['POST'])
def process_data():
    """Proxy data processing endpoint to backend"""
    request_data = request.get_json()
    adapter.log_request('POST', '/api/data', request_data)
    
    # Add adapter preprocessing
    if request_data:
        request_data["adapter_preprocessed"] = True
        request_data["preprocessed_at"] = datetime.now().isoformat()
    
    data, status_code = adapter.forward_request('POST', '/api/data', request_data)
    return jsonify(data), status_code

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        "success": False,
        "error": "Endpoint not found in TGM-Adapter",
        "available_endpoints": [
            "/adapter/status",
            "/adapter/health", 
            "/adapter/users",
            "/adapter/users/<id>",
            "/adapter/system",
            "/adapter/data"
        ],
        "adapter_info": {
            "processed_by": "TGM-Adapter",
            "timestamp": datetime.now().isoformat()
        }
    }), 404

if __name__ == '__main__':
    print("Starting TGM-Adapter Middleware...")
    print("Backend URL:", BACKEND_URL)
    print("Available adapter endpoints:")
    print("  GET  /adapter/status - Adapter status")
    print("  GET  /adapter/health - Health check (proxied)")
    print("  GET  /adapter/users - Get users (proxied)")
    print("  POST /adapter/users - Create user (proxied)")
    print("  GET  /adapter/users/<id> - Get user (proxied)")
    print("  GET  /adapter/system - System info (proxied)")
    print("  POST /adapter/data - Process data (proxied)")
    app.run(host='0.0.0.0', port=5000, debug=True)