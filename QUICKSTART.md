# Quick Start Guide - Get Running in 5 Minutes

## Step 1: Setup (2 minutes)

```bash
cd ~/Documents/ai-dj-copilot
bash setup.sh
```

This will:
- Create virtual environment
- Install all dependencies (Essentia, Librosa, etc.)
- Verify everything works

## Step 2: Get Test Music (1 minute)

**Option A: Manual Download (Recommended)**
1. Go to https://freemusicarchive.org/search?quicksearch=house
2. Download 3-5 house/techno tracks
3. Save them to `data/tracks/test/`

**Option B: Automated (May fail)**
```bash
bash download_test_music.sh
```

## Step 3: Test It! (2 minutes)

```bash
# Activate virtual environment
source venv/bin/activate

# Run quick test
python quick_test.py
```

Expected output:
```
🎧 AI DJ Co-Pilot - Quick Test
==================================================

Found 5 track(s) to analyze

[1/5] house_track.mp3
--------------------------------------------------
  BPM: 128.4
  Key: A minor (1A)
  Duration: 245.3s
  Energy: 0.756

[2/5] techno_track.mp3
--------------------------------------------------
  BPM: 140.2
  Key: E minor (2A)
  Duration: 312.1s
  Energy: 0.824

...

✓ Analyzed 5/5 tracks successfully
✓ Results saved to: data/cache/quick_test_results.json

Compatibility Matrix:
--------------------------------------------------
  house_track      ↔ techno_track       | ΔBPM: 11.8 | 🟡 Good
  house_track      ↔ ambient_track      | ΔBPM: 38.2 | 🔴 Difficult
  techno_track     ↔ dnb_track          | ΔBPM: 32.4 | 🔴 Difficult
```

## Step 4: Analyze Your Own Music

```bash
# Single track
python backend/audio_analysis/track_analyzer.py path/to/your/song.mp3

# See results
cat song_analysis.json
```

## What's Next?

✅ **Software works!** Now you can:

1. **Read the docs:**
   - `GETTING_STARTED.md` - Detailed guide
   - `docs/02_Technical_Research.md` - How it works

2. **Build queue manager** (Week 2)
   - Smart track selection
   - Compatibility scoring

3. **Add transition planner** (Week 3-4)
   - Optimal cue points
   - Automation timeline

4. **Create web UI** (Week 5-6)
   - Visual interface
   - Upload tracks
   - See suggestions

---

**Questions?** Check `GETTING_STARTED.md` or the docs folder.

**Working?** Start building the queue manager! 🚀
