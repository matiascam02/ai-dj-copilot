#!/usr/bin/env python3
"""
Test crossfader with tone generators
Generates test tones so you don't need MP3 files
"""

import numpy as np
import sounddevice as sd
import time
from backend.audio_engine.player import DJMixer

print("🎧 Crossfader Test")
print("=" * 50)

# Create mixer
mixer = DJMixer()
mixer.start()

# Generate test tones (left = 440Hz, right = 880Hz)
sample_rate = 44100
duration = 30  # 30 seconds

# Tone A: 440Hz (A note)
t = np.linspace(0, duration, int(sample_rate * duration))
tone_a = np.sin(2 * np.pi * 440 * t) * 0.3
tone_a_stereo = np.column_stack([tone_a, tone_a])

# Tone B: 880Hz (A note, one octave higher)
tone_b = np.sin(2 * np.pi * 880 * t) * 0.3
tone_b_stereo = np.column_stack([tone_b, tone_b])

# Load tones into decks
print("\n📝 Loading test tones...")
print("   Deck A: 440 Hz (low tone)")
print("   Deck B: 880 Hz (high tone)")

mixer.deck_a.audio = tone_a_stereo.astype(np.float32)
mixer.deck_a.sample_rate = sample_rate
mixer.deck_a.duration = duration
mixer.deck_a.track_path = "Test Tone A (440Hz)"

mixer.deck_b.audio = tone_b_stereo.astype(np.float32)
mixer.deck_b.sample_rate = sample_rate
mixer.deck_b.duration = duration
mixer.deck_b.track_path = "Test Tone B (880Hz)"

# Start both decks
print("\n▶️  Starting both decks...")
mixer.deck_a.play()
mixer.deck_b.play()

print("\n🎚️  Testing crossfader...")
print("   Listen carefully:\n")

# Test crossfader positions
positions = [
    (-1.0, "Full LEFT (only 440 Hz - low tone)"),
    (-0.5, "Quarter left (mostly 440 Hz)"),
    (0.0, "CENTER (both tones mixed)"),
    (0.5, "Quarter right (mostly 880 Hz)"),
    (1.0, "Full RIGHT (only 880 Hz - high tone)"),
]

for cf_value, description in positions:
    mixer.set_crossfader(cf_value)
    
    # Calculate levels
    cf_pos = (cf_value + 1) / 2
    a_level = np.cos(cf_pos * np.pi / 2)
    b_level = np.sin(cf_pos * np.pi / 2)
    
    print(f"   CF={cf_value:+.1f} → A:{a_level*100:5.1f}% B:{b_level*100:5.1f}% | {description}")
    time.sleep(3)

print("\n✓ Test complete!")
print("\nDid you hear the tones change?")
print("  • At -1.0: Only LOW tone (440 Hz)")
print("  • At  0.0: Both tones mixed")
print("  • At +1.0: Only HIGH tone (880 Hz)")
print("\nIf YES: Crossfader works! ✅")
print("If NO: Audio issue ❌")

mixer.stop()
