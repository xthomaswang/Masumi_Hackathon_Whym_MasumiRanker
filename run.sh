#!/bin/bash
cd "$(dirname "$0")/code" || exit 1
export PYTHONPATH="$(pwd)"

echo "🚀 Starting FastAPI backend..."
uvicorn backend.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

sleep 3

cd ..

LOCAL_IP=$(ipconfig getifaddr en0)
echo "📡 Local access: http://$LOCAL_IP:8000/docs"

echo "🌐 Starting ngrok tunnel on port 8000..."
ngrok http 8000

kill $BACKEND_PID 2>/dev/null || true
