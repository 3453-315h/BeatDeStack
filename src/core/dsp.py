"""
Digital Signal Processing (DSP) Utilities
Handles audio effects using scipy, numpy, and other libraries.
Design to be robust against missing dependencies.
"""
import numpy as np
from src.utils.logger import logger

# Optional dependencies
try:
    from scipy.signal import butter, lfilter
    from scipy import signal
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    logger.warning("scipy not installed. DSP effects will be limited.")

try:
    import noisereduce as nr
    NOISEREDUCE_AVAILABLE = True
except ImportError:
    NOISEREDUCE_AVAILABLE = False
    logger.debug("noisereduce not installed.")


def highpass_filter(data: np.ndarray, cutoff: float, fs: int, order: int = 5) -> np.ndarray:
    """Apply high-pass butterworth filter."""
    if not SCIPY_AVAILABLE:
        return data
        
    try:
        nyq = 0.5 * fs
        normal_cutoff = cutoff / nyq
        b, a = butter(order, normal_cutoff, btype='high', analog=False)
        return lfilter(b, a, data, axis=0)
    except Exception as e:
        logger.error(f"High-pass filter error: {e}")
        return data


def lowpass_filter(data: np.ndarray, cutoff: float, fs: int, order: int = 5) -> np.ndarray:
    """Apply low-pass butterworth filter."""
    if not SCIPY_AVAILABLE:
        return data
        
    try:
        nyq = 0.5 * fs
        normal_cutoff = cutoff / nyq
        b, a = butter(order, normal_cutoff, btype='low', analog=False)
        return lfilter(b, a, data, axis=0)
    except Exception as e:
        logger.error(f"Low-pass filter error: {e}")
        return data


def remove_echo(data: np.ndarray, sr: int, delay_ms: float = 100.0, decay: float = 0.5) -> np.ndarray:
    """Simple echo removal by subtracting delayed signal (Inverse Comb Filter)."""
    try:
        delay_samples = int(sr * delay_ms / 1000)
        if len(data) > delay_samples:
            result = data.copy()
            # result[delay:] = result[delay:] - data[:-delay] * decay
            # Vectorized subtraction for 1D array
            result[delay_samples:] = result[delay_samples:] - data[:-delay_samples] * decay
            return result
        return data
    except Exception as e:
        logger.error(f"Echo removal error: {e}")
        return data


def spectral_gate(data: np.ndarray, sr: int, threshold_factor: float = 0.1) -> np.ndarray:
    """Simple spectral gating for noise reduction."""
    if not SCIPY_AVAILABLE:
        return data
        
    try:
        # Compute STFT
        f, t, Zxx = signal.stft(data, fs=sr, nperseg=2048)
        
        # Estimate noise floor from quietest parts
        mag = np.abs(Zxx)
        noise_floor = np.percentile(mag, 10, axis=1, keepdims=True)
        
        # Apply gate
        mask = mag > (noise_floor * (1 + threshold_factor * 10))
        Zxx_cleaned = Zxx * mask
        
        # Inverse STFT
        _, cleaned = signal.istft(Zxx_cleaned, fs=sr, nperseg=2048)
        
        # Match length
        if len(cleaned) > len(data):
            cleaned = cleaned[:len(data)]
        elif len(cleaned) < len(data):
            cleaned = np.pad(cleaned, (0, len(data) - len(cleaned)))
            
        return cleaned
    except Exception as e:
        logger.error(f"Spectral gate error: {e}")
        return data


def apply_noise_reduction(data: np.ndarray, sr: int, blend: float = 0.5) -> np.ndarray:
    """Apply noise reduction using noisereduce or fallback to spectral gating."""
    if NOISEREDUCE_AVAILABLE:
        try:
            if len(data.shape) == 1:
                return nr.reduce_noise(y=data, sr=sr, prop_decrease=blend)
            else:
                # Process each channel
                reduced = np.zeros_like(data)
                for ch in range(data.shape[1]):
                    reduced[:, ch] = nr.reduce_noise(y=data[:, ch], sr=sr, prop_decrease=blend)
                return reduced
        except Exception as e:
            logger.warning(f"noisereduce failed: {e}, falling back to spectral gate")
            
    # Fallback
    if len(data.shape) == 1:
        cleaned = spectral_gate(data, sr, blend)
        return data * (1 - blend) + cleaned * blend
    else:
        # Process each channel
        result = data.copy()
        for ch in range(data.shape[1]):
            cleaned = spectral_gate(data[:, ch], sr, blend)
            result[:, ch] = data[:, ch] * (1 - blend) + cleaned * blend
        return result


def apply_eq(data: np.ndarray, sr: int, low_gain_db: float, mid_gain_db: float, high_gain_db: float) -> np.ndarray:
    """Apply 3-Band EQ using torchaudio biquad filters."""
    if low_gain_db == 0 and mid_gain_db == 0 and high_gain_db == 0:
        return data
        
    try:
        import torch
        import torchaudio
        
        # Convert to Torch tensor -> Apply EQ -> Convert back to numpy
        # Handle 1D (time) or 2D (time, channels) inputs appropriately
        original_shape = data.shape
        if len(original_shape) == 1:
            tensor = torch.tensor(data).float().unsqueeze(0) # (1, time)
        else:
            tensor = torch.tensor(data.T).float()  # (channels, time)
        
        if low_gain_db != 0:
            tensor = torchaudio.functional.equalizer_biquad(tensor, sr, center_freq=100, gain=low_gain_db, Q=1.0)
        if mid_gain_db != 0:
            tensor = torchaudio.functional.equalizer_biquad(tensor, sr, center_freq=1000, gain=mid_gain_db, Q=1.0)
        if high_gain_db != 0:
            tensor = torchaudio.functional.equalizer_biquad(tensor, sr, center_freq=10000, gain=high_gain_db, Q=1.0)
            
        result = tensor.numpy()
        
        if len(original_shape) == 1:
            return result.squeeze(0)
        else:
            return result.T
            
    except Exception as e:
        logger.warning(f"EQ failed: {e}")
        return data


def apply_compressor(data: np.ndarray, sr: int, intensity: float = 0) -> np.ndarray:
    """Apply soft-knee compression/limiting (Tanh saturation)."""
    if intensity <= 0: return data
    
    try:
        # Pre-gain based on intensity
        pre_gain = 1.0 + (intensity / 50.0) # 1x to 3x gain
        
        # Soft clipping (Tanh)
        compressed = np.tanh(data * pre_gain)
        
        return compressed
    except Exception as e:
        logger.warning(f"Compressor failed: {e}")
        return data


def apply_exciter(data: np.ndarray, sr: int, intensity: float = 0) -> np.ndarray:
    """Apply harmonic excitation (warmth)."""
    if intensity <= 0: return data
    
    try:
        alpha = intensity / 200.0 # 0 to 0.5 mix
        
        # Create saturation layer
        saturation = np.tanh(data * 2)
        
        # Mix back
        enhanced = (1.0 - alpha) * data + alpha * saturation
        return enhanced
    except Exception as e:
        logger.warning(f"Exciter failed: {e}")
        return data
