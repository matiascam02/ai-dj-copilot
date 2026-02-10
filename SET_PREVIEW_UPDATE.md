# Set Preview & Multi-Select - Implementation Plan

## User Request
"Select which songs for the set, see preview/roadmap of AI's plan before starting, see all effects, smart suggestions during playback"

## What's Implemented

### Backend ✅
1. **SetPlanner class** (`set_planner.py`)
   - `build_visual_plan()` - Generates detailed timeline
   - Timeline with icons, timestamps, descriptions
   - Transition summaries with compatibility scores
   - Smart suggestions generator

2. **Updated API** (`complete_interface.py`)
   - Modified `/auto_dj/build_plan` to accept track selection
   - Returns both automation plan + visual roadmap
   - Integrated SetPlanner

## What Needs UI Implementation

### 1. Track Selection (Checkboxes)
```javascript
// Add to each track card:
<input type="checkbox" class="track-select" 
       onchange="toggleTrackSelection(track.file_path)">

// Track selected tracks:
let selectedTracks = [];
```

### 2. Build Set Plan Button
```html
<!-- In Library tab -->
<button onclick="buildSetPreview()" 
        id="build-plan-btn" disabled>
  🎯 Build Set Plan (0 tracks)
</button>
```

### 3. Preview Modal
```html
<div class="preview-modal" id="preview-modal">
  <div class="preview-content">
    <h2>🎯 Set Plan Preview</h2>
    
    <!-- Track Order -->
    <div class="track-order">
      1. Track Name (4:30)
      2. Track Name (5:15)
      3. Track Name (3:45)
    </div>
    
    <!-- Timeline -->
    <div class="timeline">
      00:00 ▶️ Start playing: Track 1
      03:44 📀 Load to Deck B: Track 2
      04:14 ▶️ Start Deck B (silent)
      04:30 🎛️ Cut bass on Track 1
      04:38 🎚️ Crossfader → center
      04:46 ✅ Track 2 only
      ...
    </div>
    
    <!-- Transitions Summary -->
    <div class="transitions">
      Track 1 → Track 2
        Duration: 16s
        Compatibility: 85%
        BPM diff: 3 BPM
        Energy: 🔥 Energy UP
    </div>
    
    <!-- Actions -->
    <button onclick="startAutoDJ()">
      🚀 Start Auto DJ
    </button>
    <button onclick="closePreview()">
      ← Back to Selection
    </button>
  </div>
</div>
```

### 4. Smart Suggestions During Playback
```javascript
// Enhanced updateDJUI() to show:
- Current action
- Next 2-3 actions
- Manual suggestions
- Energy flow indicator
```

## Quick Implementation Steps

1. Add checkboxes to track cards
2. Track selected[] array
3. Enable "Build Set Plan" button when tracks selected
4. On click → Call `/auto_dj/build_plan` with indices
5. Show modal with visual plan
6. "Start Auto DJ" button in modal
7. Enhanced suggestion display during playback

## API Response Structure

```json
{
  "status": "ok",
  "tracks": 3,
  "total_duration": 932.5,
  "visual": {
    "total_duration_str": "15m 32s",
    "timeline": [
      {
        "time": 0.0,
        "time_str": "00:00",
        "action": "start_set",
        "icon": "▶️",
        "description": "Start playing: Track 1",
        "track_index": 0
      },
      ...
    ],
    "transitions": [
      {
        "from": "Track 1",
        "to": "Track 2",
        "duration": 16,
        "method": "energy_match",
        "compatibility": 0.85,
        "bpm_diff": 3,
        "energy_flow": "🔥 Energy UP"
      }
    ],
    "track_list": [...]
  }
}
```

## Next Steps

Would you like me to:
A) Implement the full UI now (checkboxes + modal + preview)?
B) Show you the backend API response first so you can test it?
C) Create a simpler initial version to iterate on?

The backend is ready - just need to connect the UI!
