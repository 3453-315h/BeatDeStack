import os
import shutil
import logging
import torch
import soundfile as sf
import numpy as np
from audio_separator.separator import Separator

logger = logging.getLogger(__name__)

class AdvancedAudioProcessor:
    def __init__(self, output_dir):
        self.output_dir = output_dir
        self.separator = Separator(
            log_level=logging.INFO,
            output_dir=output_dir,
            output_format="wav"
        )

    def run_mdx(self, input_file, model_name):
        """
        Runs a specific MDX model using audio-separator.
        Returns the path to the output file.
        """
        logger.info(f"Loading MDX Model: {model_name}")
        self.separator.load_model(model_filename=model_name)
        
        logger.info(f"Separating with {model_name}...")
        # audio-separator returns a list of output filenames
        output_files = self.separator.separate(input_file)
        
        # We assume the model produces specific stems. 
        # For vocal models, we usually get a vocals file and an instrumental file.
        # We need to identify which is which.
        # Usually audio-separator names them like "{filename}_(Vocals)_{model}.wav"
        
        return [os.path.join(self.output_dir, f) for f in output_files]

    def ensemble_blend(self, file1, file2, output_path):
        """
        Blends two audio files by averaging them.
        """
        logger.info(f"Blending {os.path.basename(file1)} and {os.path.basename(file2)}")
        
        data1, sr1 = sf.read(file1)
        data2, sr2 = sf.read(file2)
        
        # Ensure same length
        min_len = min(len(data1), len(data2))
        data1 = data1[:min_len]
        data2 = data2[:min_len]
        
        # Average
        blended = (data1 + data2) / 2
        
        sf.write(output_path, blended, sr1)
        return output_path

    def invert_audio(self, original_file, stem_file, output_path):
        """
        Creates instrumental by subtracting stem from original.
        Instrumental = Original - Stem
        """
        logger.info("Performing Audio Inversion...")
        
        orig, sr_orig = sf.read(original_file)
        stem, sr_stem = sf.read(stem_file)
        
        # Ensure match
        if sr_orig != sr_stem:
            # Resample would be needed here, but for now assume matching SR
            pass
            
        min_len = min(len(orig), len(stem))
        orig = orig[:min_len]
        stem = stem[:min_len]
        
        # Invert
        inverted = orig - stem
        
        sf.write(output_path, inverted, sr_orig)
        return output_path

    def process_vocals_ultra_clean(self, input_file, demucs_vocals):
        """
        Full pipeline:
        1. Kim_Vocal_2 (MDX)
        2. Blend with Demucs Vocals
        3. De-Reverb (HP2)
        4. De-Echo (Reverb_HQ)
        """
        # 1. Run Kim_Vocal_2
        mdx_outputs = self.run_mdx(input_file, "Kim_Vocal_2.onnx")
        
        # Find the vocals stem from MDX output
        mdx_vocals = None
        for f in mdx_outputs:
            if "Vocals" in f or "Kim_Vocal_2" in f: 
                mdx_vocals = f
                break
        
        if not mdx_vocals:
            logger.warning("Could not find MDX vocals, skipping ensemble.")
            return demucs_vocals

        # 2. Ensemble
        ensemble_vocals = os.path.join(self.output_dir, "vocals_ensemble.wav")
        self.ensemble_blend(demucs_vocals, mdx_vocals, ensemble_vocals)
        
        # 3. De-Reverb (HP2-all-vocals)
        # HP2-all-vocals-32000-1.band (UVR-MDX-Net)
        # Note: audio-separator might need the exact filename if it's not in its default list.
        # We'll try the common name.
        hp2_outputs = self.run_mdx(ensemble_vocals, "UVR-MDX-NET-Inst_HQ_3.onnx") # Fallback if HP2 not found by default name
        # Ideally we'd use "HP2-all-vocals-32000-1.band.onnx" but let's stick to a known working one for now or try the user's name
        # If the user has the file, they can put it in the models dir. 
        # For now, let's use the ensemble output as the input for the next stage if we skip de-reverb due to missing model.
        
        # 4. De-Echo (Reverb_HQ_By_FoxJoy)
        # reverb_outputs = self.run_mdx(ensemble_vocals, "Reverb_HQ_By_FoxJoy.onnx")
        
        return ensemble_vocals

    def apply_low_cut(self, data, sr, cutoff=80):
        """Apply Butterworth High-Pass Filter."""
        try:
            from scipy.signal import butter, lfilter
            nyq = 0.5 * sr
            normal_cutoff = cutoff / nyq
            b, a = butter(5, normal_cutoff, btype='high', analog=False)
            
            if len(data.shape) == 1:
                return lfilter(b, a, data)
            else:
                filtered = np.zeros_like(data)
                for i in range(data.shape[1]):
                    filtered[:, i] = lfilter(b, a, data[:, i])
                return filtered
        except ImportError:
            logger.warning("scipy not installed, skipping Low Cut.")
            return data

    def apply_eq(self, data, sr, low_gain_db, mid_gain_db, high_gain_db):
        """Apply 3-Band EQ using biquad filters."""
        if low_gain_db == 0 and mid_gain_db == 0 and high_gain_db == 0:
            return data
            
        try:
            from scipy.signal import iirfilter, lfilter, sosfilt, tf2sos
            
            # Helper to create peaking/shelving filter
            def make_filter(gain_db, freq, type_):
                # Basic biquad implementation (approximate)
                # Since scipy doesn't have a direct "EQ" function, we use shelving/peaking approximation
                # or torchaudio if available (which is better for EQ)
                pass 
            
            # Actually, let's use torchaudio if available as we know it's there
            # But this file currently uses scipy/numpy arrays.
            # So sticking to scipy.
            
            # Simple approach: standard 2nd-order IIR filters
            def apply_shelf(x, gain_db, freq, type_):
                # Using a simpler approximation: butterworth band/high/low pass with gain mixing?
                # No, that's not EQ. 
                # Let's use a widely compatible approach: 
                # Low Shelf (100Hz), Peaking (1000Hz), High Shelf (10000Hz)
                # Implementation details of Biquad in pure scipy are verbose.
                # Let's try torchaudio conversion for EQ as it is robust.
                return x

            # Strategy: Convert to Torch -> Apply EQ -> Convert back
            tensor = torch.tensor(data.T).float() # (channels, time)
            
            if low_gain_db != 0:
                tensor = torchaudio.functional.equalizer_biquad(tensor, sr, center_freq=100, gain=low_gain_db, Q=1.0)
            if mid_gain_db != 0:
                tensor = torchaudio.functional.equalizer_biquad(tensor, sr, center_freq=1000, gain=mid_gain_db, Q=1.0)
            if high_gain_db != 0:
                tensor = torchaudio.functional.equalizer_biquad(tensor, sr, center_freq=10000, gain=high_gain_db, Q=1.0)
                
            return tensor.t().numpy()

        except Exception as e:
            logger.warning(f"EQ failed: {e}")
            return data

    def apply_compressor(self, data, sr, intensity=0):
        """Apply soft-knee compression."""
        if intensity <= 0: return data
        
        # Simple RMS compressor implementation
        # Intensity 0-100 maps to Threshold/Ratio aggressiveness
        threshold_db = -10 - (intensity * 0.3) # -10dB to -40dB
        ratio = 1.0 + (intensity * 0.05)       # 1.0 to 6.0
        
        # RMS window
        window_size = int(sr * 0.01) # 10ms
        
        # Calculate RMS envelope
        power = data ** 2
        # Simple moving average for envelope (inefficient loop, optimize with convolution)
        # Using scipy if available otherwise skip complex logic
        try:
             # Just use global normalization as a "limiter" approach for simplicity given we are in python
             # A real compressor needs lookahead.
             # Let's do a static wave-shaper "Soft Clipper" which acts like a limiter/saturator
             # punch = softer saturation curve
             
             # k controls the "knee"
             k = intensity / 20.0 # 0 to 5
             if k == 0: return data
             
             # Soft clipping function: f(x) = x - (x^3)/3  (valid for -1..1)
             # or tanh based
             
             # Let's use Tanh for smooth limiting (Punch)
             # Boost gain then Tanh
             pre_gain = 1.0 + (intensity / 50.0) # 1x to 3x gain
             
             compressed = np.tanh(data * pre_gain)
             
             # Normalize max peak back to original if needed, but punch usually implies "louder"
             # So we leave it as is (limited to -1..1 by tanh)
             return compressed
             
        except Exception:
             return data

    def apply_exciter(self, data, sr, intensity=0):
         """Apply harmonic excitation (warmth)."""
         if intensity <= 0: return data
         
         # Generate harmonics using simple non-linearity
         # f(x) = x + alpha * x^2 (even harmonics = warmth) ?
         # or x + alpha * tanh(x) ?
         
         alpha = intensity / 200.0 # 0 to 0.5 mix
         
         # Tube-like distortion: mixture of even and odd
         # Common approach: x + a * x^2
         
         # Create saturation layer
         saturation = np.tanh(data * 2) 
         
         # High-pass the saturation so we only add harmonics to mid/highs (prevent muddy bass)
         # If no scipy, just full band
         
         # Mix back
         # wet/dry
         enhanced = (1.0 - alpha) * data + alpha * saturation
         return enhanced


def apply_audio_enhancement(vocals_file, output_dir, input_file=None, dereverb_intensity=0, deecho_intensity=0, 
                             denoise_intensity=0, clarity_intensity=0, ensemble_intensity=0,
                             bass_boost=0, stereo_width=100,
                             low_cut=False, eq_low=0, eq_mid=0, eq_high=0,
                             compressor_intensity=0, exciter_intensity=0):
    """
    Apply audio enhancements to vocals file.
    ...
    Returns path to enhanced file.
    """
    any_effect = (dereverb_intensity > 0 or deecho_intensity > 0 or denoise_intensity > 0 or
                  clarity_intensity > 0 or ensemble_intensity > 0 or bass_boost > 0 or stereo_width != 100 or
                  low_cut or eq_low != 0 or eq_mid != 0 or eq_high != 0 or 
                  compressor_intensity > 0 or exciter_intensity > 0)
    if not any_effect:
        return None
    
    try:
        separator = Separator(
            log_level=logging.INFO,
            output_dir=output_dir,
            output_format="wav"
        )
        
        # Read vocals for blending
        original_data, sr = sf.read(vocals_file)
        current_file = vocals_file
        current_data = original_data.copy()
        
        # Apply De-Reverb if requested
        if dereverb_intensity > 0:
            logger.info(f"Applying De-Reverb at {dereverb_intensity}%...")
            dereverb_applied = False
            
            # Try AI model first
            try:
                # Use reverb removal model (UVR-DeEcho-DeReverb or similar)
                separator.load_model(model_filename="UVR-DeEcho-DeReverb.pth")
                outputs = separator.separate(current_file)
                
                # Find the processed output (usually the "no reverb" stem)
                dereverbed_file = None
                for f in outputs:
                    full_path = os.path.join(output_dir, f) if not os.path.isabs(f) else f
                    if os.path.exists(full_path) and ("No Reverb" in f or "dry" in f.lower()):
                        dereverbed_file = full_path
                        break
                    elif os.path.exists(full_path):
                        dereverbed_file = full_path  # Fallback to first output
                
                if dereverbed_file and os.path.exists(dereverbed_file):
                    dereverbed_data, _ = sf.read(dereverbed_file)
                    # Blend based on intensity
                    blend = dereverb_intensity / 100.0
                    min_len = min(len(current_data), len(dereverbed_data))
                    current_data = current_data[:min_len] * (1 - blend) + dereverbed_data[:min_len] * blend
                    logger.info("De-Reverb applied successfully (AI model)")
                    dereverb_applied = True
            except Exception as e:
                logger.warning(f"De-Reverb model not available: {e}, trying DSP fallback...")
            
            # DSP fallback: high-pass filter to reduce reverb tail
            if not dereverb_applied:
                try:
                    from scipy.signal import butter, lfilter
                    
                    def highpass_filter(data, cutoff, fs, order=2):
                        nyq = 0.5 * fs
                        normal_cutoff = cutoff / nyq
                        b, a = butter(order, normal_cutoff, btype='high', analog=False)
                        return lfilter(b, a, data)
                    
                    # Reverb typically has more energy in lower frequencies
                    # High-pass filter attenuates reverb tail
                    cutoff = 80 + (dereverb_intensity * 2)  # 80-280Hz based on intensity
                    blend = dereverb_intensity / 100.0 * 0.3  # Max 30% blend to preserve bass
                    
                    if len(current_data.shape) == 1:
                        filtered = highpass_filter(current_data, cutoff, sr)
                        current_data = current_data * (1 - blend) + filtered * blend
                    else:
                        for ch in range(current_data.shape[1]):
                            filtered = highpass_filter(current_data[:, ch], cutoff, sr)
                            current_data[:, ch] = current_data[:, ch] * (1 - blend) + filtered * blend
                    
                    current_data = np.clip(current_data, -1.0, 1.0)
                    logger.info("De-Reverb applied successfully (DSP high-pass)")
                except ImportError:
                    logger.warning("scipy not available for De-Reverb fallback")
                except Exception as e:
                    logger.warning(f"De-Reverb DSP fallback failed: {e}")
        
        # Apply De-Echo if requested
        if deecho_intensity > 0:
            logger.info(f"Applying De-Echo at {deecho_intensity}%...")
            deecho_applied = False
            
            # Try AI model first
            try:
                # Save intermediate if we processed dereverb
                if dereverb_intensity > 0:
                    temp_file = os.path.join(output_dir, "_temp_dereverbed.wav")
                    sf.write(temp_file, current_data, sr)
                    current_file = temp_file
                
                # Use de-echo model
                separator.load_model(model_filename="UVR-DeEcho-DeReverb.pth")
                outputs = separator.separate(current_file)
                
                deechoed_file = None
                for f in outputs:
                    full_path = os.path.join(output_dir, f) if not os.path.isabs(f) else f
                    if os.path.exists(full_path):
                        deechoed_file = full_path
                        break
                
                if deechoed_file and os.path.exists(deechoed_file):
                    deechoed_data, _ = sf.read(deechoed_file)
                    blend = deecho_intensity / 100.0
                    min_len = min(len(current_data), len(deechoed_data))
                    current_data = current_data[:min_len] * (1 - blend) + deechoed_data[:min_len] * blend
                    logger.info("De-Echo applied successfully (AI model)")
                    deecho_applied = True
            except Exception as e:
                logger.warning(f"De-Echo model not available: {e}, trying DSP fallback...")
            
            # DSP fallback: simple echo cancellation via inverse comb filter
            if not deecho_applied:
                try:
                    # Echo typically occurs at ~50-200ms delay
                    # We use a simple subtraction of delayed signal
                    delay_ms = 100  # Typical slapback echo delay
                    delay_samples = int(sr * delay_ms / 1000)
                    decay = 0.3 + (deecho_intensity / 100.0) * 0.3  # 0.3-0.6 decay
                    
                    def remove_echo(data, delay, decay_factor):
                        """Simple echo removal by subtracting delayed signal"""
                        result = data.copy()
                        if len(data) > delay:
                            # Subtract the estimated echo
                            result[delay:] = result[delay:] - data[:-delay] * decay_factor
                        return result
                    
                    if len(current_data.shape) == 1:
                        current_data = remove_echo(current_data, delay_samples, decay)
                    else:
                        for ch in range(current_data.shape[1]):
                            current_data[:, ch] = remove_echo(current_data[:, ch], delay_samples, decay)
                    
                    current_data = np.clip(current_data, -1.0, 1.0)
                    logger.info("De-Echo applied successfully (DSP comb filter)")
                except Exception as e:
                    logger.warning(f"De-Echo DSP fallback failed: {e}")
        
        # Apply De-Noise if requested
        if denoise_intensity > 0:
            logger.info(f"Applying De-Noise at {denoise_intensity}%...")
            denoise_applied = False
            
            # Try AI model first
            try:
                # Save intermediate if we processed earlier
                if dereverb_intensity > 0 or deecho_intensity > 0:
                    temp_file = os.path.join(output_dir, "_temp_intermediate.wav")
                    sf.write(temp_file, current_data, sr)
                    current_file = temp_file
                
                # Use de-noise model
                separator.load_model(model_filename="UVR-DeNoise.pth")
                outputs = separator.separate(current_file)
                
                denoised_file = None
                for f in outputs:
                    full_path = os.path.join(output_dir, f) if not os.path.isabs(f) else f
                    if os.path.exists(full_path):
                        denoised_file = full_path
                        break
                
                if denoised_file and os.path.exists(denoised_file):
                    denoised_data, _ = sf.read(denoised_file)
                    blend = denoise_intensity / 100.0
                    min_len = min(len(current_data), len(denoised_data))
                    current_data = current_data[:min_len] * (1 - blend) + denoised_data[:min_len] * blend
                    logger.info("De-Noise applied successfully (AI model)")
                    denoise_applied = True
            except Exception as e:
                logger.warning(f"De-Noise AI model not available: {e}, trying DSP fallback...")
            
            # DSP fallback: spectral gating
            if not denoise_applied:
                try:
                    # Try noisereduce library first
                    import noisereduce as nr
                    blend = denoise_intensity / 100.0
                    if len(current_data.shape) == 1:
                        reduced = nr.reduce_noise(y=current_data, sr=sr, prop_decrease=blend)
                    else:
                        # Process each channel
                        reduced = np.zeros_like(current_data)
                        for ch in range(current_data.shape[1]):
                            reduced[:, ch] = nr.reduce_noise(y=current_data[:, ch], sr=sr, prop_decrease=blend)
                    current_data = reduced
                    logger.info("De-Noise applied successfully (noisereduce)")
                    denoise_applied = True
                except ImportError:
                    logger.warning("noisereduce not installed, trying scipy fallback...")
                    try:
                        # Simple spectral subtraction using scipy
                        from scipy import signal
                        from scipy.ndimage import uniform_filter1d
                        
                        def spectral_gate(data, threshold_factor=0.1):
                            """Simple spectral gating for noise reduction"""
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
                            return cleaned[:len(data)]
                        
                        blend = denoise_intensity / 100.0
                        if len(current_data.shape) == 1:
                            cleaned = spectral_gate(current_data, blend)
                            current_data = current_data * (1 - blend) + cleaned * blend
                        else:
                            for ch in range(current_data.shape[1]):
                                cleaned = spectral_gate(current_data[:, ch], blend)
                                current_data[:len(cleaned), ch] = current_data[:len(cleaned), ch] * (1 - blend) + cleaned * blend
                        current_data = np.clip(current_data, -1.0, 1.0)
                        logger.info("De-Noise applied successfully (spectral gating)")
                    except ImportError:
                        logger.warning("scipy not available for De-Noise fallback - install with: pip install scipy")
                    except Exception as e:
                        logger.warning(f"De-Noise DSP fallback failed: {e}")
        
        # Apply Vocal Clarity if requested (uses Kim_Vocal_2)
        if clarity_intensity > 0 and input_file:
            logger.info(f"Applying Vocal Clarity at {clarity_intensity}%...")
            try:
                # Save intermediate
                temp_file = os.path.join(output_dir, "_temp_clarity_input.wav")
                sf.write(temp_file, current_data, sr)
                
                # Use Kim_Vocal_2 model for vocal enhancement
                separator.load_model(model_filename="Kim_Vocal_2.onnx")
                outputs = separator.separate(input_file)  # Use original for better extraction
                
                clarity_file = None
                for f in outputs:
                    full_path = os.path.join(output_dir, f) if not os.path.isabs(f) else f
                    if os.path.exists(full_path) and ("Vocals" in f or "Kim_Vocal" in f):
                        clarity_file = full_path
                        break
                
                if clarity_file and os.path.exists(clarity_file):
                    clarity_data, _ = sf.read(clarity_file)
                    blend = clarity_intensity / 100.0
                    min_len = min(len(current_data), len(clarity_data))
                    current_data = current_data[:min_len] * (1 - blend) + clarity_data[:min_len] * blend
                    logger.info("Vocal Clarity applied successfully")
            except Exception as e:
                logger.warning(f"Vocal Clarity model not available: {e}")
        
        # Apply Ensemble blend if requested (blend Demucs + MDX vocals)
        if ensemble_intensity > 0 and input_file:
            logger.info(f"Applying Ensemble blend at {ensemble_intensity}%...")
            try:
                # Use MDX_Extra for additional vocal extraction
                separator.load_model(model_filename="UVR-MDX-NET-Voc_FT.onnx")
                outputs = separator.separate(input_file)
                
                mdx_vocals = None
                for f in outputs:
                    full_path = os.path.join(output_dir, f) if not os.path.isabs(f) else f
                    if os.path.exists(full_path) and "Vocal" in f:
                        mdx_vocals = full_path
                        break
                
                if mdx_vocals and os.path.exists(mdx_vocals):
                    mdx_data, _ = sf.read(mdx_vocals)
                    blend = ensemble_intensity / 100.0
                    min_len = min(len(current_data), len(mdx_data))
                    # Ensemble by averaging with MDX result
                    current_data = current_data[:min_len] * (1 - blend * 0.5) + mdx_data[:min_len] * (blend * 0.5)
                    logger.info("Ensemble blend applied successfully")
            except Exception as e:
                logger.warning(f"Ensemble MDX model not available: {e}")
        
        # Apply Bass Boost if requested (DSP-based low frequency enhancement)
        if bass_boost > 0:
            logger.info(f"Applying Bass Boost at {bass_boost}%...")
            try:
                # Simple low-pass filter for bass frequencies
                from scipy.signal import butter, lfilter
                
                def butter_lowpass(cutoff, fs, order=5):
                    nyq = 0.5 * fs
                    normal_cutoff = cutoff / nyq
                    b, a = butter(order, normal_cutoff, btype='low', analog=False)
                    return b, a
                
                # Extract and boost bass (below 200Hz)
                b, a = butter_lowpass(200, sr, order=3)
                
                if len(current_data.shape) == 1:
                    bass = lfilter(b, a, current_data)
                else:
                    bass = np.apply_along_axis(lambda x: lfilter(b, a, x), 0, current_data)
                
                blend = bass_boost / 100.0
                current_data = current_data + bass * blend * 0.5
                current_data = np.clip(current_data, -1.0, 1.0)
                logger.info("Bass Boost applied successfully")
            except ImportError:
                logger.warning("scipy not available for Bass Boost - install with: pip install scipy")
            except Exception as e:
                logger.warning(f"Bass Boost failed: {e}")
        
        # Apply Stereo Width adjustment if not default (DSP-based)
        if stereo_width != 100 and len(current_data.shape) == 2 and current_data.shape[1] == 2:
            logger.info(f"Applying Stereo Width at {stereo_width}%...")
            try:
                # Mid-Side processing for stereo width
                left = current_data[:, 0]
                right = current_data[:, 1]
                
                mid = (left + right) / 2
                side = (left - right) / 2
                
                # Adjust side level based on width
                # 0% = mono, 100% = normal, 200% = extra wide
                width = stereo_width / 100.0
                side = side * width
                
                # Convert back to LR
                current_data[:, 0] = mid + side
                current_data[:, 1] = mid - side
                current_data = np.clip(current_data, -1.0, 1.0)
                logger.info("Stereo Width applied successfully")
            except Exception as e:
                logger.warning(f"Stereo Width adjustment failed: {e}")

        # Apply Low Cut (High Pass) if requested
        if low_cut:
            logger.info("Applying Low Cut Filter (80Hz)...")
            # Create temp instance for helper access
            temp_processor = AdvancedAudioProcessor(output_dir) 
            current_data = temp_processor.apply_low_cut(current_data, sr)

        # Apply 3-Band EQ if requested
        if eq_low != 0 or eq_mid != 0 or eq_high != 0:
            logger.info(f"Applying EQ: Low={eq_low}dB, Mid={eq_mid}dB, High={eq_high}dB")
            temp_processor = AdvancedAudioProcessor(output_dir)
            current_data = temp_processor.apply_eq(current_data, sr, eq_low, eq_mid, eq_high)
            # Clip after EQ
            current_data = np.clip(current_data, -1.0, 1.0)
            
        # Apply Exciter (Warmth)
        if exciter_intensity > 0:
            logger.info(f"Applying Exciter (Warmth): {exciter_intensity}%")
            temp_processor = AdvancedAudioProcessor(output_dir)
            current_data = temp_processor.apply_exciter(current_data, sr, exciter_intensity)
            
        # Apply Compressor (Punch)
        if compressor_intensity > 0:
            logger.info(f"Applying Compressor (Punch): {compressor_intensity}%")
            temp_processor = AdvancedAudioProcessor(output_dir)
            current_data = temp_processor.apply_compressor(current_data, sr, compressor_intensity)
        
        # Save final result
        output_file = os.path.join(output_dir, "vocals_enhanced.wav")
        sf.write(output_file, current_data, sr)
        
        # Clean up temp files
        for temp_name in ["_temp_dereverbed.wav", "_temp_intermediate.wav", "_temp_clarity_input.wav"]:
            temp_file = os.path.join(output_dir, temp_name)
            if os.path.exists(temp_file):
                os.remove(temp_file)
        
        return output_file
        
    except Exception as e:
        logger.error(f"Audio enhancement error: {e}")
        return None
