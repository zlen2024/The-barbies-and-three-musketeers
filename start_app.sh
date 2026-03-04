#!/bin/bash
export SECRET_KEY=dev-secret-key
python app.py > flask_output.log 2>&1 &
cd frontend
npm run dev > vite_output.log 2>&1 &
