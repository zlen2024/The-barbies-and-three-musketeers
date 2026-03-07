#!/bin/bash
# Start backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python seed_data.py
python app.py &
BACKEND_PID=$!

# Start frontend
cd frontend
npm install
npm run dev &
FRONTEND_PID=$!

echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"

wait
