#!/usr/bin/env python3
"""
Real-Time DJ Advisor - Suggests what to do and when

Provides context-aware suggestions during a DJ set:
- When to start transitions
- What effects to apply
- EQ adjustments
- Loop opportunities
- Energy management
"""

import time
from typing import Dict, List, Optional
from datetime import datetime


class DJAdvisor:
    """Real-time suggestion engine for DJ sets"""
    
    def __init__(self, mixer, queue_manager, transition_planner):
        self.mixer = mixer
        self.queue = queue_manager
        self.planner = transition_planner
        
        # State
        self.current_plan: Optional[Dict] = None
        self.transition_started = False
        self.transition_start_time = None
        self.last_suggestion_time = 0
        
        # Thresholds
        self.transition_warning_time = 32  # Start warning 32s before transition
        self.transition_ready_time = 16   # "Get ready" at 16s before
        
    def update_transition_plan(self, track_a: Dict, track_b: Dict):
        """Update the transition plan for current tracks"""
        self.current_plan = self.planner.plan_transition(track_a, track_b)
        self.transition_started = False
        self.transition_start_time = None
        
    def get_suggestion(self) -> Dict:
        """
        Get current suggestion based on mixer state
        
        Returns suggestion with:
        - message: What to do
        - action: Action type
        - urgency: low/medium/high
        - color: green/yellow/red
        - controls: Suggested control values
        - timing: When this should happen
        """
        now = time.time()
        
        # Get mixer status
        status = self.mixer.get_status()
        deck_a = status['deck_a']
        deck_b = status['deck_b']
        
        # No track playing
        if not deck_a['playing'] and not deck_b['playing']:
            return {
                'message': '🎧 Load a track and press play to start',
                'action': 'idle',
                'urgency': 'low',
                'color': 'gray',
                'controls': {},
                'timing': None
            }
        
        # Only deck B playing (unusual - maybe just started)
        if not deck_a['playing'] and deck_b['playing']:
            return {
                'message': f'▶️ Deck B playing - {deck_b["time_remaining"]:.0f}s remaining',
                'action': 'playing',
                'urgency': 'low',
                'color': 'green',
                'controls': {},
                'timing': None
            }
        
        # Deck A playing - check if we need to transition
        if deck_a['playing']:
            time_remaining = deck_a['time_remaining']
            
            # Check if we have a transition plan
            if self.current_plan is None:
                # No plan yet - check if we should prepare
                if time_remaining < 60:
                    return {
                        'message': f'⚠️ Track ending in {time_remaining:.0f}s - Load next track!',
                        'action': 'load_next',
                        'urgency': 'high',
                        'color': 'red',
                        'controls': {
                            'next_track': self.queue.get_next_track()[0][0] if self.queue.queue else None
                        },
                        'timing': 'now'
                    }
                elif time_remaining < 90:
                    return {
                        'message': f'📋 {time_remaining:.0f}s left - Choose next track',
                        'action': 'prepare',
                        'urgency': 'medium',
                        'color': 'yellow',
                        'controls': {},
                        'timing': 'soon'
                    }
                else:
                    return {
                        'message': f'🎵 Playing smoothly - {time_remaining:.0f}s remaining',
                        'action': 'playing',
                        'urgency': 'low',
                        'color': 'green',
                        'controls': {},
                        'timing': None
                    }
            
            # We have a transition plan - guide through it
            else:
                return self._get_transition_suggestion(deck_a, deck_b)
        
        return {
            'message': '✓ All good',
            'action': 'idle',
            'urgency': 'low',
            'color': 'green',
            'controls': {},
            'timing': None
        }
    
    def _get_transition_suggestion(self, deck_a: Dict, deck_b: Dict) -> Dict:
        """Get suggestion during transition phase"""
        
        current_pos = deck_a['position']
        transition_start = self.current_plan['track_a']['transition_start']
        time_until_transition = transition_start - current_pos
        
        # Far from transition - just monitor
        if time_until_transition > self.transition_warning_time:
            return {
                'message': f'🎵 Cruising - transition in {int(time_until_transition)}s',
                'action': 'playing',
                'urgency': 'low',
                'color': 'green',
                'controls': {},
                'timing': f'{int(time_until_transition)}s'
            }
        
        # Warning phase - prepare for transition
        elif time_until_transition > self.transition_ready_time:
            if not deck_b['loaded']:
                return {
                    'message': f'⚠️ Load Deck B NOW - {int(time_until_transition)}s until transition!',
                    'action': 'load_deck_b',
                    'urgency': 'high',
                    'color': 'red',
                    'controls': {
                        'track': self.current_plan['track_b']['file_path']
                    },
                    'timing': 'now'
                }
            else:
                return {
                    'message': f'🎯 Get ready - cue Deck B to {self.current_plan["track_b"]["cue_point"]:.1f}s',
                    'action': 'cue_deck_b',
                    'urgency': 'medium',
                    'color': 'yellow',
                    'controls': {
                        'deck': 'B',
                        'cue_point': self.current_plan['track_b']['cue_point']
                    },
                    'timing': f'{int(time_until_transition)}s'
                }
        
        # Ready phase - about to start
        elif time_until_transition > 0:
            bars_until = int(time_until_transition / self.current_plan['transition']['bar_length'])
            
            if not deck_b['playing']:
                return {
                    'message': f'⏰ {bars_until} bars - START DECK B (silent)',
                    'action': 'start_deck_b',
                    'urgency': 'high',
                    'color': 'red',
                    'controls': {
                        'deck': 'B',
                        'action': 'play',
                        'volume': 0  # Start silent, on crossfader
                    },
                    'timing': f'{bars_until} bars'
                }
            else:
                return {
                    'message': f'✓ Deck B playing - {bars_until} bars until mix',
                    'action': 'ready',
                    'urgency': 'medium',
                    'color': 'yellow',
                    'controls': {},
                    'timing': f'{bars_until} bars'
                }
        
        # In transition - follow timeline
        else:
            return self._get_timeline_suggestion(current_pos, transition_start)
    
    def _get_timeline_suggestion(self, current_pos: float, transition_start: float) -> Dict:
        """Get suggestion during active transition"""
        
        time_in_transition = current_pos - transition_start
        timeline = self.current_plan['timeline']
        
        # Find current/next event
        current_event = None
        next_event = None
        
        for i, event in enumerate(timeline):
            if event['time'] <= time_in_transition:
                current_event = event
                if i < len(timeline) - 1:
                    next_event = timeline[i + 1]
        
        if current_event is None:
            current_event = timeline[0]
            next_event = timeline[1] if len(timeline) > 1 else None
        
        # Generate suggestion based on current event
        message, controls = self._event_to_suggestion(current_event)
        
        # Add timing for next event
        timing = None
        if next_event:
            time_until_next = next_event['time'] - time_in_transition
            bars_until = int(time_until_next / self.current_plan['transition']['bar_length'])
            timing = f'Next: {bars_until} bars'
        
        return {
            'message': message,
            'action': current_event['action'],
            'urgency': 'high',
            'color': 'red',
            'controls': controls,
            'timing': timing,
            'progress': time_in_transition / self.current_plan['transition']['duration']
        }
    
    def _event_to_suggestion(self, event: Dict) -> tuple:
        """Convert timeline event to suggestion"""
        
        action = event['action']
        
        messages = {
            'start_deck_b': ('▶️ START DECK B', {'deck': 'B', 'play': True}),
            'eq_low_cut_deck_a_start': ('🎛️ CUT BASS Deck A', {'deck': 'A', 'eq_bass': 0.2}),
            'eq_low_introduce_deck_b': ('🎛️ BRING BASS Deck B', {'deck': 'B', 'eq_bass': 1.0}),
            'eq_high_introduce_deck_b': ('🎛️ HIGHS IN Deck B', {'deck': 'B', 'eq_high': 1.0}),
            'eq_mid_introduce_deck_b': ('🎛️ MIDS IN Deck B', {'deck': 'B', 'eq_mid': 1.0}),
            'crossfader_50_50': ('🎚️ CROSSFADER CENTER', {'crossfader': 0.0}),
            'fade_out_deck_a': ('🎚️ FADE OUT Deck A', {'deck': 'A', 'fade_out': True}),
            'deck_b_only': ('✅ DECK B ONLY - Transition complete!', {})
        }
        
        return messages.get(action, (event['description'], {}))
    
    def get_energy_advice(self, current_energy: float, next_energy: float) -> str:
        """Suggest how to handle energy transition"""
        
        diff = next_energy - current_energy
        
        if diff > 0.2:
            return "🔥 Energy UP - Use quick transition, boost highs"
        elif diff < -0.2:
            return "🌊 Energy DOWN - Long blend, add reverb"
        else:
            return "➡️ Similar energy - Standard mix"
    
    def suggest_loop(self, position: float, duration: float, beats: list) -> Optional[Dict]:
        """Suggest loop opportunities"""
        
        # Find 4-bar or 8-bar sections
        # Simplified - in reality, analyze for good loop points
        
        if position < duration * 0.3:
            # Early in track - intro loops
            return {
                'message': '🔁 Good loop point - Try 8-bar loop',
                'start': 16.0,  # Seconds
                'length': 8  # Bars
            }
        
        return None
    
    def get_summary(self) -> str:
        """Get human-readable summary of current state"""
        
        status = self.mixer.get_status()
        
        if status['deck_a']['playing']:
            remaining = status['deck_a']['time_remaining']
            return f"Deck A: {remaining:.0f}s left"
        
        return "Ready to play"


if __name__ == "__main__":
    print("💡 DJ Advisor Test")
    print("=" * 50)
    print("✓ Advisor module loaded")
    print("\nThis module provides real-time suggestions")
    print("Run the full system to see it in action!")
