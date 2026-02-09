# AI DJ Co-Pilot 🎧🤖

**AI-powered DJ assistant that handles technical mixing while you focus on creativity**

## Vision

Enable bedroom DJs to create professional-level sets by combining human creativity with AI automation:

- **You choose** the music and creative direction  
- **AI handles** beatmatching, transitions, effects, and technical execution  
- **Hybrid control** - override AI anytime with manual input

## Status

🚧 **MVP in Development** - Core analysis & queue management

## Quick Start

```bash
# Clone repo
git clone https://github.com/matiascam02/ai-dj-copilot
cd ai-dj-copilot

# Install dependencies
pip install -r requirements.txt

# Analyze a track
python backend/analyze_track.py path/to/song.mp3
```

## Core Features (Planned MVP)

### ✅ Track Analysis
- BPM & beat detection (Essentia)
- Key detection & harmonic mixing (Camelot wheel)
- Energy level & structure analysis
- Stem separation (Demucs)

### 🚧 Queue Management  
- Intelligent 3-4 track queue
- Optimal transition point detection
- Harmonic compatibility scoring

### 📋 Auto-Mixing Engine
- Beatmatching & tempo sync
- Smart EQ transitions
- Contextual effects (reverb, delay, filters)
- Drop/breakdown detection

### 🎛️ Manual Control
- Override AI transitions anytime
- Trigger effects on-demand
- Loop/cue point suggestions
- Real-time parameter control

## Tech Stack

- **Audio Analysis:** Essentia, Librosa, Madmom
- **Stem Separation:** Demucs (Meta)
- **AI/ML:** PyTorch, Transformers, Reinforcement Learning
- **Audio Engine:** PyAudio, Sounddevice, DDSP
- **Backend:** FastAPI, SQLite/PostgreSQL
- **Frontend:** React (planned)

## Documentation

See `/docs` for detailed research and architecture.

## License

MIT

---

**Created:** February 9, 2026  
**By:** Matias Cam + Hoyuelo (OpenClaw Agent)
