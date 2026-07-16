#!/bin/bash

# Load environment variables from .env file
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

echo "🚀 Starting AI ESP Loyalty Helper App with Pinecone..."
echo ""

cd backend
nohup python3 app.py > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
cd ..

echo "⏳ Waiting for backend to start..."
sleep 10

# Check if backend is running
if ps -p $BACKEND_PID > /dev/null 2>&1; then
    echo "✅ Backend is running (PID: $BACKEND_PID)"
else
    echo "❌ Backend failed to start. Check /tmp/backend.log"
    cat /tmp/backend.log
    exit 1
fi

# Start frontend
echo "🎨 Starting frontend server on port 3001..."
cd frontend
nohup python3 -m http.server 3001 > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

sleep 2

echo ""
echo "✅ Both servers are running!"
echo ""
echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo ""
echo "📱 Access the app at: http://localhost:3001"
echo "🔧 Admin password: RICHCSM"
echo ""
echo "To stop the servers:"
echo "  kill $BACKEND_PID $FRONTEND_PID"
