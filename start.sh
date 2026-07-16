#!/bin/bash

# Start script for AI ESP Loyalty Helper App

echo "🚀 Starting AI ESP Loyalty Helper App..."
echo ""

# Check if GEMINI_API_KEY is set
if [ -z "$GEMINI_API_KEY" ]; then
    echo "⚠️  Warning: GEMINI_API_KEY is not set"
    echo "   Set it with: export GEMINI_API_KEY='your_key_here'"
    echo ""
fi

# Start backend
echo "📦 Starting backend server on port 5001..."
cd backend
python3 app.py &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 3

# Check if backend started successfully
if curl -s http://localhost:5001/api/admin/esps > /dev/null 2>&1; then
    echo "✅ Backend is running (PID: $BACKEND_PID)"
else
    echo "❌ Backend failed to start"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# Start frontend
echo "🎨 Starting frontend server on port 3001..."
cd frontend
python3 -m http.server 3001 &
FRONTEND_PID=$!
cd ..

sleep 2

echo ""
echo "✅ Both servers are running!"
echo ""
echo "📱 Access the app at: http://localhost:3001"
echo "🔧 Admin password: RICHCSM"
echo ""
echo "To stop the servers:"
echo "  kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "Or run: pkill -f 'python3 app.py' && pkill -f 'python3 -m http.server'"
