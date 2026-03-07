#!/bin/bash
# Start backend
source venv/bin/activate || true
python app.py > backend.log 2>&1 &
BACKEND_PID=$!

# Start frontend
cd frontend
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!

echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
