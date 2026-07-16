#!/bin/bash

# AI ESP Loyalty Helper - Local Startup Script
# Run this directly on your Mac (not in VM)

echo "🚀 Starting AI ESP Loyalty Helper App (Local Mode)..."
echo ""

# Navigate to script directory
cd "$(dirname "$0")"

# Check if ChromaDB exists and is accessible
if [ -d "backend/chroma_db" ] && [ -f "backend/chroma_db/chroma.sqlite3" ]; then
    echo "✅ Found existing ChromaDB"
else
    echo "⚠️  ChromaDB not found or needs initialization"
    echo "   The app will create it automatically on first run"
fi

# Set environment variables from .env file
export GEMINI_API_KEY="AQ.Ab8RN6LArZu3L8DrOLafh5uy8VhrC1OzdjkKwYQp60LMpU9kUw"
export VECTOR_DB_PROVIDER=chromadb
export FLASK_ENV=development
export FLASK_DEBUG=0
export PORT=5001

# Start backend
echo "📦 Starting backend server..."
cd backend
python3 app.py &
BACKEND_PID=$!
cd ..

echo "⏳ Waiting for backend to initialize (~10 seconds)..."
sleep 10

# Check if backend is running
if ps -p $BACKEND_PID > /dev/null; then
    echo "✅ Backend is running (PID: $BACKEND_PID)"
else
    echo "❌ Backend failed to start"
    echo "Check the error messages above"
    exit 1
fi

# Start frontend
echo "🎨 Starting frontend server..."
cd frontend
python3 -m http.server 3001 &
FRONTEND_PID=$!
cd ..

sleep 2

echo ""
echo "✅ Application is running!"
echo ""
echo "📱 Open in browser: http://localhost:3001"
echo "🔧 Backend API: http://localhost:5001"
echo "🔑 Admin password: RICHCSM"
echo ""
echo "To stop, press Ctrl+C or run:"
echo "  kill $BACKEND_PID $FRONTEND_PID"
echo ""

# Keep script running and wait for Ctrl+C
trap "echo ''; echo '🛑 Stopping servers...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM

# Wait for processes
wait
