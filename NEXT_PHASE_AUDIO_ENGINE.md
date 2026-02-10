# Next Phase: Audio Engine + Real-Time Control

**Goal:** Make it playable - actual audio, real-time suggestions, effects

**Timeline:** 2-3 days intensive work

---

## What You Want

✅ **Listen to it working** - Real audio playback  
✅ **Real-time suggestions** - "What to do now?"  
✅ **Effects control** - Loops, reverb, fader, EQ  
✅ **Section awareness** - Intro/verse/drop detection  

---

## Architecture

```
┌─────────────────────────────────────────────────┐
│         Web UI / Control Interface              │
│  (What you see: suggestions, controls, meters)  │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│          Suggestion Engine                      │
│  "Cut bass on deck A now"                       │
│  "Start fading in 8 bars"                       │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│          Mixer Engine                           │
│  Crossfader, EQ, Effects, Volume                │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────┐
│         Audio Engine (2 Decks)                  │
│  Deck A ◄────────────────► Deck B               │
└────────────────┬────────────────────────────────┘
                 │
                 ▼
         Your Speakers 🔊
```

---

## Phase 1: Basic Audio Playback (Day 1)

### Goal: Play 2 tracks simultaneously with crossfader

```python
# backend/audio_engine/player.py

import sounddevice as sd
import soundfile as sf
import numpy as np
import threading

class AudioDeck:
    """Single DJ deck"""
    
    def __init__(self, deck_id):
        self.deck_id = deck_id
        self.audio = None
        self.sample_rate = 44100
        self.position = 0
        self.is_playing = False
        self.volume = 1.0
        self.speed = 1.0  # For pitch/tempo
        
    def load(self, file_path):
        """Load audio file"""
        self.audio, self.sample_rate = sf.read(file_path, always_2d=True)
        self.position = 0
        
    def play(self):
        self.is_playing = True
        
    def pause(self):
        self.is_playing = False
        
    def cue(self, seconds):
        """Jump to position"""
        self.position = int(seconds * self.sample_rate)
        
    def get_frame(self, num_samples):
        """Get next audio chunk"""
        if not self.is_playing or self.audio is None:
            return np.zeros((num_samples, 2))
        
        end = self.position + num_samples
        if end > len(self.audio):
            self.is_playing = False
            return np.zeros((num_samples, 2))
        
        chunk = self.audio[self.position:end]
        self.position = end
        
        return chunk * self.volume


class DJMixer:
    """2-deck mixer with crossfader"""
    
    def __init__(self):
        self.deck_a = AudioDeck('A')
        self.deck_b = AudioDeck('B')
        self.crossfader = 0.0  # -1 = A only, 0 = center, +1 = B only
        self.master_volume = 0.8
        
        self.stream = None
        self.is_running = False
        
    def start(self):
        """Start audio output"""
        self.is_running = True
        self.stream = sd.OutputStream(
            samplerate=44100,
            channels=2,
            callback=self._audio_callback,
            blocksize=1024
        )
        self.stream.start()
        
    def stop(self):
        """Stop audio"""
        self.is_running = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            
    def _audio_callback(self, outdata, frames, time_info, status):
        """Real-time audio mixing"""
        # Get audio from both decks
        a_audio = self.deck_a.get_frame(frames)
        b_audio = self.deck_b.get_frame(frames)
        
        # Apply crossfader
        # -1 to +1 → 0.0 to 1.0
        cf_position = (self.crossfader + 1) / 2
        
        a_level = 1.0 - cf_position
        b_level = cf_position
        
        # Mix
        mixed = (a_audio * a_level) + (b_audio * b_level)
        
        # Master volume
        mixed *= self.master_volume
        
        # Prevent clipping
        peak = np.abs(mixed).max()
        if peak > 1.0:
            mixed /= peak
        
        outdata[:] = mixed
```

**Test it:**

```python
# test_playback.py

mixer = DJMixer()

# Load tracks
mixer.deck_a.load('track1.mp3')
mixer.deck_b.load('track2.mp3')

# Start mixer
mixer.start()

# Play deck A
mixer.deck_a.play()

time.sleep(10)  # Play for 10 seconds

# Start crossfading to B
mixer.deck_b.play()

for i in range(100):
    mixer.crossfader = -1 + (i / 50)  # -1 to +1 over 100 steps
    time.sleep(0.1)

mixer.stop()
```

---

## Phase 2: EQ + Effects (Day 1-2)

### Goal: Bass/mid/high EQ + reverb + filter

```python
# backend/audio_engine/effects.py

from scipy import signal
import numpy as np

class EQ:
    """3-band EQ (bass, mid, high)"""
    
    def __init__(self, sample_rate=44100):
        self.sr = sample_rate
        
        # EQ gains (0.0 = mute, 1.0 = neutral, >1.0 = boost)
        self.bass = 1.0    # < 250 Hz
        self.mid = 1.0     # 250 Hz - 4 kHz
        self.high = 1.0    # > 4 kHz
        
        # Create filters
        self._create_filters()
        
    def _create_filters(self):
        """Create butterworth filters"""
        # Low-pass (bass)
        self.bass_b, self.bass_a = signal.butter(
            4, 250, btype='low', fs=self.sr
        )
        
        # Band-pass (mid)
        self.mid_b, self.mid_a = signal.butter(
            4, [250, 4000], btype='band', fs=self.sr
        )
        
        # High-pass (high)
        self.high_b, self.high_a = signal.butter(
            4, 4000, btype='high', fs=self.sr
        )
        
    def process(self, audio):
        """Apply EQ to audio"""
        # Split into frequency bands
        bass_band = signal.lfilter(self.bass_b, self.bass_a, audio, axis=0)
        mid_band = signal.lfilter(self.mid_b, self.mid_a, audio, axis=0)
        high_band = signal.lfilter(self.high_b, self.high_a, audio, axis=0)
        
        # Apply gains
        bass_band *= self.bass
        mid_band *= self.mid
        high_band *= self.high
        
        # Sum back together
        return bass_band + mid_band + high_band


class Filter:
    """Low-pass/high-pass filter (sweepable)"""
    
    def __init__(self, sample_rate=44100):
        self.sr = sample_rate
        self.cutoff = 20000  # Hz
        self.type = 'lowpass'  # or 'highpass'
        
    def process(self, audio):
        """Apply filter"""
        b, a = signal.butter(4, self.cutoff, btype=self.type, fs=self.sr)
        return signal.lfilter(b, a, audio, axis=0)


class Reverb:
    """Simple reverb (convolution-based)"""
    
    def __init__(self):
        self.wet = 0.0  # 0.0 = dry, 1.0 = full wet
        self.decay = 0.5
        
    def process(self, audio):
        """Apply reverb"""
        # Simplified - real reverb needs IR convolution
        # This is a quick delay-based reverb
        
        if self.wet == 0:
            return audio
            
        # Create delayed copies
        delayed = np.zeros_like(audio)
        
        delays = [441, 882, 1323]  # ~10ms, 20ms, 30ms at 44.1kHz
        
        for delay_samples in delays:
            if delay_samples < len(audio):
                delayed[delay_samples:] += audio[:-delay_samples] * self.decay
        
        # Mix dry and wet
        return (audio * (1 - self.wet)) + (delayed * self.wet)
```

**Add to DJMixer:**

```python
class DJMixer:
    def __init__(self):
        # ... existing code ...
        
        # Effects per deck
        self.deck_a_eq = EQ()
        self.deck_a_filter = Filter()
        self.deck_a_reverb = Reverb()
        
        self.deck_b_eq = EQ()
        self.deck_b_filter = Filter()
        self.deck_b_reverb = Reverb()
        
    def _audio_callback(self, outdata, frames, time_info, status):
        # Get raw audio
        a_audio = self.deck_a.get_frame(frames)
        b_audio = self.deck_b.get_frame(frames)
        
        # Apply effects to deck A
        a_audio = self.deck_a_eq.process(a_audio)
        a_audio = self.deck_a_filter.process(a_audio)
        a_audio = self.deck_a_reverb.process(a_audio)
        
        # Apply effects to deck B
        b_audio = self.deck_b_eq.process(b_audio)
        b_audio = self.deck_b_filter.process(b_audio)
        b_audio = self.deck_b_reverb.process(b_audio)
        
        # ... rest of mixing ...
```

---

## Phase 3: Real-Time Suggestions (Day 2)

### Goal: Tell you WHAT to do and WHEN

```python
# backend/suggestion_engine/realtime_advisor.py

class RealtimeAdvisor:
    """Suggests what to do in real-time"""
    
    def __init__(self, mixer, transition_plan):
        self.mixer = mixer
        self.plan = transition_plan
        self.current_event_index = 0
        
    def get_current_suggestion(self):
        """Get what to do RIGHT NOW"""
        
        # Get current position in track A
        deck_a = self.mixer.deck_a
        current_time = deck_a.position / deck_a.sample_rate
        
        # Check if we're in transition phase
        transition_start = self.plan['track_a']['transition_start']
        
        if current_time < transition_start - 32:
            return {
                'action': 'wait',
                'message': f'Playing normally. Transition in {int(transition_start - current_time)}s',
                'urgency': 'low',
                'color': 'green'
            }
        
        elif current_time < transition_start - 16:
            return {
                'action': 'prepare',
                'message': 'Prepare next track. Cue point ready?',
                'urgency': 'medium',
                'color': 'yellow',
                'todo': [
                    'Check track B is loaded',
                    'Set cue point',
                    'Monitor levels'
                ]
            }
        
        elif current_time >= transition_start:
            # We're in transition - find current event
            timeline = self.plan['timeline']
            
            for i, event in enumerate(timeline):
                if current_time >= transition_start + event['time']:
                    if i > self.current_event_index:
                        self.current_event_index = i
                        
                        return {
                            'action': event['action'],
                            'message': self._get_human_message(event),
                            'urgency': 'high',
                            'color': 'red',
                            'parameters': self._get_parameters(event)
                        }
            
        return {'action': 'wait', 'message': 'All good', 'urgency': 'low'}
    
    def _get_human_message(self, event):
        """Convert event to human-readable message"""
        
        messages = {
            'start_deck_b': '▶️ START DECK B (silent)',
            'eq_low_cut_deck_a_start': '🎛️ CUT BASS on Deck A',
            'eq_low_introduce_deck_b': '🎛️ BRING IN BASS on Deck B',
            'crossfader_50_50': '🎚️ CROSSFADER to CENTER',
            'fade_out_deck_a': '🎚️ FADE OUT Deck A',
            'deck_b_only': '✅ DECK B ONLY - Transition complete!'
        }
        
        return messages.get(event['action'], event['description'])
    
    def _get_parameters(self, event):
        """Get specific parameters for action"""
        
        if 'eq_low_cut' in event['action']:
            return {'eq_bass': 0.3}
        
        elif 'eq_low_introduce' in event['action']:
            return {'eq_bass': 1.0}
        
        elif 'crossfader' in event['action']:
            return {'crossfader': 0.0}  # Center
        
        return {}
```

---

## Phase 4: Web UI Updates (Day 2-3)

### Goal: Visual feedback + controls

Add to `backend/api/main.py`:

```python
@app.get("/mixer/status")
async def mixer_status():
    """Get current mixer state"""
    return {
        'deck_a': {
            'playing': mixer.deck_a.is_playing,
            'position': mixer.deck_a.position / mixer.deck_a.sample_rate,
            'track': mixer.deck_a.current_track,
            'volume': mixer.deck_a.volume
        },
        'deck_b': {
            'playing': mixer.deck_b.is_playing,
            'position': mixer.deck_b.position / mixer.deck_b.sample_rate,
            'track': mixer.deck_b.current_track,
            'volume': mixer.deck_b.volume
        },
        'crossfader': mixer.crossfader,
        'suggestion': advisor.get_current_suggestion()
    }

@app.post("/mixer/control")
async def control_mixer(command: dict):
    """Control mixer (play, pause, EQ, effects)"""
    
    action = command['action']
    
    if action == 'play_a':
        mixer.deck_a.play()
    elif action == 'play_b':
        mixer.deck_b.play()
    elif action == 'set_crossfader':
        mixer.crossfader = command['value']
    elif action == 'set_eq_bass_a':
        mixer.deck_a_eq.bass = command['value']
    # ... etc
    
    return {'status': 'ok'}
```

**UI with live suggestions:**

```html
<!-- Real-time suggestion panel -->
<div id="suggestion-panel" class="suggestion-card">
    <h2>🎯 What To Do Now</h2>
    <div id="suggestion-message" class="message">
        Loading...
    </div>
    <div id="suggestion-actions" class="actions">
        <!-- Action buttons appear here -->
    </div>
</div>

<script>
    // Poll for suggestions every 100ms
    setInterval(async () => {
        const status = await fetch('/mixer/status').then(r => r.json());
        
        const suggestion = status.suggestion;
        
        // Update message
        document.getElementById('suggestion-message').textContent = suggestion.message;
        
        // Change color based on urgency
        const panel = document.getElementById('suggestion-panel');
        panel.className = `suggestion-card ${suggestion.urgency}`;
        
        // Show action buttons if needed
        if (suggestion.parameters) {
            showActionButtons(suggestion.parameters);
        }
    }, 100);
    
    function showActionButtons(params) {
        // Create buttons for suggested actions
        const container = document.getElementById('suggestion-actions');
        
        if (params.eq_bass !== undefined) {
            container.innerHTML = `
                <button onclick="setEQ('bass', ${params.eq_bass})">
                    ${params.eq_bass < 0.5 ? '🔻 Cut Bass' : '🔺 Boost Bass'}
                </button>
            `;
        }
    }
</script>
```

---

## Phase 5: Section Detection (Day 3)

### Goal: Know intro/verse/chorus/drop

```python
# backend/audio_analysis/section_detector.py

import librosa
import numpy as np

class SectionDetector:
    """Detect song sections (intro, verse, chorus, drop, breakdown)"""
    
    def detect_sections(self, audio_path):
        """Analyze and label sections"""
        
        # Load audio
        y, sr = librosa.load(audio_path)
        
        # Detect beats
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
        beat_times = librosa.frames_to_time(beats, sr=sr)
        
        # Detect sections using self-similarity
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        similarity = librosa.segment.recurrence_matrix(
            chroma, 
            mode='affinity',
            metric='cosine'
        )
        
        # Find boundaries
        boundaries = librosa.segment.agglomerative(similarity, k=8)
        boundary_times = librosa.frames_to_time(boundaries, sr=sr)
        
        # Classify each section
        sections = []
        for i, start in enumerate(boundary_times[:-1]):
            end = boundary_times[i + 1]
            
            section_audio = y[int(start*sr):int(end*sr)]
            
            # Classify based on energy and spectral features
            energy = librosa.feature.rms(y=section_audio)[0].mean()
            spectral_centroid = librosa.feature.spectral_centroid(
                y=section_audio, sr=sr
            )[0].mean()
            
            # Simple heuristic classification
            if i == 0:
                label = 'intro'
            elif i == len(boundary_times) - 2:
                label = 'outro'
            elif energy > 0.15 and spectral_centroid > 3000:
                label = 'drop'
            elif energy < 0.08:
                label = 'breakdown'
            elif energy > 0.12:
                label = 'chorus'
            else:
                label = 'verse'
            
            sections.append({
                'start': float(start),
                'end': float(end),
                'label': label,
                'energy': float(energy),
                'duration': float(end - start)
            })
        
        return sections
```

**Use it for better suggestions:**

```python
# Now advisor can say:
# "Drop coming in 8 bars - prepare filter sweep"
# "Breakdown ahead - good time to transition"
# "Chorus starting - peak energy"
```

---

## Quick Start Guide

### Step 1: Install audio dependencies

```bash
pip install sounddevice soundfile scipy
```

### Step 2: Create basic player

```bash
# I'll create the files now
```

### Step 3: Test playback

```python
python backend/audio_engine/test_player.py
```

### Step 4: Test with web UI

```bash
./run_server.sh
# Open http://localhost:8000/mixer
```

---

## Timeline

**Day 1 (Today):**
- ✅ Basic audio playback (2 decks + crossfader)
- ✅ Simple EQ (bass/mid/high)

**Day 2 (Tomorrow):**
- Real-time suggestion engine
- Web UI with live controls
- Effects (reverb, filter)

**Day 3:**
- Section detection
- Loop controls
- Polish & testing

---

## Want me to start building this NOW?

I can implement:
1. Basic audio player first (so you can hear it)
2. Then add effects
3. Then real-time suggestions

Let me know and I'll build it! 🎧🚀
