#!/usr/bin/env python3
"""
Queue Manager - Smart track queue with compatibility scoring

Handles:
- Track queue management
- Compatibility scoring (BPM, Key, Energy)
- Camelot wheel logic for harmonic mixing
- Next track suggestions
"""

from typing import List, Dict, Tuple, Optional
import json


class QueueManager:
    """Manages DJ queue with intelligent track suggestions"""
    
    def __init__(self):
        self.queue: List[Dict] = []
        self.current_track: Optional[Dict] = None
        self.played_tracks: List[Dict] = []
        
    def add_track(self, track_analysis: Dict) -> None:
        """Add track to queue"""
        self.queue.append(track_analysis)
        
    def remove_track(self, track_id: str) -> bool:
        """Remove track from queue by file path"""
        for i, track in enumerate(self.queue):
            if track.get('file_path') == track_id:
                self.queue.pop(i)
                return True
        return False
        
    def set_current_track(self, track_analysis: Dict) -> None:
        """Set the currently playing track"""
        if self.current_track:
            self.played_tracks.append(self.current_track)
        self.current_track = track_analysis
        
    def get_next_track(self, count: int = 1) -> List[Tuple[Dict, float]]:
        """
        Get next track(s) with compatibility scores
        
        Args:
            count: Number of suggestions to return
            
        Returns:
            List of (track, score) tuples, sorted by score (best first)
        """
        if not self.queue:
            return []
            
        if not self.current_track:
            # No current track, just return first track(s)
            return [(track, 1.0) for track in self.queue[:count]]
        
        # Score all tracks in queue
        scored = []
        for track in self.queue:
            score = self._score_compatibility(self.current_track, track)
            scored.append((track, score))
        
        # Sort by score (best first)
        scored.sort(key=lambda x: x[1], reverse=True)
        
        return scored[:count]
    
    def _score_compatibility(self, track_a: Dict, track_b: Dict) -> float:
        """
        Score how well two tracks mix together
        
        Considers:
        - BPM compatibility (±6 BPM = perfect)
        - Key compatibility (Camelot wheel)
        - Energy compatibility (similar energy levels)
        
        Returns:
            Score from 0.0 (incompatible) to 1.0 (perfect match)
        """
        # BPM compatibility (40% weight)
        bpm_diff = abs(track_a['bpm'] - track_b['bpm'])
        if bpm_diff <= 6:
            bpm_score = 1.0
        else:
            bpm_score = max(0, 1 - (bpm_diff - 6) / 20)
        
        # Key compatibility (30% weight)
        key_score = self._camelot_compatibility(
            track_a.get('camelot', ''), 
            track_b.get('camelot', '')
        )
        
        # Energy compatibility (30% weight)
        energy_a = track_a.get('energy', 0.5)
        energy_b = track_b.get('energy', 0.5)
        energy_diff = abs(energy_a - energy_b)
        energy_score = max(0, 1 - energy_diff)
        
        # Weighted average
        total_score = (
            0.4 * bpm_score +
            0.3 * key_score +
            0.3 * energy_score
        )
        
        return total_score
    
    def _camelot_compatibility(self, camelot_a: str, camelot_b: str) -> float:
        """
        Check Camelot wheel compatibility
        
        Rules:
        - Same key (e.g., 1A → 1A): Perfect (1.0)
        - Relative major/minor (e.g., 1A → 1B): Perfect (1.0)
        - Adjacent keys (e.g., 1A → 2A or 12A): Good (0.8)
        - +1 hour (e.g., 1A → 2A): Good (0.8)
        - -1 hour (e.g., 1A → 12A): Good (0.8)
        - Everything else: Mediocre (0.5)
        
        Returns:
            Compatibility score from 0.5 to 1.0
        """
        if not camelot_a or not camelot_b:
            return 0.5
            
        if camelot_a == camelot_b:
            return 1.0  # Same key = perfect
        
        try:
            # Extract number and letter
            num_a = int(camelot_a[:-1])
            letter_a = camelot_a[-1]
            num_b = int(camelot_b[:-1])
            letter_b = camelot_b[-1]
            
            # Relative major/minor (same number, different letter)
            if num_a == num_b and letter_a != letter_b:
                return 1.0
            
            # Adjacent keys (±1 hour, same letter)
            if letter_a == letter_b:
                diff = (num_b - num_a) % 12
                if diff == 1 or diff == 11:  # +1 or -1 (wrapping at 12)
                    return 0.8
            
            # Not compatible, but not terrible
            return 0.5
            
        except (ValueError, IndexError):
            return 0.5
    
    def get_compatibility_matrix(self) -> List[Dict]:
        """
        Get compatibility scores for all pairs of tracks in queue
        
        Returns:
            List of compatibility entries with track pairs and scores
        """
        if not self.queue or len(self.queue) < 2:
            return []
        
        matrix = []
        for i, track_a in enumerate(self.queue):
            for j, track_b in enumerate(self.queue):
                if i >= j:
                    continue
                
                score = self._score_compatibility(track_a, track_b)
                
                matrix.append({
                    'track_a': track_a.get('file_path', 'Unknown'),
                    'track_b': track_b.get('file_path', 'Unknown'),
                    'bpm_a': track_a.get('bpm', 0),
                    'bpm_b': track_b.get('bpm', 0),
                    'bpm_diff': abs(track_a.get('bpm', 0) - track_b.get('bpm', 0)),
                    'key_a': f"{track_a.get('key', '?')} {track_a.get('scale', '?')}",
                    'key_b': f"{track_b.get('key', '?')} {track_b.get('scale', '?')}",
                    'camelot_a': track_a.get('camelot', ''),
                    'camelot_b': track_b.get('camelot', ''),
                    'score': score,
                    'rating': self._score_to_rating(score)
                })
        
        # Sort by score (best first)
        matrix.sort(key=lambda x: x['score'], reverse=True)
        
        return matrix
    
    def _score_to_rating(self, score: float) -> str:
        """Convert score to human-readable rating"""
        if score >= 0.85:
            return "🟢 Perfect"
        elif score >= 0.70:
            return "🟡 Good"
        elif score >= 0.50:
            return "🟠 OK"
        else:
            return "🔴 Difficult"
    
    def get_queue_info(self) -> Dict:
        """Get current queue status"""
        return {
            'current_track': self.current_track.get('file_path') if self.current_track else None,
            'queue_length': len(self.queue),
            'queue': [
                {
                    'file_path': t.get('file_path'),
                    'bpm': t.get('bpm'),
                    'key': f"{t.get('key', '?')} {t.get('scale', '?')}",
                    'camelot': t.get('camelot'),
                    'energy': t.get('energy', 0.5)
                }
                for t in self.queue
            ],
            'played_count': len(self.played_tracks)
        }


if __name__ == "__main__":
    # Quick test
    print("🎧 Queue Manager Test")
    print("=" * 50)
    
    # Create some fake tracks for testing
    track1 = {
        'file_path': 'track1.mp3',
        'bpm': 128.0,
        'key': 'A',
        'scale': 'minor',
        'camelot': '1A',
        'energy': 0.75,
        'duration': 240.0
    }
    
    track2 = {
        'file_path': 'track2.mp3',
        'bpm': 126.5,
        'key': 'B',
        'scale': 'minor',
        'camelot': '2A',
        'energy': 0.72,
        'duration': 250.0
    }
    
    track3 = {
        'file_path': 'track3.mp3',
        'bpm': 140.0,
        'key': 'C',
        'scale': 'major',
        'camelot': '8B',
        'energy': 0.85,
        'duration': 230.0
    }
    
    # Create queue manager
    qm = QueueManager()
    
    # Set current track
    qm.set_current_track(track1)
    print(f"Current track: {track1['file_path']}")
    print(f"  BPM: {track1['bpm']}, Key: {track1['camelot']}, Energy: {track1['energy']}")
    print()
    
    # Add tracks to queue
    qm.add_track(track2)
    qm.add_track(track3)
    print(f"Added {len(qm.queue)} tracks to queue")
    print()
    
    # Get next track suggestions
    print("Next track suggestions:")
    print("-" * 50)
    suggestions = qm.get_next_track(count=2)
    
    for i, (track, score) in enumerate(suggestions, 1):
        print(f"{i}. {track['file_path']}")
        print(f"   BPM: {track['bpm']}, Key: {track['camelot']}, Energy: {track['energy']}")
        print(f"   Compatibility: {score:.2%} ({qm._score_to_rating(score)})")
        print()
    
    print("✓ Queue Manager working!")
