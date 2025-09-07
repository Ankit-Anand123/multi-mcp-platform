#!/bin/bash

echo "Starting Multi-MCP Platform..."

# Check if setup was run
if [ ! -f backend/.env ]; then
    echo "Error: Configuration not found. Please run setup.sh first."
    exit 1
fi

if [ ! -d backend/venv ]; then
    echo "Error: Python environment not found. Please run setup.sh first."
    exit 1
fi

if [ ! -d frontend/node_modules ]; then
    echo "Error: Node modules not found. Please run setup.sh first."
    exit 1
fi

# Function to cleanup background processes
cleanup() {
    echo ""
    echo "Stopping servers..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
    fi
    exit
}

# Set trap to cleanup on exit
trap cleanup EXIT INT TERM

# Check if ports are already in use
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "Error: Port 8000 is already in use. Please stop the service using that port."
    exit 1
fi

if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "Error: Port 3000 is already in use. Please stop the service using that port."
    exit 1
fi

# Start backend in background
echo "Starting backend server..."
cd backend

# Activate virtual environment
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Start backend with output redirection
python -m uvicorn mcp_orchestrator:app --host 0.0.0.0 --port 8000 --reload > ../backend.log 2>&1 &
BACKEND_PID=$!

cd ..

# Wait a moment for backend to start
echo "Waiting for backend to initialize..."
sleep 5

# Check if backend started successfully
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "Error: Backend failed to start. Check backend.log for details."
    exit 1
fi

# Test backend health
for i in {1..10}; do
    if curl -s http://localhost:8000/api/health >/dev/null 2>&1; then
        echo "Backend is ready!"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "Error: Backend health check failed. Check backend.log for details."
        exit 1
    fi
    echo "Waiting for backend... ($i/10)"
    sleep 2
done

# Start frontend in background
echo "Starting frontend server..."
cd frontend

# Start frontend with output redirection
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!

cd ..

# Wait a moment for frontend to start
echo "Waiting for frontend to initialize..."
sleep 5

# Check if frontend started successfully
if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    echo "Error: Frontend failed to start. Check frontend.log for details."
    exit 1
fi

echo ""
echo "=================================="
echo "Multi-MCP Platform Started!"
echo "=================================="
echo ""
echo "Access URLs:"
echo "  Frontend:  http://localhost:3000"
echo "  Backend:   http://localhost:8000"
echo "  API Docs:  http://localhost:8000/docs"
echo ""
echo "Logs:"
echo "  Backend:   tail -f backend.log"
echo "  Frontend:  tail -f frontend.log"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Wait for either process to exit
wait $BACKEND_PID $FRONTEND_PID