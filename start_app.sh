#!/bin/bash

# AI ESP Loyalty Helper - Startup Script
# This script starts both the backend and frontend servers

echo "🚀 Starting AI ESP Loyalty Helper App..."
echo ""

# Set environment variables
export GEMINI_API_KEY="AQ.Ab8RN6LArZu3L8DrOLafh5uy8VhrC1OzdjkKwYQp60LMpU9kUw"
export VECTOR_DB_PROVIDER=chromadb
export FLASK_ENV=production
export FLASK_DEBUG=0
export PORT=5001

# Navigate to backend directory
cd "$(dirname "$0")/backend"

# Start backend server
echo "📦 Starting backend server on port 5001..."
python3 app.py > ../logs/backend.log 2>&1 &
BACKEND_PID=$!

# Wait for backend to initialize
echo "⏳ Waiting for backend to initialize (this takes ~10-15 seconds)..."
sleep 15

# Check if backend is responding
if curl -s http://localhost:5001/api/admin/esps > /dev/null 2>&1; then
    echo "✅ Backend is running and responding (PID: $BACKEND_PID)"
else
    echo "❌ Backend failed to start. Check logs/backend.log for errors."
    cat ../logs/backend.log | tail -20
    exit 1
fi

# Start frontend server
cd ../frontend
echo "🎨 Starting frontend server on port 3001..."
python3 -m http.server 3001 > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!

sleep 2

echo ""
echo "✅ Application is running!"
echo ""
echo "📱 Frontend: http://localhost:3001"
echo "🔧 Backend API: http://localhost:5001  "
echo "🔑 Admin password: RICHCSM"
echo ""
echo "Server PIDs:"
echo "  Backend: $BACKEND_PID"
echo "  Frontend: $FRONTEND_PID"
echo ""
echo "To view logs:"
echo "  tail -f logs/backend.log"
echo "  tail -f logs/frontend.log"
echo ""
echo "To stop servers:"
echo "  kill $BACKEND_PID $FRONTEND_PID"
echo "  or press Ctrl+C in this terminal"
echo ""

# Wait for user to stop
wait
