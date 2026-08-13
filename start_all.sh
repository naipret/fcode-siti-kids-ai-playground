#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 [SITI Gala Launcher] Starting F-Code SITI AI Playground..."

# Check Python virtualenv
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment (.venv)..."
    python3 -m venv .venv
fi

echo "🔄 Activating virtual environment..."
source .venv/bin/activate

echo "📌 Checking & installing python dependencies..."
pip install --quiet -r app/requirements.txt

# Create assets directories if missing
mkdir -p app/assets/audio/koon app/assets/audio/timnang app/assets/video

# Free ports 8000 and 8001 if currently in use by old processes
echo "🧹 Cleaning up existing processes on ports 8000 & 8001..."
if command -v fuser >/dev/null 2>&1; then
    fuser -k 8000/tcp 2>/dev/null || true
    fuser -k 8001/tcp 2>/dev/null || true
elif command -v lsof >/dev/null 2>&1; then
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    lsof -ti:8001 | xargs kill -9 2>/dev/null || true
fi
sleep 1

echo "🎮 Launching Game 1: Cùng Koon Đi Tìm Cầu Vồng (Port :8000)..."
python app/server.py &
PID_KOON=$!

echo "🎮 Launching Game 2: Tìm Nắng Cùng AI (Port :8001)..."
python app/timnang_master.py &
PID_TIMNANG=$!

# Function to clean up background processes on Ctrl+C / exit
cleanup() {
    echo ""
    echo "🛑 Shutting down servers..."
    kill $PID_KOON 2>/dev/null || true
    kill $PID_TIMNANG 2>/dev/null || true
    echo "👋 Stopped successfully."
    exit 0
}

trap cleanup INT TERM EXIT

echo "⏳ Waiting for healthchecks..."
sleep 3

curl -s http://localhost:8000/health > /dev/null && echo "  ✅ Game 1 (:8000) is ONLINE" || echo "  ⚠️ Game 1 starting..."
curl -s http://localhost:8001/health > /dev/null && echo "  ✅ Game 2 (:8001) is ONLINE" || echo "  ⚠️ Game 2 starting..."

echo ""
echo "✨ Both servers are running!"
echo "   - Master Game 1: http://localhost:8000"
echo "   - Master Game 2: http://localhost:8001"
echo "   - Stations:      http://<your-ip>:8001/station/A"
echo "Press Ctrl+C to stop both servers."

wait
