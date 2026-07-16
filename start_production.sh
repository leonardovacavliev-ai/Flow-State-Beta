#!/bin/bash
export GEMINI_API_KEY="AQ.Ab8RN6LArZu3L8DrOLafh5uy8VhrC1OzdjkKwYQp60LMpU9kUw"
export VECTOR_DB_PROVIDER=pinecone
export PINECONE_API_KEY="pcsk_2aKY6Q_KMnu4YGdpctHN78PQ4KuC4bZcYQR9ztVkoGrYqNLBa1r6wFgpLp6JESsiEg2jwU"
export PINECONE_INDEX_NAME="esp-loyalty-docs1"
export FLASK_ENV=production
export FLASK_DEBUG=0

echo "🚀 Starting AI ESP Loyalty Helper App (Production Mode)..."
echo ""

cd backend
nohup python3 app.py > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
cd ..

echo "⏳ Waiting for backend to start..."
sleep 8

# Check if backend is running
if ps -p $BACKEND_PID > /dev/null 2>&1; then
    echo "✅ Backend is running (PID: $BACKEND_PID)"
    
    # Test the backend
    if curl -s http://localhost:5001/api/admin/esps > /dev/null 2>&1; then
        echo "✅ Backend API is responding"
    else
        echo "⚠️  Backend started but API not responding yet..."
    fi
else
    echo "❌ Backend failed to start. Check /tmp/backend.log"
    tail -30 /tmp/backend.log
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
echo "Backend PID: $BACKEND_PID (port 5001)"
echo "Frontend PID: $FRONTEND_PID (port 3001)"
echo ""
echo "📱 Frontend: http://localhost:3001"
echo "🔧 Backend API: http://localhost:5001"
echo "🔑 Admin password: RICHCSM"
echo ""
echo "To view logs:"
echo "  tail -f /tmp/backend.log"
echo "  tail -f /tmp/frontend.log"
echo ""
echo "To stop the servers:"
echo "  kill $BACKEND_PID $FRONTEND_PID"
