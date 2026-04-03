#!/bin/bash
# ================================================
# ApplyGenius — Start Script
# Runs backend API server + opens frontend
# ================================================

echo ""
echo "🚀 Starting ApplyGenius..."
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run setup.sh first."
    exit 1
fi

# Activate venv
source venv/bin/activate

# Check .env
if [ ! -f "backend/.env" ]; then
    echo "❌ backend/.env not found. Run setup.sh first."
    exit 1
fi

# Start backend in background
echo "🔧 Starting Flask backend on http://localhost:5000 ..."
cd backend
python app.py &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 2

# Open frontend
echo "🌐 Opening frontend..."
if command -v python3 &> /dev/null; then
    # Start simple HTTP server for frontend
    cd frontend
    python3 -m http.server 3000 &
    FRONTEND_PID=$!
    cd ..
    
    # Try to open browser
    if command -v xdg-open &> /dev/null; then
        xdg-open http://localhost:3000
    elif command -v open &> /dev/null; then
        open http://localhost:3000
    fi
fi

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║  ✅ ApplyGenius is running!              ║"
echo "║                                          ║"
echo "║  Frontend: http://localhost:3000         ║"
echo "║  Backend:  http://localhost:5000         ║"
echo "║                                          ║"
echo "║  Press Ctrl+C to stop                   ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# Wait for Ctrl+C
trap "echo ''; echo '🛑 Stopping...'; kill $BACKEND_PID 2>/dev/null; kill $FRONTEND_PID 2>/dev/null; exit 0" INT

wait
