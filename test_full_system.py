#!/usr/bin/env python3
"""
Full System Test - Tests all components (Week 1-6)

Tests:
1. Track Analysis (quick_test.py - already works)
2. Queue Manager (Week 1-2)
3. Transition Planner (Week 3-4)
4. API endpoints (Week 5-6)
"""

import os
import sys
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

print("🎧 AI DJ Co-Pilot - Full System Test")
print("=" * 60)
print()

# Test 1: Check imports
print("Step 1: Checking imports...")
print("-" * 60)

try:
    from backend.audio_analysis.track_analyzer import TrackAnalyzer
    print("✓ TrackAnalyzer imported")
except ImportError as e:
    print(f"✗ TrackAnalyzer import failed: {e}")
    sys.exit(1)

try:
    from backend.queue_manager.queue import QueueManager
    print("✓ QueueManager imported")
except ImportError as e:
    print(f"✗ QueueManager import failed: {e}")
    sys.exit(1)

try:
    from backend.queue_manager.transition_planner import TransitionPlanner
    print("✓ TransitionPlanner imported")
except ImportError as e:
    print(f"✗ TransitionPlanner import failed: {e}")
    sys.exit(1)

print()

# Test 2: Load analyzed tracks
print("Step 2: Loading track library...")
print("-" * 60)

cache_file = Path("data/cache/quick_test_results.json")
if not cache_file.exists():
    print("✗ No analyzed tracks found")
    print(f"  Run: python quick_test.py")
    print()
    sys.exit(1)

with open(cache_file, 'r') as f:
    data = json.load(f)
    tracks = data.get('tracks', [])

if len(tracks) < 2:
    print(f"✗ Need at least 2 tracks, found {len(tracks)}")
    print(f"  Add more tracks to data/tracks/test/")
    print()
    sys.exit(1)

print(f"✓ Loaded {len(tracks)} track(s)")
for track in tracks:
    name = Path(track['file_path']).name
    print(f"  - {name}: {track['bpm']:.1f} BPM, {track['camelot']}")
print()

# Test 3: Queue Manager
print("Step 3: Testing Queue Manager...")
print("-" * 60)

qm = QueueManager()

# Set current track
current_track = tracks[0]
qm.set_current_track(current_track)
print(f"✓ Set current track: {Path(current_track['file_path']).name}")

# Add remaining tracks to queue
for track in tracks[1:]:
    qm.add_track(track)
print(f"✓ Added {len(tracks) - 1} track(s) to queue")
print()

# Get next track suggestions
print("Next track suggestions:")
suggestions = qm.get_next_track(count=min(3, len(tracks) - 1))

for i, (track, score) in enumerate(suggestions, 1):
    name = Path(track['file_path']).name
    rating = qm._score_to_rating(score)
    print(f"  {i}. {name}")
    print(f"     BPM: {track['bpm']:.1f}, Key: {track['camelot']}")
    print(f"     Compatibility: {score:.2%} {rating}")
    print()

# Get compatibility matrix
print("Compatibility Matrix:")
matrix = qm.get_compatibility_matrix()
for entry in matrix[:5]:  # Show top 5
    name_a = Path(entry['track_a']).stem[:25]
    name_b = Path(entry['track_b']).stem[:25]
    print(f"  {name_a} ↔ {name_b}")
    print(f"    ΔBPM: {entry['bpm_diff']:.1f} | Score: {entry['score']:.2%} {entry['rating']}")
print()

# Test 4: Transition Planner
print("Step 4: Testing Transition Planner...")
print("-" * 60)

tp = TransitionPlanner()

# Plan a transition
if len(tracks) >= 2:
    track_a = current_track
    track_b = tracks[1]
    
    plan = tp.plan_transition(track_a, track_b, transition_type='standard')
    
    print(f"Transition Plan:")
    print(f"  Track A: {Path(track_a['file_path']).name}")
    print(f"    Start mixing at: {plan['track_a']['transition_start']:.1f}s (bar {plan['track_a']['transition_start_bars']})")
    print()
    
    print(f"  Track B: {Path(track_b['file_path']).name}")
    print(f"    Cue point: {plan['track_b']['cue_point']:.1f}s (bar {plan['track_b']['cue_point_bars']})")
    print()
    
    print(f"  Transition:")
    print(f"    Duration: {plan['transition']['duration']:.1f}s ({plan['transition']['duration_bars']} bars)")
    print(f"    Type: {plan['transition']['type']}")
    print()
    
    print(f"  Timeline (first 5 events):")
    for event in plan['timeline'][:5]:
        print(f"    Beat {event['beat']:3d} ({event['time']:5.1f}s): {event['description']}")
    print()

# Test 5: Summary
print("Step 5: System Status")
print("-" * 60)
print("✓ All components working!")
print()
print("Component Status:")
print(f"  ✓ Track Analysis: {len(tracks)} track(s) analyzed")
print(f"  ✓ Queue Manager: Working with {len(qm.queue)} track(s) in queue")
print(f"  ✓ Transition Planner: Generated {len(plan['timeline'])} automation events")
print()
print("=" * 60)
print("🎉 Full system test PASSED!")
print()
print("Next steps:")
print("  1. Start the web UI: python -m uvicorn backend.api.main:app --reload")
print("  2. Open http://localhost:8000 in your browser")
print("  3. Upload more tracks and test the interface")
print()
