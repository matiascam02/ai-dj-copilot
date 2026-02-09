#!/usr/bin/env python3
"""
Quick Test - Analyze all tracks in data/tracks/test/
"""

import os
import sys
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from backend.audio_analysis.track_analyzer import TrackAnalyzer
except ImportError:
    print("Error: Could not import TrackAnalyzer")
    print("Make sure you're in the project root and ran setup.sh")
    sys.exit(1)


def main():
    print("🎧 AI DJ Co-Pilot - Quick Test")
    print("=" * 50)
    print()
    
    # Find test tracks
    test_dir = Path("data/tracks/test")
    if not test_dir.exists():
        print(f"Error: Directory not found: {test_dir}")
        print("Create it with: mkdir -p data/tracks/test")
        print("Then add some MP3 files there")
        sys.exit(1)
    
    # Find audio files
    audio_files = []
    for ext in ['*.mp3', '*.wav', '*.flac', '*.m4a']:
        audio_files.extend(test_dir.glob(ext))
    
    if not audio_files:
        print(f"No audio files found in {test_dir}")
        print()
        print("Download some test music:")
        print("  1. Run: bash download_test_music.sh")
        print("  2. Or manually download from:")
        print("     - https://freemusicarchive.org/")
        print("     - https://www.jamendo.com/")
        print()
        sys.exit(1)
    
    print(f"Found {len(audio_files)} track(s) to analyze")
    print()
    
    # Analyze all tracks
    analyzer = TrackAnalyzer()
    results = []
    
    for i, audio_path in enumerate(audio_files, 1):
        print(f"[{i}/{len(audio_files)}] {audio_path.name}")
        print("-" * 50)
        
        try:
            result = analyzer.analyze(str(audio_path))
            results.append(result)
            
            # Print summary
            print(f"  BPM: {result['bpm']:.1f}")
            print(f"  Key: {result['key']} {result['scale']} ({result['camelot']})")
            print(f"  Duration: {result['duration']:.1f}s")
            if 'energy' in result:
                print(f"  Energy: {result['energy']:.3f}")
            print()
            
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            print()
            continue
    
    # Save results
    if results:
        output_file = Path("data/cache/quick_test_results.json")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump({
                'total_tracks': len(results),
                'tracks': results
            }, f, indent=2)
        
        print("=" * 50)
        print(f"✓ Analyzed {len(results)}/{len(audio_files)} tracks successfully")
        print(f"✓ Results saved to: {output_file}")
        print()
        
        # Print compatibility matrix
        if len(results) >= 2:
            print("Compatibility Matrix (BPM difference):")
            print("-" * 50)
            for i, track_a in enumerate(results):
                name_a = Path(track_a['file_path']).stem[:20]
                for j, track_b in enumerate(results):
                    if i >= j:
                        continue
                    name_b = Path(track_b['file_path']).stem[:20]
                    bpm_diff = abs(track_a['bpm'] - track_b['bpm'])
                    
                    # Simple compatibility
                    if bpm_diff <= 6:
                        compat = "🟢 Perfect"
                    elif bpm_diff <= 12:
                        compat = "🟡 Good"
                    else:
                        compat = "🔴 Difficult"
                    
                    print(f"  {name_a:20s} ↔ {name_b:20s} | ΔBPM: {bpm_diff:4.1f} | {compat}")
            print()
    else:
        print("✗ No tracks analyzed successfully")
        sys.exit(1)


if __name__ == "__main__":
    main()
