#!/bin/bash
# AI DJ Co-Pilot - Quick Setup Script

set -e  # Exit on error

echo "🎧 AI DJ Co-Pilot - Setup"
echo "=========================="
echo ""

# Check Python version
echo "→ Checking Python version..."
python3 --version || { echo "Error: Python 3 not found. Install Python 3.10+"; exit 1; }

# Create virtual environment
echo "→ Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo "→ Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "→ Upgrading pip..."
pip install --upgrade pip --quiet

# Install dependencies
echo "→ Installing dependencies (this may take 5-10 minutes)..."
echo "  - essentia-tensorflow (audio analysis)"
echo "  - librosa (feature extraction)"
echo "  - numpy, scipy (math)"
pip install essentia-tensorflow librosa numpy scipy --quiet

echo ""
echo "✓ Installation complete!"
echo ""

# Verify installation
echo "→ Verifying installation..."
python3 -c "import essentia; print('  ✓ Essentia OK')" || echo "  ✗ Essentia failed"
python3 -c "import librosa; print('  ✓ Librosa OK')" || echo "  ✗ Librosa failed"
python3 -c "import numpy; print('  ✓ NumPy OK')" || echo "  ✗ NumPy failed"

echo ""
echo "=========================="
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Download some test music (see GETTING_STARTED.md)"
echo "  2. Run: source venv/bin/activate"
echo "  3. Run: python backend/audio_analysis/track_analyzer.py path/to/song.mp3"
echo ""
echo "For detailed instructions: cat GETTING_STARTED.md"
echo ""
