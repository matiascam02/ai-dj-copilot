#!/usr/bin/env python3
"""
Transition Planner - Identifies optimal transition points between tracks

Handles:
- Transition point detection (where to start mixing)
- Cue point identification (where to start next track)
- Timeline generation (automation events)
- Transition strategies (quick mix, long blend, etc.)
"""

from typing import Dict, List, Optional
import json


class TransitionPlanner:
    """Plans transitions between DJ tracks"""
    
    def __init__(self):
        self.default_transition_bars = 16  # Standard DJ transition length
        
    def plan_transition(
        self, 
        track_a: Dict, 
        track_b: Dict,
        transition_type: str = 'standard'
    ) -> Dict:
        """
        Plan a transition between two tracks
        
        Args:
            track_a: Currently playing track analysis
            track_b: Next track analysis  
            transition_type: 'quick' (8 bars), 'standard' (16 bars), 'long' (32 bars)
            
        Returns:
            Transition plan with cue points and timeline
        """
        # Get transition length based on type
        if transition_type == 'quick':
            transition_bars = 8
        elif transition_type == 'long':
            transition_bars = 32
        else:
            transition_bars = self.default_transition_bars
        
        # Calculate bar length from BPM
        track_a_bpm = track_a['bpm']
        track_a_duration = track_a['duration']
        bar_length = self._calculate_bar_length(track_a_bpm)
        
        # Find transition start point in track A
        # Usually: start transition N bars before the end
        transition_start = track_a_duration - (transition_bars * bar_length)
        transition_start = max(0, transition_start)  # Don't go negative
        
        # Find cue point in track B
        # Usually: start at intro (first 16-32 beats)
        track_b_cue = self._find_cue_point(track_b)
        
        # Calculate transition duration
        transition_duration = transition_bars * bar_length
        
        # Generate automation timeline
        timeline = self._generate_timeline(
            transition_bars, 
            bar_length,
            track_a_bpm,
            track_b.get('bpm', track_a_bpm)
        )
        
        # Calculate mix strategy based on track compatibility
        mix_strategy = self._determine_mix_strategy(track_a, track_b)
        
        return {
            'track_a': {
                'file_path': track_a.get('file_path'),
                'transition_start': transition_start,
                'transition_start_bars': int(transition_start / bar_length),
                'bpm': track_a_bpm
            },
            'track_b': {
                'file_path': track_b.get('file_path'),
                'cue_point': track_b_cue,
                'cue_point_bars': int(track_b_cue / self._calculate_bar_length(track_b['bpm'])),
                'bpm': track_b['bpm']
            },
            'transition': {
                'duration': transition_duration,
                'duration_bars': transition_bars,
                'type': transition_type,
                'strategy': mix_strategy,
                'bar_length': bar_length
            },
            'timeline': timeline
        }
    
    def _calculate_bar_length(self, bpm: float) -> float:
        """
        Calculate length of one bar in seconds
        
        Args:
            bpm: Beats per minute
            
        Returns:
            Bar length in seconds (assuming 4/4 time signature)
        """
        beat_length = 60.0 / bpm  # Seconds per beat
        bar_length = beat_length * 4  # 4 beats per bar
        return bar_length
    
    def _find_cue_point(self, track: Dict) -> float:
        """
        Find optimal cue point to start next track
        
        Usually:
        - Start at beat 16 or 32 (after intro)
        - Or at first drop (if available)
        
        Args:
            track: Track analysis
            
        Returns:
            Cue point in seconds
        """
        # Check if we have beat positions
        if 'beats' in track and len(track['beats']) > 0:
            beats = track['beats']
            
            # Use 16th beat as cue (typical intro length)
            if len(beats) > 16:
                return beats[16]
            # Or use 8th beat if track is short
            elif len(beats) > 8:
                return beats[8]
            else:
                return 0.0
        
        # Fallback: estimate based on BPM
        bpm = track.get('bpm', 120)
        beat_length = 60.0 / bpm
        
        # Start at 16 beats (4 bars)
        return 16 * beat_length
    
    def _generate_timeline(
        self, 
        bars: int, 
        bar_length: float,
        bpm_a: float,
        bpm_b: float
    ) -> List[Dict]:
        """
        Generate automation timeline for transition
        
        Creates a series of events with timing and actions
        
        Args:
            bars: Number of bars in transition
            bar_length: Length of one bar in seconds
            bpm_a: BPM of track A
            bpm_b: BPM of track B
            
        Returns:
            List of automation events
        """
        timeline = []
        beats_per_bar = 4
        total_beats = bars * beats_per_bar
        
        # Different strategies for different transition lengths
        if bars == 8:  # Quick mix
            timeline = [
                {
                    'beat': 0,
                    'time': 0.0,
                    'action': 'start_deck_b',
                    'description': 'Start playing track B (silent)'
                },
                {
                    'beat': 4,
                    'time': 4 * (bar_length / beats_per_bar),
                    'action': 'eq_low_cut_deck_a_start',
                    'description': 'Start cutting lows on track A'
                },
                {
                    'beat': 8,
                    'time': 8 * (bar_length / beats_per_bar),
                    'action': 'eq_low_introduce_deck_b',
                    'description': 'Introduce lows on track B'
                },
                {
                    'beat': 16,
                    'time': 16 * (bar_length / beats_per_bar),
                    'action': 'crossfader_50_50',
                    'description': 'Crossfader at 50/50'
                },
                {
                    'beat': 24,
                    'time': 24 * (bar_length / beats_per_bar),
                    'action': 'fade_out_deck_a',
                    'description': 'Fade out track A'
                },
                {
                    'beat': 32,
                    'time': 32 * (bar_length / beats_per_bar),
                    'action': 'deck_b_only',
                    'description': 'Track B only playing'
                }
            ]
        
        elif bars == 16:  # Standard mix
            timeline = [
                {
                    'beat': 0,
                    'time': 0.0,
                    'action': 'start_deck_b',
                    'description': 'Start playing track B (silent)'
                },
                {
                    'beat': 8,
                    'time': 8 * (bar_length / beats_per_bar),
                    'action': 'eq_low_cut_deck_a_start',
                    'description': 'Start cutting lows on track A'
                },
                {
                    'beat': 12,
                    'time': 12 * (bar_length / beats_per_bar),
                    'action': 'eq_low_introduce_deck_b',
                    'description': 'Introduce lows on track B'
                },
                {
                    'beat': 32,
                    'time': 32 * (bar_length / beats_per_bar),
                    'action': 'crossfader_50_50',
                    'description': 'Crossfader at 50/50'
                },
                {
                    'beat': 48,
                    'time': 48 * (bar_length / beats_per_bar),
                    'action': 'fade_out_deck_a',
                    'description': 'Fade out track A'
                },
                {
                    'beat': 64,
                    'time': 64 * (bar_length / beats_per_bar),
                    'action': 'deck_b_only',
                    'description': 'Track B only playing'
                }
            ]
        
        else:  # Long mix (32 bars)
            timeline = [
                {
                    'beat': 0,
                    'time': 0.0,
                    'action': 'start_deck_b',
                    'description': 'Start playing track B (silent)'
                },
                {
                    'beat': 16,
                    'time': 16 * (bar_length / beats_per_bar),
                    'action': 'eq_high_introduce_deck_b',
                    'description': 'Introduce highs on track B'
                },
                {
                    'beat': 32,
                    'time': 32 * (bar_length / beats_per_bar),
                    'action': 'eq_mid_introduce_deck_b',
                    'description': 'Introduce mids on track B'
                },
                {
                    'beat': 48,
                    'time': 48 * (bar_length / beats_per_bar),
                    'action': 'eq_low_cut_deck_a_start',
                    'description': 'Start cutting lows on track A'
                },
                {
                    'beat': 64,
                    'time': 64 * (bar_length / beats_per_bar),
                    'action': 'eq_low_introduce_deck_b',
                    'description': 'Introduce lows on track B'
                },
                {
                    'beat': 80,
                    'time': 80 * (bar_length / beats_per_bar),
                    'action': 'crossfader_50_50',
                    'description': 'Crossfader at 50/50'
                },
                {
                    'beat': 96,
                    'time': 96 * (bar_length / beats_per_bar),
                    'action': 'fade_out_deck_a',
                    'description': 'Fade out track A'
                },
                {
                    'beat': 128,
                    'time': 128 * (bar_length / beats_per_bar),
                    'action': 'deck_b_only',
                    'description': 'Track B only playing'
                }
            ]
        
        return timeline
    
    def _determine_mix_strategy(self, track_a: Dict, track_b: Dict) -> Dict:
        """
        Determine mix strategy based on track characteristics
        
        Args:
            track_a: Current track analysis
            track_b: Next track analysis
            
        Returns:
            Mix strategy with recommendations
        """
        bpm_diff = abs(track_a['bpm'] - track_b['bpm'])
        energy_a = track_a.get('energy', 0.5)
        energy_b = track_b.get('energy', 0.5)
        energy_diff = abs(energy_a - energy_b)
        
        # Determine transition type
        if bpm_diff <= 3:
            transition_speed = 'smooth'
            recommended_bars = 16
        elif bpm_diff <= 6:
            transition_speed = 'moderate'
            recommended_bars = 12
        else:
            transition_speed = 'quick'
            recommended_bars = 8
        
        # Determine EQ strategy
        if energy_b > energy_a:
            eq_strategy = 'gradual_energy_increase'
            eq_notes = 'Gradually introduce high-end first, then mids, then bass'
        elif energy_b < energy_a:
            eq_strategy = 'energy_decrease'
            eq_notes = 'Quick bass swap, fade highs slowly'
        else:
            eq_strategy = 'balanced'
            eq_notes = 'Standard EQ swap (lows first, then highs)'
        
        # Effects recommendations
        effects = []
        if bpm_diff > 3:
            effects.append('tempo_sync')
        if energy_diff > 0.2:
            effects.append('reverb_wash')
        
        return {
            'transition_speed': transition_speed,
            'recommended_bars': recommended_bars,
            'bpm_difference': round(bpm_diff, 1),
            'energy_difference': round(energy_diff, 2),
            'eq_strategy': eq_strategy,
            'eq_notes': eq_notes,
            'recommended_effects': effects,
            'confidence': self._calculate_confidence(bpm_diff, energy_diff)
        }
    
    def _calculate_confidence(self, bpm_diff: float, energy_diff: float) -> str:
        """
        Calculate confidence level for transition
        
        Args:
            bpm_diff: BPM difference between tracks
            energy_diff: Energy difference between tracks
            
        Returns:
            Confidence level: 'high', 'medium', or 'low'
        """
        if bpm_diff <= 3 and energy_diff <= 0.15:
            return 'high'
        elif bpm_diff <= 6 and energy_diff <= 0.3:
            return 'medium'
        else:
            return 'low'


if __name__ == "__main__":
    # Quick test
    print("🎧 Transition Planner Test")
    print("=" * 50)
    
    # Create test tracks
    track_a = {
        'file_path': 'track_a.mp3',
        'bpm': 128.0,
        'duration': 300.0,  # 5 minutes
        'energy': 0.75,
        'beats': list(range(0, 300, 2))  # Fake beat positions
    }
    
    track_b = {
        'file_path': 'track_b.mp3',
        'bpm': 126.5,
        'duration': 280.0,
        'energy': 0.78,
        'beats': list(range(0, 280, 2))
    }
    
    # Create planner
    planner = TransitionPlanner()
    
    # Plan transition
    plan = planner.plan_transition(track_a, track_b, transition_type='standard')
    
    # Print plan
    print(f"Track A: {plan['track_a']['file_path']}")
    print(f"  Transition starts at: {plan['track_a']['transition_start']:.1f}s (bar {plan['track_a']['transition_start_bars']})")
    print()
    
    print(f"Track B: {plan['track_b']['file_path']}")
    print(f"  Cue point: {plan['track_b']['cue_point']:.1f}s (bar {plan['track_b']['cue_point_bars']})")
    print()
    
    print(f"Transition:")
    print(f"  Duration: {plan['transition']['duration']:.1f}s ({plan['transition']['duration_bars']} bars)")
    print(f"  Type: {plan['transition']['type']}")
    print()
    
    print(f"Mix Strategy:")
    strategy = plan['timeline']
    for event in strategy:
        print(f"  Beat {event['beat']:3d} ({event['time']:5.1f}s): {event['description']}")
    
    print()
    print("✓ Transition Planner working!")
