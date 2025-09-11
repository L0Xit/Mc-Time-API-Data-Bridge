#!/usr/bin/env python3
"""
Backend API - Provides data endpoints for the TGM-Adapter system
"""

from flask import Flask, jsonify, request
import json
from datetime import datetime

app = Flask(__name__)

# Sample data storage
users_data = [
    {"id": 1, "name": "Max Mustermann", "email": "max@example.com", "role": "admin"},
    {"id": 2, "name": "Anna Schmidt", "email": "anna@example.com", "role": "user"},
    {"id": 3, "name": "Tom Weber", "email": "tom@example.com", "role": "user"}
]

system_data = {
    "version": "1.0.0",
    "status": "running",
    "uptime": "24h 15m",
    "last_update": datetime.now().isoformat()
}

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "backend-api"
    })

@app.route('/api/users', methods=['GET'])
def get_users():
    """Get all users"""
    return jsonify({
        "success": True,
        "data": users_data,
        "count": len(users_data)
    })

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Get specific user by ID"""
    user = next((u for u in users_data if u["id"] == user_id), None)
    if user:
        return jsonify({
            "success": True,
            "data": user
        })
    else:
        return jsonify({
            "success": False,
            "error": "User not found"
        }), 404

@app.route('/api/users', methods=['POST'])
def create_user():
    """Create a new user"""
    data = request.get_json()
    if not data or not data.get('name') or not data.get('email'):
        return jsonify({
            "success": False,
            "error": "Name and email are required"
        }), 400
    
    new_id = max([u["id"] for u in users_data]) + 1 if users_data else 1
    new_user = {
        "id": new_id,
        "name": data["name"],
        "email": data["email"],
        "role": data.get("role", "user")
    }
    users_data.append(new_user)
    
    return jsonify({
        "success": True,
        "data": new_user,
        "message": "User created successfully"
    }), 201

@app.route('/api/system', methods=['GET'])
def get_system_info():
    """Get system information"""
    system_data["last_update"] = datetime.now().isoformat()
    return jsonify({
        "success": True,
        "data": system_data
    })

@app.route('/api/data', methods=['POST'])
def process_data():
    """Process incoming data"""
    data = request.get_json()
    if not data:
        return jsonify({
            "success": False,
            "error": "No data provided"
        }), 400
    
    # Simple data processing simulation
    processed_data = {
        "original": data,
        "processed_at": datetime.now().isoformat(),
        "result": f"Processed {len(str(data))} characters of data",
        "status": "completed"
    }
    
    return jsonify({
        "success": True,
        "data": processed_data
    })

if __name__ == '__main__':
    print("Starting Backend API Server...")
    print("Available endpoints:")
    print("  GET  /api/health - Health check")
    print("  GET  /api/users - Get all users")
    print("  GET  /api/users/<id> - Get specific user")
    print("  POST /api/users - Create new user")
    print("  GET  /api/system - Get system info")
    print("  POST /api/data - Process data")
    app.run(host='0.0.0.0', port=5001, debug=True)