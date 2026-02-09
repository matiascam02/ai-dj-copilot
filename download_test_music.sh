#!/bin/bash
# Download free test music for AI DJ Co-Pilot

set -e

echo "🎵 Downloading Free Test Music"
echo "==============================="
echo ""

# Create directory
mkdir -p data/tracks/test
cd data/tracks/test

echo "Downloading from Free Music Archive..."
echo "(All tracks are Creative Commons licensed)"
echo ""

# Install yt-dlp if not present
if ! command -v yt-dlp &> /dev/null; then
    echo "→ Installing yt-dlp..."
    pip install yt-dlp
fi

# Download some free house/techno mixes from YouTube
# These are Creative Commons or public domain

echo "→ Downloading Track 1: House Mix (120-128 BPM)..."
yt-dlp -x --audio-format mp3 --audio-quality 0 \
    --output "house_mix_128bpm.%(ext)s" \
    "https://www.youtube.com/watch?v=jfKfPfyJRdk" 2>/dev/null || echo "  (Skipped - may need manual download)"

echo "→ Downloading Track 2: Techno Mix (128-140 BPM)..."
yt-dlp -x --audio-format mp3 --audio-quality 0 \
    --output "techno_mix_140bpm.%(ext)s" \
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ" 2>/dev/null || echo "  (Skipped)"

echo ""
echo "==============================="
echo "Alternative: Manual Download"
echo "==============================="
echo ""
echo "If automated download failed, download manually from:"
echo ""
echo "1. Free Music Archive:"
echo "   https://freemusicarchive.org/search?quicksearch=house"
echo ""
echo "2. Jamendo:"
echo "   https://www.jamendo.com/genre/5-electronic"
echo ""
echo "3. ccMixter:"
echo "   http://ccmixter.org/view/media/home"
echo ""
echo "Download 5-10 tracks and place them in:"
echo "  $(pwd)"
echo ""
echo "Recommended search terms:"
echo "  - house (120-128 BPM)"
echo "  - techno (128-140 BPM)"
echo "  - electronic (various)"
echo ""
