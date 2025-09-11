#!/bin/bash

# TGM-Adapter System Startup Script
# This script starts all three components of the TGM-Adapter system

echo "=== TGM-Adapter System Startup ==="
echo "Starting all components..."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

# Install dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies..."
    pip3 install -r requirements.txt
fi

echo ""
echo "Starting components in the following order:"
echo "1. Backend API (Port 5001)"
echo "2. TGM-Adapter Middleware (Port 5000)" 
echo "3. Frontend Web Interface (Port 8080)"
echo ""

# Start backend in background
echo "Starting Backend API..."
python3 backend.py &
BACKEND_PID=$!
echo "Backend started with PID: $BACKEND_PID"

# Wait a moment for backend to start
sleep 3

# Start middleware in background
echo "Starting TGM-Adapter Middleware..."
python3 middleware.py &
MIDDLEWARE_PID=$!
echo "Middleware started with PID: $MIDDLEWARE_PID"

# Wait a moment for middleware to start
sleep 3

# Start frontend in background
echo "Starting Frontend..."
python3 frontend.py &
FRONTEND_PID=$!
echo "Frontend started with PID: $FRONTEND_PID"

echo ""
echo "=== All components started! ==="
echo "URLs:"
echo "  Frontend:   http://localhost:8080"
echo "  Middleware: http://localhost:5000"
echo "  Backend:    http://localhost:5001"
echo ""
echo "Process IDs:"
echo "  Backend:    $BACKEND_PID"
echo "  Middleware: $MIDDLEWARE_PID"
echo "  Frontend:   $FRONTEND_PID"
echo ""
echo "To stop all services, run: kill $BACKEND_PID $MIDDLEWARE_PID $FRONTEND_PID"
echo "Or press Ctrl+C to stop this script and all background processes."

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Stopping all services..."
    kill $BACKEND_PID $MIDDLEWARE_PID $FRONTEND_PID 2>/dev/null
    echo "All services stopped."
    exit 0
}

# Trap Ctrl+C and call cleanup
trap cleanup INT

# Wait for any process to exit
wait