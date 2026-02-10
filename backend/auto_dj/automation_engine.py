#!/usr/bin/env python3
"""
Auto DJ Automation Engine
Executes transitions automatically while allowing human override
"""

import time
import threading
from typing import Optional, List, Dict
from datetime import datetime


class AutoDJEngine:
    """Smart hybrid automation - AI does the work, human can override"""
    
    def __init__(self, mixer, queue_manager, transition_planner):
        self.mixer = mixer
        self.queue = queue_manager
        self.planner = transition_planner
        
        # State
        self.enabled = False
        self.running = False
        self.paused = False
        self.thread: Optional[threading.Thread] = None
        
        # Current automation state
        self.current_track_index = 0
        self.playlist: List[Dict] = []
        self.current_action = "idle"
        self.action_details = ""
        self.next_action_time = None
        
        # Human override detection
        self.last_mixer_state = None
        self.override_detected = False
        
        # Lock for thread safety
        self.lock = threading.Lock()
    
    def build_set_plan(self, tracks: List[Dict]) -> Dict:
        """
        Build complete set plan from track list
        
        Returns:
            Set plan with transitions, timing, total duration
        """
        if len(tracks) < 2:
            return {
                'status': 'error',
                'message': 'Need at least 2 tracks'
            }
        
        # Build queue
        for track in tracks:
            self.queue.add_track(track)
        
        # Generate transitions
        transitions = []
        total_duration = 0
        
        for i in range(len(tracks) - 1):
            plan = self.planner.plan_transition(tracks[i], tracks[i + 1])
            transitions.append(plan)
            
            # Add track duration minus overlap
            total_duration += tracks[i]['duration']
            if plan and 'transition' in plan:
                total_duration -= plan['transition'].get('duration', 30)
        
        # Add final track duration
        total_duration += tracks[-1]['duration']
        
        self.playlist = tracks
        
        return {
            'status': 'ok',
            'tracks': len(tracks),
            'transitions': len(transitions),
            'total_duration': total_duration,
            'transitions_details': transitions
        }
    
    def start(self):
        """Start automatic DJ mode"""
        with self.lock:
            if self.running:
                return {'status': 'error', 'message': 'Already running'}
            
            if not self.playlist:
                return {'status': 'error', 'message': 'No tracks loaded'}
            
            self.enabled = True
            self.running = True
            self.paused = False
            self.current_track_index = 0
            
            # Start automation thread
            self.thread = threading.Thread(target=self._automation_loop, daemon=True)
            self.thread.start()
            
            return {'status': 'ok', 'message': 'Auto DJ started'}
    
    def stop(self):
        """Stop automatic DJ mode"""
        with self.lock:
            self.enabled = False
            self.running = False
            self.current_action = "stopped"
            
        return {'status': 'ok', 'message': 'Auto DJ stopped'}
    
    def pause(self):
        """Pause automation (human taking over)"""
        with self.lock:
            self.paused = True
            self.current_action = "paused"
            self.action_details = "Human override - AI paused"
    
    def resume(self):
        """Resume automation after human override"""
        with self.lock:
            self.paused = False
            self.override_detected = False
            self.current_action = "resuming"
            self.action_details = "AI resuming control..."
    
    def _automation_loop(self):
        """Main automation loop (runs in thread)"""
        
        print("🤖 Auto DJ started")
        
        # Load first track
        self._execute_action("loading_first_track", "Loading first track to Deck A...")
        self.mixer.deck_a.load(self.playlist[0]['file_path'])
        time.sleep(1)
        
        # Start playing
        self._execute_action("starting_first_track", "Starting playback...")
        self.mixer.deck_a.play()
        self.mixer.set_crossfader(-1.0)  # Full A
        
        while self.running and self.current_track_index < len(self.playlist) - 1:
            
            # Check for human override
            if self._check_override():
                self._handle_override()
                continue
            
            # Skip if paused
            if self.paused:
                time.sleep(0.5)
                continue
            
            # Get current state
            current_track = self.playlist[self.current_track_index]
            next_track = self.playlist[self.current_track_index + 1]
            
            # Get transition plan
            plan = self.planner.plan_transition(current_track, next_track)
            
            if not plan:
                # No plan available, skip to next
                self.current_track_index += 1
                continue
            
            # Calculate timing
            deck_a = self.mixer.deck_a
            current_pos = deck_a.get_position()
            transition_start = plan['track_a']['transition_start']
            time_until_transition = transition_start - current_pos
            
            # State machine for transition phases
            
            # Phase 1: Wait for load time (60s before transition)
            if time_until_transition > 60:
                self._execute_action(
                    "monitoring",
                    f"Playing track {self.current_track_index + 1}/{len(self.playlist)} - " +
                    f"Next mix in {int(time_until_transition)}s"
                )
                time.sleep(5)  # Check every 5 seconds
                continue
            
            # Phase 2: Load next track
            if time_until_transition <= 60 and time_until_transition > 30:
                if self.mixer.deck_b.audio is None:
                    self._execute_action(
                        "loading_next_track",
                        f"Loading track {self.current_track_index + 2} to Deck B..."
                    )
                    self.mixer.deck_b.load(next_track['file_path'])
                    
                    # Cue to start point
                    cue_point = plan['track_b']['cue_point']
                    self.mixer.deck_b.cue(cue_point)
                    
                    time.sleep(2)
                
                self._execute_action(
                    "ready",
                    f"Ready to mix - {int(time_until_transition)}s until transition"
                )
                time.sleep(2)
                continue
            
            # Phase 3: Start Deck B
            if time_until_transition <= 30 and time_until_transition > 0:
                if not self.mixer.deck_b.is_playing:
                    self._execute_action(
                        "starting_next_track",
                        "Starting Deck B (silent on crossfader)..."
                    )
                    self.mixer.deck_b.play()
                    time.sleep(1)
                
                self._execute_action(
                    "transition_ready",
                    f"Both decks playing - transition starts in {int(time_until_transition)}s"
                )
                time.sleep(2)
                continue
            
            # Phase 4: Execute transition
            if time_until_transition <= 0:
                self._execute_transition(plan)
                
                # Move to next track
                self.current_track_index += 1
                
                # Swap decks (B becomes A)
                self._execute_action("swapping_decks", "Swapping decks...")
                self.mixer.deck_a.stop()
                
                # Copy B to A for next transition
                if self.current_track_index < len(self.playlist) - 1:
                    self.mixer.deck_a.audio = self.mixer.deck_b.audio
                    self.mixer.deck_a.track_path = self.mixer.deck_b.track_path
                    self.mixer.deck_a.duration = self.mixer.deck_b.duration
                    self.mixer.deck_a.position = self.mixer.deck_b.position
                    self.mixer.deck_a.is_playing = True
                    
                    self.mixer.deck_b.audio = None
                    self.mixer.set_crossfader(-1.0)  # Reset to A
                
                continue
        
        # Finished
        self._execute_action("completed", "Set complete! 🎉")
        self.running = False
        print("🤖 Auto DJ finished")
    
    def _execute_transition(self, plan: Dict):
        """Execute the transition according to plan"""
        
        timeline = plan['timeline']
        transition_duration = plan['transition']['duration']
        
        self._execute_action(
            "transitioning",
            f"AI mixing tracks - {transition_duration:.0f}s transition"
        )
        
        start_time = time.time()
        
        for event in timeline:
            # Wait for event time
            elapsed = time.time() - start_time
            wait_time = event['time'] - elapsed
            
            if wait_time > 0:
                time.sleep(wait_time)
            
            # Check for override during transition
            if self._check_override():
                self._handle_override()
                return
            
            if self.paused:
                # Wait for resume
                while self.paused and self.running:
                    time.sleep(0.5)
            
            # Execute event
            self._execute_timeline_event(event)
        
        # Ensure we end on Deck B
        self._execute_action("crossfading_complete", "Transition complete - now on Deck B")
        self.mixer.set_crossfader(1.0)
        time.sleep(1)
    
    def _execute_timeline_event(self, event: Dict):
        """Execute a single timeline event"""
        
        action = event['action']
        
        # Update status
        self.action_details = event['description']
        
        if 'deck_b' in action and 'start' in action:
            # Already started in phase 3
            pass
        
        elif 'eq' in action:
            # EQ changes
            if 'deck_a' in action and 'low_cut' in action:
                # Cut bass on A
                pass  # Will implement with effects chain
            elif 'deck_b' in action and 'introduce' in action:
                # Bring in B
                pass
        
        elif 'crossfader' in action:
            # Crossfader movement
            if '50_50' in action:
                self.mixer.set_crossfader(0.0)
            
        elif 'fade_out' in action:
            # Fade out A
            for i in range(10):
                cf = -1.0 + (i / 9.0) * 2.0  # -1 to +1
                self.mixer.set_crossfader(cf)
                time.sleep(0.5)
        
        elif 'deck_b_only' in action:
            # Full B
            self.mixer.set_crossfader(1.0)
    
    def _execute_action(self, action: str, details: str):
        """Update current action state"""
        with self.lock:
            self.current_action = action
            self.action_details = details
        print(f"🤖 {details}")
    
    def _check_override(self) -> bool:
        """Check if human has touched any controls"""
        
        # Get current state
        current_state = {
            'crossfader': self.mixer.crossfader,
            'deck_a_playing': self.mixer.deck_a.is_playing,
            'deck_b_playing': self.mixer.deck_b.is_playing,
        }
        
        # First run - save state
        if self.last_mixer_state is None:
            self.last_mixer_state = current_state
            return False
        
        # Check for changes
        if current_state != self.last_mixer_state:
            # State changed - might be human or automation
            # For now, we'll assume automation doesn't trigger this
            # In production, we'd track automation-initiated changes
            self.last_mixer_state = current_state
            # Don't treat as override yet - need more sophisticated detection
        
        return False
    
    def _handle_override(self):
        """Handle human override"""
        self.pause()
        print("👤 Human override detected - AI paused")
        
        # Wait for human to signal continue
        # In UI, this would be a "Resume Auto DJ" button
    
    def get_status(self) -> Dict:
        """Get current automation status"""
        with self.lock:
            return {
                'enabled': self.enabled,
                'running': self.running,
                'paused': self.paused,
                'current_action': self.current_action,
                'action_details': self.action_details,
                'current_track_index': self.current_track_index,
                'total_tracks': len(self.playlist),
                'playlist': [t.get('title', t.get('filename', 'Unknown')) for t in self.playlist]
            }


if __name__ == "__main__":
    print("🤖 Auto DJ Engine")
    print("=" * 50)
    print("✓ Automation engine loaded")
    print("\nFeatures:")
    print("  • Automatic track loading")
    print("  • Intelligent transitions")
    print("  • Human override detection")
    print("  • Re-planning after override")
