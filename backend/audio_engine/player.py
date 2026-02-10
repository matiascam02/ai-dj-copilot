#!/usr/bin/env python3
"""
Audio Player - Real-time 2-deck mixer with effects

Features:
- Dual deck playback
- Crossfader mixing
- Per-deck volume control
- Cue points and loops
- Real-time position tracking
"""

import sounddevice as sd
import soundfile as sf
import numpy as np
import threading
import time
from pathlib import Path
from typing import Optional, Tuple


class AudioDeck:
    """Single DJ deck with playback controls"""
    
    def __init__(self, deck_id: str):
        self.deck_id = deck_id
        self.audio: Optional[np.ndarray] = None
        self.sample_rate = 44100
        self.position = 0
        self.is_playing = False
        self.volume = 1.0
        self.speed = 1.0
        
        # Track info
        self.track_path: Optional[str] = None
        self.duration = 0.0
        
        # Cue points and loops
        self.cue_point = 0
        self.loop_start = None
        self.loop_end = None
        self.loop_enabled = False
        
        # Lock for thread safety
        self.lock = threading.Lock()
        
    def load(self, file_path: str) -> bool:
        """Load audio file into deck"""
        try:
            with self.lock:
                # Read audio file
                audio, sr = sf.read(file_path, always_2d=True)
                
                # Resample if needed (ensure 44.1kHz)
                if sr != self.sample_rate:
                    from scipy import signal
                    num_samples = int(len(audio) * self.sample_rate / sr)
                    audio = signal.resample(audio, num_samples)
                
                self.audio = audio.astype(np.float32)
                self.sample_rate = 44100
                self.position = 0
                self.track_path = file_path
                self.duration = len(audio) / self.sample_rate
                
                print(f"[Deck {self.deck_id}] Loaded: {Path(file_path).name}")
                print(f"  Duration: {self.duration:.1f}s, Samples: {len(audio)}")
                
                return True
                
        except Exception as e:
            print(f"[Deck {self.deck_id}] Error loading {file_path}: {e}")
            return False
    
    def play(self):
        """Start playback"""
        with self.lock:
            if self.audio is not None:
                self.is_playing = True
                print(f"[Deck {self.deck_id}] ▶ Play")
    
    def pause(self):
        """Pause playback"""
        with self.lock:
            self.is_playing = False
            print(f"[Deck {self.deck_id}] ⏸ Pause")
    
    def stop(self):
        """Stop and reset"""
        with self.lock:
            self.is_playing = False
            self.position = 0
            print(f"[Deck {self.deck_id}] ⏹ Stop")
    
    def cue(self, seconds: float):
        """Jump to position in seconds"""
        with self.lock:
            if self.audio is not None:
                self.position = int(seconds * self.sample_rate)
                self.position = max(0, min(self.position, len(self.audio) - 1))
                print(f"[Deck {self.deck_id}] ⏭ Cue to {seconds:.1f}s")
    
    def set_cue_point(self):
        """Set cue point at current position"""
        with self.lock:
            self.cue_point = self.position
            print(f"[Deck {self.deck_id}] 📍 Cue point set at {self.get_position():.1f}s")
    
    def return_to_cue(self):
        """Jump back to cue point"""
        with self.lock:
            self.position = self.cue_point
            print(f"[Deck {self.deck_id}] ↩️ Return to cue")
    
    def set_loop(self, start: float, end: float):
        """Set loop points"""
        with self.lock:
            self.loop_start = int(start * self.sample_rate)
            self.loop_end = int(end * self.sample_rate)
            self.loop_enabled = True
            print(f"[Deck {self.deck_id}] 🔁 Loop set: {start:.1f}s - {end:.1f}s")
    
    def clear_loop(self):
        """Disable loop"""
        with self.lock:
            self.loop_enabled = False
            print(f"[Deck {self.deck_id}] ❌ Loop cleared")
    
    def get_position(self) -> float:
        """Get current position in seconds"""
        with self.lock:
            if self.audio is not None:
                return self.position / self.sample_rate
            return 0.0
    
    def get_progress(self) -> float:
        """Get playback progress (0.0 to 1.0)"""
        with self.lock:
            if self.audio is not None and len(self.audio) > 0:
                return self.position / len(self.audio)
            return 0.0
    
    def get_time_remaining(self) -> float:
        """Get time remaining in seconds"""
        if self.audio is not None:
            return self.duration - self.get_position()
        return 0.0
    
    def get_frame(self, num_samples: int) -> np.ndarray:
        """
        Get next audio frame
        
        Returns:
            Audio samples (num_samples x 2) or zeros if not playing
        """
        with self.lock:
            # Return silence if not playing or no audio loaded
            if not self.is_playing or self.audio is None:
                return np.zeros((num_samples, 2), dtype=np.float32)
            
            # Check if we've reached the end
            if self.position >= len(self.audio):
                self.is_playing = False
                return np.zeros((num_samples, 2), dtype=np.float32)
            
            # Get audio chunk
            end_pos = self.position + num_samples
            
            # Handle loop
            if self.loop_enabled and self.loop_start is not None and self.loop_end is not None:
                if self.position >= self.loop_end:
                    self.position = self.loop_start
                    end_pos = self.position + num_samples
                
                # If chunk crosses loop end, wrap around
                if end_pos > self.loop_end:
                    first_part_len = self.loop_end - self.position
                    second_part_len = num_samples - first_part_len
                    
                    first_part = self.audio[self.position:self.loop_end]
                    second_part = self.audio[self.loop_start:self.loop_start + second_part_len]
                    
                    chunk = np.vstack([first_part, second_part])
                    self.position = self.loop_start + second_part_len
                    
                    return (chunk * self.volume).astype(np.float32)
            
            # Normal playback (no loop)
            if end_pos > len(self.audio):
                # Pad with zeros if we run out
                chunk = self.audio[self.position:]
                padding = np.zeros((num_samples - len(chunk), 2), dtype=np.float32)
                chunk = np.vstack([chunk, padding])
                self.position = len(self.audio)
            else:
                chunk = self.audio[self.position:end_pos]
                self.position = end_pos
            
            # Apply volume
            return (chunk * self.volume).astype(np.float32)


class DJMixer:
    """2-deck DJ mixer with crossfader and master output"""
    
    def __init__(self):
        self.deck_a = AudioDeck('A')
        self.deck_b = AudioDeck('B')
        
        # Mixer controls
        self.crossfader = 0.0  # -1 (A only) to +1 (B only)
        self.master_volume = 0.8
        
        # Audio stream
        self.stream: Optional[sd.OutputStream] = None
        self.is_running = False
        self.sample_rate = 44100
        self.blocksize = 1024
        
        # Metering
        self.peak_a = 0.0
        self.peak_b = 0.0
        self.peak_master = 0.0
        
    def start(self):
        """Start audio output stream"""
        if self.is_running:
            print("Mixer already running")
            return
        
        try:
            self.stream = sd.OutputStream(
                samplerate=self.sample_rate,
                channels=2,
                callback=self._audio_callback,
                blocksize=self.blocksize,
                dtype='float32'
            )
            self.stream.start()
            self.is_running = True
            print("🎛️ Mixer started")
            
        except Exception as e:
            print(f"Error starting mixer: {e}")
            self.is_running = False
    
    def stop(self):
        """Stop audio output"""
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        
        self.is_running = False
        print("🎛️ Mixer stopped")
    
    def set_crossfader(self, value: float):
        """Set crossfader position (-1 to +1)"""
        old_value = self.crossfader
        self.crossfader = max(-1.0, min(1.0, value))
        
        # Debug: Show crossfader change
        if abs(self.crossfader - old_value) > 0.05:  # Only log significant changes
            print(f"🎚️ Crossfader: {self.crossfader:+.2f} (A={self._get_a_level():.2f} B={self._get_b_level():.2f})")
    
    def _get_a_level(self) -> float:
        """Get current deck A level from crossfader"""
        cf_pos = (self.crossfader + 1) / 2
        return float(np.cos(cf_pos * np.pi / 2))
    
    def _get_b_level(self) -> float:
        """Get current deck B level from crossfader"""
        cf_pos = (self.crossfader + 1) / 2
        return float(np.sin(cf_pos * np.pi / 2))
    
    def _audio_callback(self, outdata, frames, time_info, status):
        """
        Real-time audio callback
        
        Called by sounddevice to fill output buffer
        This runs in a high-priority thread!
        """
        if status:
            print(f"Audio callback status: {status}")
        
        try:
            # Get audio from both decks
            a_audio = self.deck_a.get_frame(frames)
            b_audio = self.deck_b.get_frame(frames)
            
            # Calculate crossfader curves
            # -1 to +1 → deck A level / deck B level
            cf_pos = (self.crossfader + 1) / 2  # 0 to 1
            
            # Use constant power crossfade (sounds better)
            a_level = np.cos(cf_pos * np.pi / 2)
            b_level = np.sin(cf_pos * np.pi / 2)
            
            # Mix decks
            mixed = (a_audio * a_level) + (b_audio * b_level)
            
            # Apply master volume
            mixed *= self.master_volume
            
            # Update meters (peak detection)
            self.peak_a = float(np.abs(a_audio).max())
            self.peak_b = float(np.abs(b_audio).max())
            self.peak_master = float(np.abs(mixed).max())
            
            # Soft clipping to prevent harsh distortion
            mixed = np.tanh(mixed)
            
            # Output
            outdata[:] = mixed
            
        except Exception as e:
            print(f"Error in audio callback: {e}")
            outdata[:] = np.zeros((frames, 2), dtype=np.float32)
    
    def get_status(self) -> dict:
        """Get current mixer status"""
        return {
            'deck_a': {
                'loaded': self.deck_a.audio is not None,
                'track': Path(self.deck_a.track_path).name if self.deck_a.track_path else None,
                'playing': self.deck_a.is_playing,
                'position': self.deck_a.get_position(),
                'progress': self.deck_a.get_progress(),
                'time_remaining': self.deck_a.get_time_remaining(),
                'duration': self.deck_a.duration,
                'volume': self.deck_a.volume,
                'peak': self.peak_a,
                'cf_level': self._get_a_level()  # Crossfader level
            },
            'deck_b': {
                'loaded': self.deck_b.audio is not None,
                'track': Path(self.deck_b.track_path).name if self.deck_b.track_path else None,
                'playing': self.deck_b.is_playing,
                'position': self.deck_b.get_position(),
                'progress': self.deck_b.get_progress(),
                'time_remaining': self.deck_b.get_time_remaining(),
                'duration': self.deck_b.duration,
                'volume': self.deck_b.volume,
                'peak': self.peak_b,
                'cf_level': self._get_b_level()  # Crossfader level
            },
            'crossfader': self.crossfader,
            'crossfader_a_level': self._get_a_level(),
            'crossfader_b_level': self._get_b_level(),
            'master_volume': self.master_volume,
            'master_peak': self.peak_master,
            'is_running': self.is_running
        }


if __name__ == "__main__":
    # Quick test
    print("🎧 Audio Player Test")
    print("=" * 50)
    
    mixer = DJMixer()
    mixer.start()
    
    # Load test tracks (if they exist)
    test_dir = Path("data/tracks/test")
    audio_files = list(test_dir.glob("*.mp3"))[:2]
    
    if len(audio_files) >= 2:
        mixer.deck_a.load(str(audio_files[0]))
        mixer.deck_b.load(str(audio_files[1]))
        
        # Play deck A
        mixer.deck_a.play()
        print("\n▶ Playing Deck A for 10 seconds...")
        time.sleep(10)
        
        # Start deck B and crossfade
        print("\n▶ Starting Deck B and crossfading...")
        mixer.deck_b.play()
        
        for i in range(100):
            mixer.set_crossfader(-1 + (i / 50))  # -1 to +1
            time.sleep(0.05)
        
        print("\n✓ Crossfade complete, playing Deck B")
        time.sleep(5)
        
        mixer.stop()
        print("\n✓ Test complete!")
    
    else:
        print("Need at least 2 MP3 files in data/tracks/test/")
        mixer.stop()
