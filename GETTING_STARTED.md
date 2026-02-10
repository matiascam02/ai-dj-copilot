# Getting Started - AI DJ Co-Pilot

**Complete flow from zero to DJing in 5 minutes!**

---

## 🚀 Quick Start

```bash
cd ~/Documents/ai-dj-copilot

# Start the interface
./start.sh

# Open browser
open http://localhost:8000
```

---

## 📚 Step 1: Build Your Library

### Upload Tracks

1. Go to **"📚 Library"** tab (default)
2. Drag & drop MP3 files into the upload area
   - Or click to browse
3. Click **"🔍 Analyze X Track(s)"**

**What happens:**
- Files are uploaded to `data/tracks/uploads/`
- Each track is analyzed for:
  - BPM (beats per minute)
  - Key (musical key)
  - Energy level (0-1)
  - Duration
- Results saved to library

**Analysis takes:** ~10-30 seconds per track

### Browse Library

- See all tracks in a grid
- Each card shows:
  - Track title
  - BPM
  - Key
  - Duration
  - Energy level

---

## 🎛️ Step 2: Load Tracks

### Select and Load

1. **Click a track** in the library
   - Card turns blue (selected)
2. **Click "Load to Deck A"** or **"Load to Deck B"**
   - Track loads into the deck
   - Automatically switches to DJ Mode

### Typical Setup

- **Deck A:** Current playing track
- **Deck B:** Next track (queued)

---

## 🎧 Step 3: DJ!

### Basic Controls

**Deck A/B:**
- ▶️ **Play** - Start playback
- ⏸ **Pause** - Pause (keeps position)
- ⏹ **Stop** - Stop and reset

**Crossfader:**
- Full left = Deck A only
- Center = 50/50 mix
- Full right = Deck B only

### Follow the Suggestions

**Center panel shows real-time advice:**

```
🎵 Playing smoothly - 157s remaining
  [Green - all good]

📋 90s left - Choose next track
  [Yellow - prepare soon]

⚠️ Load Deck B NOW - 25s until transition!
  [Red - do this now!]

🎛️ CUT BASS Deck A
  Next: 4 bars
  [Red - in transition, follow timeline]
```

### Make Your First Mix

1. **Start Deck A** (your first track)
2. **Load Deck B** when prompted (~60s before end)
3. **Set crossfader to full left** (A only)
4. **Start Deck B** when suggested (it plays silently)
5. **Slowly move crossfader right** (mixing A → B)
6. **Done!** Deck B is now playing

---

## 🎯 Full Workflow Example

### Session Setup

```bash
# Terminal 1 - Start interface
cd ~/Documents/ai-dj-copilot
./start.sh

# Browser - http://localhost:8000
```

### First 5 Minutes

**Minute 1-2: Upload**
- Drag 5-10 MP3 files
- Click "Analyze"
- Wait for analysis

**Minute 3: Load**
- Click first track → "Load to Deck A"
- Click second track → "Load to Deck B"

**Minute 4-5: DJ!**
- Play Deck A
- Watch suggestions
- Mix to Deck B when prompted

---

## 💡 Tips

### Track Selection

**Good mixes need:**
- Similar BPM (±5 BPM)
- Compatible keys (shown in library)
- Smooth energy transitions

**The system suggests:**
- Next tracks from queue
- Best transition points
- EQ adjustments

### Suggestions

**Trust the suggestions!**
- They're based on audio analysis
- Timing is calculated from BPM
- Energy flow is optimized

**But you're in control:**
- Suggestions are advice, not commands
- You can freestyle anytime
- Manual EQ/effects always available

### Practice

**Start simple:**
1. Two similar tracks (same BPM)
2. Let Deck A play most of the way
3. Follow suggestions exactly
4. Move crossfader slowly

**Get fancy later:**
- EQ mixing (cut bass/highs)
- Loops and effects
- Faster transitions

---

## 🎨 Interface Guide

### Library Tab (📚)

**Top section:**
- Upload area (drag & drop)
- Analyze button

**Main area:**
- Grid of tracks
- Click to select
- Load buttons appear

### DJ Mode Tab (🎛️)

**Left:** Deck A
- Waveform (visual progress)
- Time displays
- Play/pause/stop buttons

**Center:** Suggestions + Crossfader
- Real-time advice
- Color-coded urgency
- Crossfader control

**Right:** Deck B
- Same as Deck A
- Typically your "next" track

---

## 🔧 Under the Hood

### Audio Analysis

Uses `librosa` + `essentia` to detect:
- BPM via beat tracking
- Key via chroma analysis
- Energy via RMS + spectral features
- Structure (intro, verse, drop, etc.)

### Real-Time Suggestions

Advisor engine watches:
- Current playback position
- Time remaining on deck
- Transition plan (from queue manager)
- Energy flow

Suggests:
- When to load next track
- When to start mixing
- What EQ changes to make
- Loop opportunities

### Audio Playback

- `sounddevice` for low-latency output
- 44.1kHz stereo
- Real-time mixing in audio callback
- Effects applied per deck

---

## 🐛 Troubleshooting

### No audio?

```bash
# Test audio output
python -c "import sounddevice as sd; print(sd.query_devices())"
```

### Analysis fails?

**Check:**
- MP3 file is valid
- File size < 50MB
- Sample rate is standard (44.1kHz)

**Logs show:**
```
📥 Uploaded: track.mp3
🔍 Analyzing...
✅ Analyzed: 128 BPM, Am
```

### Tracks not loading?

**Make sure:**
- Track was analyzed (shows in library)
- File path is valid
- Deck is not currently playing

---

## 📖 Next Steps

### Learn More

- **`AUDIO_ENGINE_COMPLETE.md`** - Technical details
- **`WEEK_7_8.md`** - Development history
- **`IMPLEMENTATION_SUMMARY.md`** - Architecture

### Advanced Features (Coming Soon)

- Section detection (intro/drop colors)
- Loop controls with markers
- Beatmatching (auto BPM sync)
- Effects presets
- Set recording

---

## 🎉 You're Ready!

**Now go DJ!**

1. Upload some tracks
2. Load them into decks
3. Follow the suggestions
4. Have fun! 🎧🔥

---

**Questions?** Check the other docs or experiment - you can't break anything!

**Tips:**
- Start with 2-3 tracks
- Let suggestions guide you
- Practice makes perfect
- Have fun with it!

🎧 **Happy DJing!**
