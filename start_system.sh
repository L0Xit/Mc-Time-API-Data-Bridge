#!/bin/bash
#
# TGM-Adapter System Startup Script
# Starts all components of the TGM-Adapter system.
#

echo "Starting TGM-Adapter System..."
echo "================================"

# Function to handle cleanup on script exit
cleanup() {
    echo ""
    echo "Shutting down TGM-Adapter System..."
    echo "Stopping all components..."
    kill $BACKEND_PID $MIDDLEWARE_PID $FRONTEND_PID 2>/dev/null
    wait
    echo "System shutdown complete."
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start Backend
echo "Starting Backend..."
python3 backend/backend.py &
BACKEND_PID=$!
echo "Backend started with PID: $BACKEND_PID"

# Start Middleware  
echo "Starting Middleware..."
python3 middleware/middleware.py &
MIDDLEWARE_PID=$!
echo "Middleware started with PID: $MIDDLEWARE_PID"

# Start Frontend
echo "Starting Frontend..."
python3 frontend/frontend.py &
FRONTEND_PID=$!
echo "Frontend started with PID: $FRONTEND_PID"

echo ""
echo "All components started successfully!"
echo "Backend PID: $BACKEND_PID"
echo "Middleware PID: $MIDDLEWARE_PID" 
echo "Frontend PID: $FRONTEND_PID"
echo ""
echo "Press Ctrl+C to stop all components..."

# Wait for all background processes
wait