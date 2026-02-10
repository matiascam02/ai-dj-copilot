#!/bin/bash
# Start AI DJ Co-Pilot Web Server

echo "🎧 AI DJ Co-Pilot - Starting Web Server"
echo "========================================"
echo ""

# Check if in project root
if [ ! -f "quick_test.py" ]; then
    echo "Error: Must run from project root"
    echo "cd ~/Documents/ai-dj-copilot"
    exit 1
fi

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found"
    echo "Run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Activate venv
echo "Activating virtual environment..."
source venv/bin/activate

# Check if fastapi is installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "Installing FastAPI..."
    pip install fastapi uvicorn python-multipart
fi

echo ""
echo "Starting server on http://localhost:8000"
echo "Press Ctrl+C to stop"
echo ""

# Start server
python -m uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000
