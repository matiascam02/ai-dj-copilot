#!/bin/bash
# Start AI DJ Co-Pilot Live Interface

echo "🎧 AI DJ Co-Pilot - Live DJ Interface"
echo "========================================"
echo ""

# Check if in project root
if [ ! -f "quick_test.py" ]; then
    echo "Error: Must run from project root"
    echo "cd ~/Documents/ai-dj-copilot"
    exit 1
fi

# Install audio dependencies if needed
echo "Checking audio dependencies..."
pip install -q sounddevice soundfile websockets python-multipart

echo ""
echo "Starting live DJ interface..."
echo "🎛️ Open http://localhost:8000 in your browser"
echo ""
echo "Controls:"
echo "  - Load tracks into Deck A and B"
echo "  - Use Play/Pause buttons"
echo "  - Adjust crossfader to mix"
echo "  - EQ controls at bottom"
echo "  - Real-time suggestions in center"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Start server
python -m uvicorn backend.api.dj_interface:app --reload --host 0.0.0.0 --port 8000
