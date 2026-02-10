#!/usr/bin/env python3
"""
Simple Track Analyzer - Librosa-only fallback
Works without Essentia for basic analysis
"""

import librosa
import numpy as np
from pathlib import Path
from typing import Dict


class SimpleTrackAnalyzer:
    """Simple analyzer using only librosa (no Essentia required)"""
    
    def analyze(self, audio_path: str) -> Dict:
        """
        Analyze audio track using librosa only
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dictionary with analysis results
        """
        print(f"Analyzing (librosa): {audio_path}")
        
        # Extract filename
        file_path_obj = Path(audio_path)
        filename = file_path_obj.name
        title = file_path_obj.stem
        
        # Load audio
        print("  → Loading audio...")
        y, sr = librosa.load(audio_path, sr=44100, mono=True)
        duration = len(y) / sr
        
        # BPM detection
        print("  → Detecting BPM...")
        try:
            tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
            bpm = float(tempo) if isinstance(tempo, (int, float, np.number)) else float(tempo[0])
        except Exception as e:
            print(f"  ⚠️ BPM detection failed: {e}")
            bpm = 120.0  # Default
        
        # Key detection (simplified)
        print("  → Detecting key...")
        try:
            chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
            chroma_mean = np.mean(chroma, axis=1)
            key_index = np.argmax(chroma_mean)
            
            keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            key = keys[key_index]
            scale = 'major'  # Simplified (would need more analysis)
            
            # Camelot wheel (simplified mapping)
            camelot_map = {
                'C': '8B', 'G': '9B', 'D': '10B', 'A': '11B',
                'E': '12B', 'B': '1B', 'F#': '2B', 'C#': '3B',
                'G#': '4B', 'D#': '5B', 'A#': '6B', 'F': '7B'
            }
            camelot = camelot_map.get(key, '8B')
        except Exception as e:
            print(f"  ⚠️ Key detection failed: {e}")
            key = 'Am'
            scale = 'minor'
            camelot = '8A'
        
        # Energy (RMS)
        print("  → Calculating energy...")
        try:
            rms = librosa.feature.rms(y=y)[0]
            energy = float(np.mean(rms))
            energy = min(1.0, energy * 3)  # Normalize to 0-1
        except Exception as e:
            print(f"  ⚠️ Energy calculation failed: {e}")
            energy = 0.5
        
        # Loudness (approximation)
        try:
            loudness = 20 * np.log10(np.sqrt(np.mean(y**2)) + 1e-10)
        except Exception as e:
            print(f"  ⚠️ Loudness calculation failed: {e}")
            loudness = -20.0
        
        results = {
            'file_path': audio_path,
            'filename': filename,
            'title': title,
            'duration': duration,
            'bpm': bpm,
            'key': key,
            'scale': scale,
            'camelot': camelot,
            'energy': energy,
            'loudness': loudness
        }
        
        print(f"✓ Analysis complete: {bpm:.0f} BPM, {key}")
        
        return results


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python simple_analyzer.py <audio_file>")
        sys.exit(1)
    
    analyzer = SimpleTrackAnalyzer()
    result = analyzer.analyze(sys.argv[1])
    
    print("\n" + "="*50)
    print("ANALYSIS RESULT")
    print("="*50)
    for key, value in result.items():
        if key not in ['file_path']:
            print(f"{key}: {value}")
