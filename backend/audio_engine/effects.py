#!/usr/bin/env python3
"""
Audio Effects - EQ, filters, reverb, delay

Real-time effects processing for DJ mixing
"""

import numpy as np
from scipy import signal
from collections import deque


class ThreeBandEQ:
    """3-band EQ (Bass, Mid, High)"""
    
    def __init__(self, sample_rate=44100):
        self.sr = sample_rate
        
        # EQ gains (0.0 = kill, 1.0 = neutral, 2.0 = boost)
        self.bass = 1.0    # < 250 Hz
        self.mid = 1.0     # 250 Hz - 4 kHz
        self.high = 1.0    # > 4 kHz
        
        # Filter coefficients
        self._update_filters()
        
        # Filter states (for continuous processing)
        self.bass_zi = None
        self.mid_zi = None
        self.high_zi = None
        
    def _update_filters(self):
        """Create butterworth filters for each band"""
        # Low-pass (bass)
        self.bass_b, self.bass_a = signal.butter(
            4, 250, btype='low', fs=self.sr
        )
        
        # Band-pass (mid)
        self.mid_b, self.mid_a = signal.butter(
            4, [250, 4000], btype='band', fs=self.sr
        )
        
        # High-pass (high)
        self.high_b, self.high_a = signal.butter(
            4, 4000, btype='high', fs=self.sr
        )
    
    def process(self, audio: np.ndarray) -> np.ndarray:
        """
        Apply EQ to audio buffer
        
        Args:
            audio: Audio samples (N x 2)
            
        Returns:
            Processed audio
        """
        if len(audio) == 0:
            return audio
        
        # Initialize filter states if needed
        if self.bass_zi is None:
            self.bass_zi = signal.lfilter_zi(self.bass_b, self.bass_a)
            self.bass_zi = np.tile(self.bass_zi[:, np.newaxis], (1, 2))
            
            self.mid_zi = signal.lfilter_zi(self.mid_b, self.mid_a)
            self.mid_zi = np.tile(self.mid_zi[:, np.newaxis], (1, 2))
            
            self.high_zi = signal.lfilter_zi(self.high_b, self.high_a)
            self.high_zi = np.tile(self.high_zi[:, np.newaxis], (1, 2))
        
        # Process each channel
        output = np.zeros_like(audio)
        
        for ch in range(audio.shape[1]):
            # Split into bands
            bass_band, self.bass_zi[:, ch] = signal.lfilter(
                self.bass_b, self.bass_a, audio[:, ch],
                zi=self.bass_zi[:, ch]
            )
            
            mid_band, self.mid_zi[:, ch] = signal.lfilter(
                self.mid_b, self.mid_a, audio[:, ch],
                zi=self.mid_zi[:, ch]
            )
            
            high_band, self.high_zi[:, ch] = signal.lfilter(
                self.high_b, self.high_a, audio[:, ch],
                zi=self.high_zi[:, ch]
            )
            
            # Apply gains
            bass_band *= self.bass
            mid_band *= self.mid
            high_band *= self.high
            
            # Sum back together
            output[:, ch] = bass_band + mid_band + high_band
        
        return output.astype(np.float32)


class Filter:
    """Sweepable low-pass/high-pass filter"""
    
    def __init__(self, sample_rate=44100):
        self.sr = sample_rate
        self.cutoff = 20000  # Hz
        self.type = 'lowpass'  # or 'highpass'
        self.resonance = 1.0  # Q factor
        
        self.zi = None
        self._update_filter()
        
    def _update_filter(self):
        """Update filter coefficients"""
        try:
            self.b, self.a = signal.butter(
                4,
                self.cutoff,
                btype=self.type,
                fs=self.sr
            )
        except:
            # If cutoff is invalid, use passthrough
            self.b = np.array([1.0])
            self.a = np.array([1.0])
    
    def set_cutoff(self, freq: float):
        """Set filter cutoff frequency"""
        self.cutoff = max(20, min(20000, freq))
        self._update_filter()
        self.zi = None  # Reset state
    
    def set_type(self, filter_type: str):
        """Set filter type ('lowpass' or 'highpass')"""
        self.type = filter_type
        self._update_filter()
        self.zi = None
    
    def process(self, audio: np.ndarray) -> np.ndarray:
        """Apply filter"""
        if len(audio) == 0:
            return audio
        
        # Initialize state
        if self.zi is None:
            self.zi = signal.lfilter_zi(self.b, self.a)
            self.zi = np.tile(self.zi[:, np.newaxis], (1, 2))
        
        # Process each channel
        output = np.zeros_like(audio)
        
        for ch in range(audio.shape[1]):
            output[:, ch], self.zi[:, ch] = signal.lfilter(
                self.b, self.a, audio[:, ch],
                zi=self.zi[:, ch]
            )
        
        return output.astype(np.float32)


class SimpleReverb:
    """Simple delay-based reverb"""
    
    def __init__(self, sample_rate=44100):
        self.sr = sample_rate
        self.wet = 0.0  # 0.0 = dry, 1.0 = full wet
        self.decay = 0.5
        self.room_size = 0.5  # Controls delay times
        
        # Delay lines (circular buffers)
        max_delay = int(0.1 * sample_rate)  # 100ms max
        self.delay_buffer_l = deque([0.0] * max_delay, maxlen=max_delay)
        self.delay_buffer_r = deque([0.0] * max_delay, maxlen=max_delay)
        
    def process(self, audio: np.ndarray) -> np.ndarray:
        """Apply reverb"""
        if len(audio) == 0 or self.wet == 0:
            return audio
        
        output = np.copy(audio)
        
        # Simplified reverb using multiple delays
        delays_ms = [23, 41, 59, 79]  # Prime numbers for natural sound
        
        for delay_ms in delays_ms:
            delay_samples = int(delay_ms * self.sr / 1000 * self.room_size)
            delay_samples = max(1, min(delay_samples, len(self.delay_buffer_l)))
            
            # Create delayed signal
            for i in range(len(audio)):
                # Get delayed samples
                delayed_l = self.delay_buffer_l[-delay_samples] if delay_samples <= len(self.delay_buffer_l) else 0
                delayed_r = self.delay_buffer_r[-delay_samples] if delay_samples <= len(self.delay_buffer_r) else 0
                
                # Add to output
                output[i, 0] += delayed_l * self.decay
                output[i, 1] += delayed_r * self.decay
                
                # Update delay buffers
                self.delay_buffer_l.append(audio[i, 0])
                self.delay_buffer_r.append(audio[i, 1])
        
        # Mix dry and wet
        return ((audio * (1 - self.wet)) + (output * self.wet)).astype(np.float32)


class Echo:
    """Simple echo/delay effect"""
    
    def __init__(self, sample_rate=44100):
        self.sr = sample_rate
        self.delay_time = 0.5  # seconds
        self.feedback = 0.3
        self.wet = 0.0
        
        # Delay buffer
        max_delay = int(2.0 * sample_rate)  # 2 seconds max
        self.buffer = deque([0.0] * max_delay, maxlen=max_delay)
        
    def process(self, audio: np.ndarray) -> np.ndarray:
        """Apply echo"""
        if len(audio) == 0 or self.wet == 0:
            return audio
        
        output = np.copy(audio)
        delay_samples = int(self.delay_time * self.sr)
        
        for i in range(len(audio)):
            # Mono mix for simplicity
            mono = (audio[i, 0] + audio[i, 1]) / 2
            
            # Get delayed sample
            delayed = self.buffer[-delay_samples] if delay_samples <= len(self.buffer) else 0
            
            # Feedback
            new_sample = mono + (delayed * self.feedback)
            self.buffer.append(new_sample)
            
            # Add to output (stereo)
            output[i, 0] += delayed * self.wet
            output[i, 1] += delayed * self.wet
        
        return output.astype(np.float32)


class EffectsChain:
    """Chain multiple effects together"""
    
    def __init__(self, sample_rate=44100):
        self.eq = ThreeBandEQ(sample_rate)
        self.filter = Filter(sample_rate)
        self.reverb = SimpleReverb(sample_rate)
        self.echo = Echo(sample_rate)
        
        # Effect enables
        self.eq_enabled = True
        self.filter_enabled = False
        self.reverb_enabled = False
        self.echo_enabled = False
    
    def process(self, audio: np.ndarray) -> np.ndarray:
        """Process audio through effect chain"""
        if len(audio) == 0:
            return audio
        
        output = audio
        
        if self.eq_enabled:
            output = self.eq.process(output)
        
        if self.filter_enabled:
            output = self.filter.process(output)
        
        if self.reverb_enabled:
            output = self.reverb.process(output)
        
        if self.echo_enabled:
            output = self.echo.process(output)
        
        return output


if __name__ == "__main__":
    # Test effects
    print("🎛️ Effects Test")
    print("=" * 50)
    
    # Generate test tone
    sr = 44100
    duration = 1.0
    t = np.linspace(0, duration, int(sr * duration))
    
    # Mix of frequencies
    audio = np.zeros((len(t), 2))
    audio[:, 0] = (
        np.sin(2 * np.pi * 100 * t) +  # Bass
        np.sin(2 * np.pi * 1000 * t) +  # Mid
        np.sin(2 * np.pi * 5000 * t)    # High
    ) / 3
    audio[:, 1] = audio[:, 0]  # Stereo
    
    # Test EQ
    eq = ThreeBandEQ(sr)
    eq.bass = 2.0  # Boost bass
    eq.high = 0.5  # Cut highs
    
    processed = eq.process(audio)
    print(f"✓ EQ processed {len(processed)} samples")
    
    # Test filter
    filt = Filter(sr)
    filt.set_cutoff(1000)  # Low-pass at 1kHz
    
    processed = filt.process(audio)
    print(f"✓ Filter processed {len(processed)} samples")
    
    # Test reverb
    reverb = SimpleReverb(sr)
    reverb.wet = 0.3
    
    processed = reverb.process(audio)
    print(f"✓ Reverb processed {len(processed)} samples")
    
    print("\n✓ All effects working!")
