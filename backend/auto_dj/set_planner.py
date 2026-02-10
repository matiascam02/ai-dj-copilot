#!/usr/bin/env python3
"""
Set Planner - Visual timeline and roadmap generator
Creates detailed preview of what Auto DJ will do
"""

from typing import List, Dict
from datetime import timedelta


class SetPlanner:
    """Generate visual set plans with detailed timelines"""
    
    def __init__(self, transition_planner):
        self.planner = transition_planner
    
    def build_visual_plan(self, tracks: List[Dict]) -> Dict:
        """
        Build complete visual roadmap of the set
        
        Returns:
            Detailed plan with timeline, actions, effects, duration
        """
        if len(tracks) < 2:
            return {
                'status': 'error',
                'message': 'Need at least 2 tracks for a set'
            }
        
        timeline = []
        total_time = 0.0
        
        # First track
        timeline.append({
            'time': 0.0,
            'time_str': '00:00',
            'action': 'start_set',
            'icon': '▶️',
            'description': f'Start playing: {self._get_track_name(tracks[0])}',
            'track_index': 0,
            'details': {
                'bpm': tracks[0].get('bpm'),
                'key': tracks[0].get('key'),
                'energy': tracks[0].get('energy')
            }
        })
        
        # Build transitions
        for i in range(len(tracks) - 1):
            current_track = tracks[i]
            next_track = tracks[i + 1]
            
            # Get transition plan
            plan = self.planner.plan_transition(current_track, next_track)
            
            if not plan:
                continue
            
            # Add current track duration
            track_duration = current_track.get('duration', 0)
            transition_start = plan['track_a']['transition_start']
            
            # Timeline events for this transition
            transition_events = self._build_transition_timeline(
                plan, 
                total_time,
                i + 1,
                next_track
            )
            
            timeline.extend(transition_events)
            
            # Update total time (subtract overlap)
            total_time += track_duration
            overlap = plan['transition'].get('duration', 30)
            total_time -= overlap
        
        # Add final track
        final_track = tracks[-1]
        total_time += final_track.get('duration', 0)
        
        # Build transitions summary
        transitions_summary = []
        for i in range(len(tracks) - 1):
            plan = self.planner.plan_transition(tracks[i], tracks[i + 1])
            if plan:
                transitions_summary.append({
                    'from': self._get_track_name(tracks[i]),
                    'to': self._get_track_name(tracks[i + 1]),
                    'duration': plan['transition']['duration'],
                    'method': plan['transition']['method'],
                    'compatibility': plan['compatibility'],
                    'bpm_diff': abs(tracks[i].get('bpm', 0) - tracks[i + 1].get('bpm', 0)),
                    'energy_flow': self._get_energy_flow(
                        tracks[i].get('energy', 0.5),
                        tracks[i + 1].get('energy', 0.5)
                    )
                })
        
        return {
            'status': 'ok',
            'tracks': len(tracks),
            'total_duration': total_time,
            'total_duration_str': self._format_duration(total_time),
            'timeline': timeline,
            'transitions': transitions_summary,
            'track_list': [
                {
                    'index': i,
                    'name': self._get_track_name(t),
                    'duration': t.get('duration', 0),
                    'bpm': t.get('bpm'),
                    'key': t.get('key'),
                    'energy': t.get('energy')
                }
                for i, t in enumerate(tracks)
            ]
        }
    
    def _build_transition_timeline(self, plan: Dict, base_time: float, 
                                   next_index: int, next_track: Dict) -> List[Dict]:
        """Build detailed timeline for a single transition"""
        
        events = []
        transition_start = plan['track_a']['transition_start']
        
        # Load next track (60s before transition)
        load_time = base_time + transition_start - 60
        events.append({
            'time': load_time,
            'time_str': self._format_time(load_time),
            'action': 'load_next',
            'icon': '📀',
            'description': f'Load to Deck B: {self._get_track_name(next_track)}',
            'track_index': next_index,
            'details': {
                'deck': 'B',
                'cue_point': plan['track_b']['cue_point']
            }
        })
        
        # Start next track (30s before transition)
        start_time = base_time + transition_start - 30
        events.append({
            'time': start_time,
            'time_str': self._format_time(start_time),
            'action': 'start_next',
            'icon': '▶️',
            'description': 'Start Deck B (silent on crossfader)',
            'track_index': next_index,
            'details': {
                'deck': 'B',
                'crossfader': -1.0
            }
        })
        
        # Transition events
        for event in plan['timeline']:
            event_time = base_time + transition_start + event['time']
            
            icon = self._get_event_icon(event['action'])
            description = event['description']
            
            events.append({
                'time': event_time,
                'time_str': self._format_time(event_time),
                'action': event['action'],
                'icon': icon,
                'description': description,
                'track_index': next_index,
                'details': event
            })
        
        return events
    
    def _get_event_icon(self, action: str) -> str:
        """Get icon for timeline event"""
        icons = {
            'start_deck_b': '▶️',
            'eq_low_cut_deck_a_start': '🎛️',
            'eq_low_introduce_deck_b': '🎛️',
            'eq_high_introduce_deck_b': '🎛️',
            'eq_mid_introduce_deck_b': '🎛️',
            'crossfader_50_50': '🎚️',
            'fade_out_deck_a': '🎚️',
            'deck_b_only': '✅'
        }
        return icons.get(action, '•')
    
    def _get_track_name(self, track: Dict) -> str:
        """Get display name for track"""
        return track.get('title') or track.get('filename') or 'Unknown Track'
    
    def _format_time(self, seconds: float) -> str:
        """Format seconds as MM:SS"""
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration as 'Xm Ys'"""
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins}m {secs}s"
    
    def _get_energy_flow(self, energy_a: float, energy_b: float) -> str:
        """Describe energy transition"""
        diff = energy_b - energy_a
        
        if diff > 0.2:
            return '🔥 Energy UP'
        elif diff < -0.2:
            return '🌊 Energy DOWN'
        else:
            return '➡️ Steady'
    
    def generate_suggestions(self, plan: Dict, current_position: float) -> List[str]:
        """
        Generate smart suggestions based on set plan
        
        Args:
            plan: Set plan from build_visual_plan
            current_position: Current time in set (seconds)
            
        Returns:
            List of suggestion strings
        """
        suggestions = []
        
        # Find current position in timeline
        timeline = plan.get('timeline', [])
        
        # Find next 3 events
        upcoming = [e for e in timeline if e['time'] > current_position][:3]
        
        if not upcoming:
            suggestions.append("Set ending soon!")
            return suggestions
        
        next_event = upcoming[0]
        time_until = next_event['time'] - current_position
        
        # Context-aware suggestions
        if time_until < 10:
            suggestions.append(f"⏰ Coming up: {next_event['description']}")
        
        # Check for manual opportunities
        if 'eq' in next_event['action']:
            suggestions.append("💡 Tip: You can adjust EQ manually for creative flair")
        
        if 'crossfader' in next_event['action']:
            suggestions.append("🎚️ Try moving the crossfader yourself for more control")
        
        # Show next events
        if len(upcoming) > 1:
            suggestions.append(f"Next: {upcoming[1]['description']}")
        
        return suggestions


if __name__ == "__main__":
    print("🎯 Set Planner")
    print("=" * 50)
    print("Generates visual roadmaps for DJ sets")
    print("\nFeatures:")
    print("  • Detailed timeline with icons")
    print("  • Transition preview")
    print("  • Effects timeline")
    print("  • Smart suggestions")
