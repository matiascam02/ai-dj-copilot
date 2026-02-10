#!/bin/bash
# Start AI DJ Co-Pilot - Complete Interface

echo "🎧 AI DJ Co-Pilot"
echo "================="
echo ""

# Check if in project root
if [ ! -f "quick_test.py" ]; then
    echo "❌ Error: Must run from project root"
    echo "Run: cd ~/Documents/ai-dj-copilot"
    exit 1
fi

# Install dependencies if needed
echo "📦 Checking dependencies..."
pip3 install --break-system-packages sounddevice soundfile scipy websockets python-multipart 2>&1 | grep -E "(Successfully|already)" || echo "✓ Dependencies ready"

echo ""
echo "🚀 Starting complete interface..."
echo ""
echo "📚 Features:"
echo "  • Upload & analyze MP3 files"
echo "  • Browse your library"
echo "  • Load tracks into decks"
echo "  • Live DJ with real-time suggestions"
echo ""
echo "🌐 Open: http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Start server
python -m uvicorn backend.api.complete_interface:app --reload --host 0.0.0.0 --port 8000
