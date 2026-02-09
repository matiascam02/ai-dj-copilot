---
title: AI DJ Co-Pilot - Getting Started Guide
type: guide
project: ai-dj-copilot
created: 2026-02-09
---

# Getting Started - Software MVP

**Focus: Build software first. Hardware only if this makes sense.**

---

## Phase 0: Get Music for Testing

You need tracks to test the analyzer. Here's how to get high-quality, **legal**, **free** music.

### Option 1: Free Music Archives (Best for Testing)

#### A. Free Music Archive (FMA)
**URL:** https://freemusicarchive.org/

**What it is:**
- 100,000+ tracks, all legal
- Multiple genres (electronic, house, techno, hip-hop)
- Creative Commons licenses (free to use)

**How to download:**
```bash
# Install spotdl (Python tool)
pip install spotdl

# Or just download from website:
# 1. Go to https://freemusicarchive.org/
# 2. Search for genre: "Electronic" or "House"
# 3. Download individual tracks (MP3)
```

**Recommended for DJ testing:**
- Search: "techno" (high BPM, clear beats)
- Search: "house" (4/4 time, perfect for testing)
- Download 10-20 tracks

---

#### B. Jamendo Music
**URL:** https://www.jamendo.com/

**What it is:**
- 500,000+ tracks
- All Creative Commons
- Organized by genre

**How to use:**
```
1. Go to Jamendo.com
2. Browse → Electronic → House/Techno
3. Download MP3 (free account needed)
```

---

#### C. ccMixter
**URL:** http://ccmixter.org/

**What it is:**
- Remix-friendly music
- Stems available (vocals, drums separate)
- Perfect for testing stem separation

**Good for:**
- Testing Demucs (stem separation)
- Mashup experiments

---

#### D. Internet Archive (Archive.org)
**URL:** https://archive.org/details/audio

**What it is:**
- MASSIVE collection
- Live sets, mixtapes, original tracks
- All public domain or CC-licensed

**Search:**
```
site:archive.org "DJ mix" filetype:mp3
site:archive.org "techno" filetype:flac
```

---

### Option 2: Sample Packs (Professional Quality)

#### Splice Free Sounds
**URL:** https://splice.com/sounds/free

**What you get:**
- Professional loops (drums, bass, melody)
- High-quality stems
- Great for testing beat detection

**Note:** Not full tracks, but useful for development

---

#### Looperman
**URL:** https://www.looperman.com/

**What you get:**
- User-uploaded loops
- Many genres
- Free to download

---

### Option 3: YouTube (For Personal Testing ONLY)

**Use yt-dlp to download mixes:**
```bash
# Install yt-dlp
pip install yt-dlp

# Download DJ mix (audio only, best quality)
yt-dlp -x --audio-format mp3 --audio-quality 0 "https://youtube.com/watch?v=VIDEO_ID"

# Example: Download a Boiler Room set
yt-dlp -x --audio-format mp3 --audio-quality 0 "https://youtube.com/watch?v=boilerroom_set"
```

**⚠️ Legal note:**
- Only for personal testing
- Do NOT distribute
- Do NOT use in production/demos

---

### Option 4: Create Your Own Test Tracks

**If you want specific BPMs/keys for testing:**

```bash
# Use sonic-pi or similar to generate test tracks
# Example: 128 BPM, A minor, 2 minutes

# Or use online generators:
# - https://www.beatsperminuteonline.com/
# - Generate simple 4/4 beats at different BPMs
```

---

## Recommended Starter Library

**Download these for comprehensive testing:**

| Genre | Tracks | BPM Range | Purpose |
|-------|--------|-----------|---------|
| House | 5 tracks | 120-128 | Standard DJ testing |
| Techno | 5 tracks | 128-140 | High BPM testing |
| Hip-Hop | 3 tracks | 80-100 | Low BPM, complex beats |
| Drum & Bass | 2 tracks | 160-180 | Extreme BPM testing |
| Ambient | 2 tracks | 60-90 | Low energy testing |

**Total: ~20 tracks = enough to test everything**

---

## Phase 1: Test What We Have

### Step 1: Setup Development Environment

```bash
# 1. Clone the repo (if not done)
cd ~/Documents
git clone https://github.com/matiascam02/ai-dj-copilot
cd ai-dj-copilot

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Mac/Linux
# venv\Scripts\activate   # On Windows

# 3. Install dependencies
pip install --upgrade pip
pip install essentia-tensorflow librosa numpy scipy

# 4. Verify installation
python -c "import essentia; print('Essentia OK')"
python -c "import librosa; print('Librosa OK')"
```

---

### Step 2: Download Test Music

```bash
# Create directory for test tracks
mkdir -p data/tracks/test

# Option 1: Use FMA (recommended)
# Go to https://freemusicarchive.org/
# Search "house" or "techno"
# Download 5-10 tracks to data/tracks/test/

# Option 2: Use yt-dlp for quick testing
cd data/tracks/test
yt-dlp -x --audio-format mp3 --audio-quality 0 "https://youtube.com/watch?v=HOUSE_MIX_ID"
```

---

### Step 3: Run the Track Analyzer

```bash
# Analyze a single track
python backend/audio_analysis/track_analyzer.py data/tracks/test/song.mp3

# Expected output:
# Analyzing: data/tracks/test/song.mp3
#   → Extracting rhythm...
#   → Detecting key...
#   → Measuring loudness...
#   → Estimating energy...
# ✓ Analysis complete!
# 
# ==================================================
# ANALYSIS SUMMARY
# ==================================================
# Track: song.mp3
# Duration: 245.3s
# BPM: 128.4
# Key: A minor (1A)
# Loudness: -8.45 LUFS
# Energy: 0.756
# ==================================================
# ✓ Saved analysis to: song_analysis.json
```

**What to check:**
- ✅ BPM accurate? (compare to known BPM or tap along)
- ✅ Key correct? (if you know the track)
- ✅ Analysis completes without errors

---

### Step 4: Batch Analyze Your Library

```bash
# Create a batch analysis script
cat > analyze_library.py << 'EOF'
import os
import json
from pathlib import Path
from backend.audio_analysis.track_analyzer import TrackAnalyzer

def analyze_library(music_dir, output_dir):
    """Analyze all tracks in a directory"""
    analyzer = TrackAnalyzer()
    
    # Find all audio files
    audio_files = []
    for ext in ['*.mp3', '*.wav', '*.flac', '*.m4a']:
        audio_files.extend(Path(music_dir).glob(ext))
    
    print(f"Found {len(audio_files)} tracks to analyze\n")
    
    results = []
    for i, audio_path in enumerate(audio_files, 1):
        print(f"[{i}/{len(audio_files)}] {audio_path.name}")
        try:
            result = analyzer.analyze(str(audio_path))
            results.append(result)
            
            # Save individual analysis
            output_file = Path(output_dir) / f"{audio_path.stem}_analysis.json"
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
                
        except Exception as e:
            print(f"  ERROR: {e}")
            continue
    
    # Save summary
    summary = {
        'total_tracks': len(results),
        'tracks': results
    }
    
    summary_file = Path(output_dir) / 'library_analysis.json'
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n✓ Analyzed {len(results)} tracks")
    print(f"✓ Summary saved to: {summary_file}")

if __name__ == "__main__":
    analyze_library("data/tracks/test", "data/cache")
EOF

# Run batch analysis
python analyze_library.py
```

---

### Step 5: Explore the Results

```bash
# View the summary
cat data/cache/library_analysis.json | jq '.tracks[] | {file: .file_path, bpm: .bpm, key: .key, camelot: .camelot}'

# Example output:
# {
#   "file": "data/tracks/test/track1.mp3",
#   "bpm": 128.4,
#   "key": "A",
#   "camelot": "1A"
# }
# {
#   "file": "data/tracks/test/track2.mp3",
#   "bpm": 126.8,
#   "key": "E",
#   "camelot": "2A"
# }
```

**What to look for:**
- BPM distribution (are they clustered or varied?)
- Key distribution (Camelot wheel coverage)
- Any analysis failures (tracks that errored out)

---

## Phase 2: Build the Next Features

### Week 1-2: Queue Manager

**Goal:** Smart track queue that scores compatibility

**What to build:**

```python
# backend/queue_manager/queue.py

class QueueManager:
    def __init__(self):
        self.queue = []  # List of track IDs
        self.current_track = None
        
    def add_track(self, track_analysis):
        """Add track to queue"""
        self.queue.append(track_analysis)
        
    def get_next_track(self):
        """Get next track with compatibility score"""
        if not self.current_track or not self.queue:
            return self.queue[0] if self.queue else None
        
        # Score all tracks in queue
        scored = []
        for track in self.queue:
            score = self._score_compatibility(
                self.current_track, 
                track
            )
            scored.append((track, score))
        
        # Sort by score (best first)
        scored.sort(key=lambda x: x[1], reverse=True)
        
        return scored[0] if scored else None
    
    def _score_compatibility(self, track_a, track_b):
        """Score how well two tracks mix together"""
        score = 1.0
        
        # BPM compatibility (±6 BPM = perfect)
        bpm_diff = abs(track_a['bpm'] - track_b['bpm'])
        if bpm_diff <= 6:
            bpm_score = 1.0
        else:
            bpm_score = max(0, 1 - (bpm_diff - 6) / 20)
        
        # Key compatibility (Camelot wheel)
        key_score = self._camelot_compatibility(
            track_a['camelot'], 
            track_b['camelot']
        )
        
        # Energy compatibility
        energy_diff = abs(
            track_a.get('energy', 0.5) - 
            track_b.get('energy', 0.5)
        )
        energy_score = max(0, 1 - energy_diff)
        
        # Weighted average
        score = (
            0.4 * bpm_score +
            0.3 * key_score +
            0.3 * energy_score
        )
        
        return score
    
    def _camelot_compatibility(self, camelot_a, camelot_b):
        """Check Camelot wheel compatibility"""
        if camelot_a == camelot_b:
            return 1.0  # Same key
        
        # Extract number and letter
        num_a = int(camelot_a[:-1])
        letter_a = camelot_a[-1]
        num_b = int(camelot_b[:-1])
        letter_b = camelot_b[-1]
        
        # Check compatibility rules
        if num_a == num_b and letter_a != letter_b:
            return 1.0  # Relative major/minor
        if abs(num_a - num_b) == 1 and letter_a == letter_b:
            return 0.8  # Adjacent keys
        
        return 0.5  # Not compatible, but not terrible
```

**Test it:**
```python
# test_queue.py
from backend.queue_manager.queue import QueueManager
import json

# Load your analyzed tracks
with open('data/cache/library_analysis.json') as f:
    library = json.load(f)

qm = QueueManager()

# Add all tracks to queue
for track in library['tracks']:
    qm.add_track(track)

# Set current track
qm.current_track = library['tracks'][0]

# Get best next track
next_track, score = qm.get_next_track()

print(f"Current: {qm.current_track['file_path']}")
print(f"  BPM: {qm.current_track['bpm']}, Key: {qm.current_track['camelot']}")
print(f"\nBest next: {next_track['file_path']}")
print(f"  BPM: {next_track['bpm']}, Key: {next_track['camelot']}")
print(f"  Compatibility: {score:.2%}")
```

---

### Week 3-4: Transition Planner

**Goal:** Identify optimal transition points between tracks

```python
# backend/queue_manager/transition_planner.py

class TransitionPlanner:
    def plan_transition(self, track_a, track_b):
        """Plan a transition between two tracks"""
        
        # Find best cue point in track A (where to start transition)
        # Usually: 16 or 32 bars before the end
        track_a_duration = track_a['duration']
        track_a_bpm = track_a['bpm']
        
        # Calculate bar length
        bar_length = (60 / track_a_bpm) * 4  # 4 beats per bar
        
        # Start transition 32 bars from end
        transition_start = track_a_duration - (32 * bar_length)
        
        # Find best cue point in track B (where to start playing)
        # Usually: intro or first drop
        track_b_beats = track_b['beats']
        
        # Use 16th beat as cue (typical intro length)
        if len(track_b_beats) > 16:
            track_b_cue = track_b_beats[16]
        else:
            track_b_cue = 0
        
        # Transition duration (16 bars = standard)
        transition_duration = 16 * bar_length
        
        return {
            'track_a_transition_start': transition_start,
            'track_b_cue_point': track_b_cue,
            'duration': transition_duration,
            'duration_bars': 16,
            'timeline': self._generate_timeline(
                transition_duration, 
                track_a_bpm
            )
        }
    
    def _generate_timeline(self, duration, bpm):
        """Generate automation timeline for transition"""
        bar_length = (60 / bpm) * 4
        
        return {
            'beat_0': {'action': 'start_deck_b'},
            'beat_8': {'action': 'eq_low_cut_deck_a'},
            'beat_12': {'action': 'eq_low_introduce_deck_b'},
            'beat_32': {'action': 'crossfader_50_50'},
            'beat_48': {'action': 'fade_out_deck_a'},
            'beat_64': {'action': 'deck_b_only'},
        }
```

---

### Week 5-6: Simple Web UI

**Goal:** Visual interface to see what the AI is doing

**Tech:** FastAPI (backend) + basic HTML/JS (frontend)

```bash
# Install FastAPI
pip install fastapi uvicorn jinja2

# Create API
mkdir -p backend/api
```

```python
# backend/api/main.py

from fastapi import FastAPI, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import json

app = FastAPI()

# In-memory storage (replace with DB later)
library = []
queue_manager = None

@app.get("/")
async def index():
    return HTMLResponse("""
    <html>
    <head><title>AI DJ Co-Pilot</title></head>
    <body>
        <h1>AI DJ Co-Pilot</h1>
        <h2>Upload Track</h2>
        <form action="/upload" method="post" enctype="multipart/form-data">
            <input type="file" name="file" accept="audio/*">
            <button type="submit">Analyze</button>
        </form>
        <h2>Library</h2>
        <div id="library">Loading...</div>
        <script>
            fetch('/library')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('library').innerHTML = 
                        data.map(t => `
                            <div>
                                <b>${t.file_path}</b><br>
                                BPM: ${t.bpm.toFixed(1)} | 
                                Key: ${t.key} ${t.scale} (${t.camelot})
                            </div>
                        `).join('<hr>');
                });
        </script>
    </body>
    </html>
    """)

@app.post("/upload")
async def upload(file: UploadFile):
    # Save file
    content = await file.read()
    file_path = f"data/tracks/{file.filename}"
    with open(file_path, 'wb') as f:
        f.write(content)
    
    # Analyze
    from backend.audio_analysis.track_analyzer import TrackAnalyzer
    analyzer = TrackAnalyzer()
    result = analyzer.analyze(file_path)
    
    library.append(result)
    
    return {"status": "ok", "analysis": result}

@app.get("/library")
async def get_library():
    return library

@app.get("/queue/next")
async def get_next():
    # Use queue manager to suggest next track
    if not queue_manager or not library:
        return {"error": "No tracks in library"}
    
    next_track, score = queue_manager.get_next_track()
    return {
        "next_track": next_track,
        "compatibility_score": score
    }

# Run with: uvicorn backend.api.main:app --reload
```

---

## Testing Checklist

### Core Analysis
- [ ] BPM detection accurate (±1 BPM)
- [ ] Key detection works (test with known keys)
- [ ] Beat positions aligned (visual check in Audacity)
- [ ] Energy estimation reasonable (high for energetic, low for ambient)

### Queue Manager
- [ ] Compatibility scoring makes sense (similar BPM = high score)
- [ ] Camelot wheel logic works (1A → 2A = compatible)
- [ ] Best track suggestion is reasonable

### Transition Planner
- [ ] Transition points are musically sensible
- [ ] Timeline makes sense (not too fast/slow)

---

## Next Steps After MVP

1. **Stem Separation** (Demucs)
   - Pre-process tracks to separate vocals/drums/bass
   - Enable stem-based mixing

2. **Real-Time Audio Engine**
   - Implement actual playback
   - Beatmatching algorithm
   - EQ automation

3. **Machine Learning**
   - Train on your own mixes
   - Learn your style

4. **Better UI**
   - React frontend
   - Waveform visualization
   - Drag-and-drop queue

---

## Success Metrics

**Week 1:** Analyze 20 tracks, all complete without errors  
**Week 2:** Queue manager suggests reasonable next tracks  
**Week 3:** Transition planner generates sensible plans  
**Week 4:** Web UI working, can upload and analyze tracks  

**After 1 month:** You should have a working prototype that:
- Analyzes your music library
- Suggests next tracks based on compatibility
- Plans transitions with automation timelines
- Has a basic web interface

**Then decide:** Is this useful? Does it make sense? → Hardware or pivot

---

**Let's build it!** 🦞🎧

---

**Created:** February 9, 2026  
**Status:** Ready to start
