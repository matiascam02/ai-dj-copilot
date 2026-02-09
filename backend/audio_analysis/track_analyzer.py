"""
Track Analyzer - Core audio analysis using Essentia & Librosa
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
import numpy as np

try:
    from essentia.standard import (
        MonoLoader,
        RhythmExtractor2013,
        KeyExtractor,
        Loudness,
    )
    ESSENTIA_AVAILABLE = True
except ImportError:
    print("Warning: Essentia not installed. Install with: pip install essentia-tensorflow")
    ESSENTIA_AVAILABLE = False

try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    print("Warning: Librosa not installed. Install with: pip install librosa")
    LIBROSA_AVAILABLE = False


class TrackAnalyzer:
    """Analyze audio tracks for DJ mixing purposes"""
    
    def __init__(self):
        if not ESSENTIA_AVAILABLE:
            raise ImportError("Essentia is required. Install with: pip install essentia-tensorflow")
    
    def analyze(self, audio_path: str) -> Dict:
        """
        Complete track analysis
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dictionary containing all analysis results
        """
        print(f"Analyzing: {audio_path}")
        
        # Load audio
        loader = MonoLoader(filename=audio_path)
        audio = loader()
        
        # Extract features
        results = {
            "file_path": audio_path,
            "duration": len(audio) / 44100.0,  # Assuming 44.1kHz
        }
        
        # Rhythm analysis (BPM + beats)
        print("  → Extracting rhythm...")
        rhythm_results = self._extract_rhythm(audio)
        results.update(rhythm_results)
        
        # Key detection
        print("  → Detecting key...")
        key_results = self._extract_key(audio)
        results.update(key_results)
        
        # Loudness
        print("  → Measuring loudness...")
        loudness_results = self._extract_loudness(audio)
        results.update(loudness_results)
        
        # Energy estimation (using Librosa if available)
        if LIBROSA_AVAILABLE:
            print("  → Estimating energy...")
            energy_results = self._estimate_energy(audio_path)
            results.update(energy_results)
        
        print("✓ Analysis complete!")
        return results
    
    def _extract_rhythm(self, audio: np.ndarray) -> Dict:
        """Extract BPM and beat positions"""
        rhythm_extractor = RhythmExtractor2013(method="multifeature")
        bpm, beats, beats_confidence, _, beats_intervals = rhythm_extractor(audio)
        
        # Find downbeats (simplified - every 4th beat)
        if len(beats) >= 4:
            downbeats = beats[::4].tolist()
        else:
            downbeats = []
        
        return {
            "bpm": float(bpm),
            "beats": beats.tolist(),
            "beats_confidence": float(beats_confidence),
            "downbeats": downbeats,
            "num_beats": len(beats),
        }
    
    def _extract_key(self, audio: np.ndarray) -> Dict:
        """Detect musical key"""
        key_extractor = KeyExtractor()
        key, scale, strength = key_extractor(audio)
        
        # Convert to Camelot notation
        camelot = self._to_camelot(key, scale)
        
        return {
            "key": key,
            "scale": scale,
            "key_strength": float(strength),
            "camelot": camelot,
        }
    
    def _extract_loudness(self, audio: np.ndarray) -> Dict:
        """Measure loudness (LUFS)"""
        loudness_extractor = Loudness()
        loudness = loudness_extractor(audio)
        
        return {
            "loudness": float(loudness),
        }
    
    def _estimate_energy(self, audio_path: str) -> Dict:
        """Estimate energy level using Librosa"""
        y, sr = librosa.load(audio_path, sr=22050)
        
        # RMS energy
        rms = librosa.feature.rms(y=y)[0]
        energy = float(np.mean(rms))
        
        # Spectral centroid (brightness)
        centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        brightness = float(np.mean(centroid))
        
        return {
            "energy": energy,
            "brightness": brightness,
        }
    
    def _to_camelot(self, key: str, scale: str) -> str:
        """Convert musical key to Camelot notation"""
        # Simplified Camelot wheel mapping
        CAMELOT_MINOR = {
            'A': '1A', 'E': '2A', 'B': '3A', 'F#': '4A',
            'C#': '5A', 'G#': '6A', 'D#': '7A', 'A#': '8A',
            'F': '9A', 'C': '10A', 'G': '11A', 'D': '12A',
        }
        CAMELOT_MAJOR = {
            'C': '1B', 'G': '2B', 'D': '3B', 'A': '4B',
            'E': '5B', 'B': '6B', 'F#': '7B', 'C#': '8B',
            'G#': '9B', 'D#': '10B', 'A#': '11B', 'F': '12B',
        }
        
        if scale == 'minor':
            return CAMELOT_MINOR.get(key, 'Unknown')
        else:
            return CAMELOT_MAJOR.get(key, 'Unknown')
    
    def save_analysis(self, results: Dict, output_path: Optional[str] = None):
        """Save analysis results to JSON"""
        if output_path is None:
            track_name = Path(results["file_path"]).stem
            output_path = f"{track_name}_analysis.json"
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"✓ Saved analysis to: {output_path}")


def main():
    """CLI entry point"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python track_analyzer.py <audio_file>")
        sys.exit(1)
    
    audio_path = sys.argv[1]
    
    if not Path(audio_path).exists():
        print(f"Error: File not found: {audio_path}")
        sys.exit(1)
    
    # Analyze
    analyzer = TrackAnalyzer()
    results = analyzer.analyze(audio_path)
    
    # Print summary
    print("\n" + "="*50)
    print("ANALYSIS SUMMARY")
    print("="*50)
    print(f"Track: {Path(audio_path).name}")
    print(f"Duration: {results['duration']:.1f}s")
    print(f"BPM: {results['bpm']:.1f}")
    print(f"Key: {results['key']} {results['scale']} ({results['camelot']})")
    print(f"Loudness: {results['loudness']:.2f} LUFS")
    if 'energy' in results:
        print(f"Energy: {results['energy']:.3f}")
    print("="*50)
    
    # Save
    analyzer.save_analysis(results)


if __name__ == "__main__":
    main()
