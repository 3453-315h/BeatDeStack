import os
import shutil
import logging
import torch
import torchaudio
import soundfile as sf
import numpy as np
from audio_separator.separator import Separator
from src.utils.logger import logger
import src.core.dsp as dsp
from src.core import constants

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
        
        # Resample stem if sample rates don't match
        if sr_orig != sr_stem:
            logger.info(f"Resampling stem from {sr_stem}Hz to {sr_orig}Hz for inversion...")
            stem_tensor = torch.tensor(stem.T if len(stem.shape) > 1 else stem).float().unsqueeze(0)
            resampler = torchaudio.transforms.Resample(sr_stem, sr_orig)
            stem_resampled = resampler(stem_tensor)
            stem = stem_resampled.squeeze(0).numpy().T if len(stem.shape) > 1 else stem_resampled.squeeze().numpy()
            
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
        1. Secondary Model (Kim_Vocal_2) [Optional - Only if present]
        2. Blend with Primary Vocals
        3. De-Reverb (Roformer > FoxJoy)
        """
        current_vocals = demucs_vocals
        
        # 1. Ensemble Step (Optional)
        # Only run if we have the specific "Kim" model to add flavor/cleaning to Demucs.
        # If the user is already using Roformer as primary, this might be redundant unless Kim is present.
        secondary_model = constants.MODEL_KIM_VOCAL_2
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        models_dir = os.path.join(project_root, "models")
        
        if os.path.exists(os.path.join(models_dir, secondary_model)):
            try:
                mdx_outputs = self.run_mdx(input_file, secondary_model)
                mdx_vocals = None
                for f in mdx_outputs:
                    if "Vocals" in f or "vocal" in f.lower(): 
                        mdx_vocals = f
                        break
                
                if mdx_vocals:
                    ensemble_vocals = os.path.join(self.output_dir, "vocals_ensemble.wav")
                    # Blend 50/50
                    self.ensemble_blend(demucs_vocals, mdx_vocals, ensemble_vocals)
                    current_vocals = ensemble_vocals
            except Exception as e:
                logger.warning(f"Ensemble step failed: {e}. Continuing with primary vocals.")
        
        # 2. De-Reverb Step (The "Clean" part)
        # Prioritize BS-Roformer De-Reverb -> FoxJoy -> Skip
        dereverb_models = [
            "deverb_bs_roformer_8_384dim_10depth.ckpt", # SOTA
            "Reverb_HQ_By_FoxJoy.onnx"                  # Legacy Good
        ]
        
        selected_dereverb = None
        for m in dereverb_models:
            if os.path.exists(os.path.join(models_dir, m)):
                selected_dereverb = m
                break
        
        if selected_dereverb:
            try:
                # Run De-Reverb
                # Roformer/MDX outputs usually: "{input}_{model}.wav" or stems
                outputs = self.run_mdx(current_vocals, selected_dereverb)
                
                # Identify the "Dry" / "No Reverb" stem
                # For Roformer De-Reverb, result is usually just the separated file? Or stems?
                # BS-Roformer De-Reverb typically outputs "no_reverb" path if using audio-separator properly?
                # Let's inspect outputs.
                best_candidate = None
                for f in outputs:
                    lower_f = f.lower()
                    if "no_reverb" in lower_f or "dry" in lower_f:
                        best_candidate = f
                        break
                    # If it's a single output from a de-reverb model, assume it's the result
                    if len(outputs) == 1:
                        best_candidate = f
                        break
                        
                if best_candidate and os.path.exists(best_candidate):
                    current_vocals = best_candidate
                    logger.info(f"Ultra Clean: Applied De-Reverb using {selected_dereverb}")
            except Exception as e:
                 logger.warning(f"Ultra Clean De-Reverb failed: {e}")
                 
        # AGGRESSIVE CLEANUP
        # Scan for temp files and model outputs to delete.
        import time
        cleanup_patterns = constants.CLEANUP_PATTERNS
        
        for f in os.listdir(self.output_dir):
            full_path = os.path.join(self.output_dir, f)
            
            # Skip the current desired result
            if os.path.normpath(full_path) == os.path.normpath(current_vocals):
                continue
                
            # Check pattern
            if any(p in f for p in cleanup_patterns):
                for attempt in range(3):
                    try:
                        if os.path.exists(full_path):
                            os.remove(full_path)
                            logger.info(f"Ultra Clean: Cleaned up temp file {f}")
                        break
                    except PermissionError:
                        time.sleep(0.5)
                    except Exception:
                        break

        return current_vocals


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
        import traceback
        
        # Try to initialize Separator, but it may fail in bundled EXE
        separator = None
        try:
            separator = Separator(
                log_level=logging.INFO,
                output_dir=output_dir,
                output_format="wav"
            )
        except Exception as sep_err:
            logger.warning(f"Separator init failed (AI models unavailable): {sep_err}")
            logger.debug(traceback.format_exc())
            # Continue without AI models - DSP fallbacks will be used
        
        # Read vocals for blending
        original_data, sr = sf.read(vocals_file)
        current_file = vocals_file
        current_data = original_data.copy()
        
        # Apply De-Reverb if requested
        if dereverb_intensity > 0:
            logger.info(f"Applying De-Reverb at {dereverb_intensity}%...")
            dereverb_applied = False
            
            # Try AI model first (only if separator available)
            if separator:
                try:
                    # Use reverb removal model (UVR-DeEcho-DeReverb or similar)
                    separator.load_model(model_filename="UVR-DeEcho-DeReverb.pth")
                    outputs = separator.separate(current_file)
                    
                    logger.info(f"De-Reverb separator outputs: {outputs}")
                    
                    # Find the processed output (usually the "no reverb" stem)
                    dereverbed_file = None
                    for f in outputs:
                        full_path = os.path.join(output_dir, f) if not os.path.isabs(f) else f
                        lower_f = f.lower()
                        
                        # Check for various naming patterns
                        if os.path.exists(full_path):
                            if "no reverb" in lower_f or "no_reverb" in lower_f or "dry" in lower_f:
                                dereverbed_file = full_path
                                logger.info(f"Found de-reverb output (matched pattern): {f}")
                                break
                            elif "reverb" not in lower_f and "echo" not in lower_f:
                                # Not reverb/echo, probably the dry/clean output
                                dereverbed_file = full_path
                                logger.info(f"Found de-reverb output (fallback - not reverb/echo): {f}")
                                break
                    
                    # If still nothing found, use first output
                    if not dereverbed_file and outputs:
                        first_output = outputs[0]
                        full_path = os.path.join(output_dir, first_output) if not os.path.isabs(first_output) else first_output
                        if os.path.exists(full_path):
                            dereverbed_file = full_path
                            logger.info(f"Using first output as de-reverb result: {first_output}")
                    
                    if dereverbed_file and os.path.exists(dereverbed_file):
                        dereverbed_data, _ = sf.read(dereverbed_file)
                        # Blend based on intensity
                        blend = dereverb_intensity / 100.0
                        min_len = min(len(current_data), len(dereverbed_data))
                        current_data = current_data[:min_len] * (1 - blend) + dereverbed_data[:min_len] * blend
                        logger.info(f"De-Reverb applied successfully (AI model, blend={blend:.2f})")
                        dereverb_applied = True
                    else:
                        logger.warning(f"De-Reverb: Could not find valid output file. Outputs were: {outputs}")
                except Exception as e:
                    logger.warning(f"De-Reverb model not available: {e}, trying DSP fallback...")
            
            # DSP fallback: high-pass filter to reduce reverb tail
            if not dereverb_applied:
                try:
                    # Reverb typically has more energy in lower frequencies
                    # High-pass filter attenuates reverb tail
                    cutoff = 80 + (dereverb_intensity * 2)  # 80-280Hz based on intensity
                    blend = dereverb_intensity / 100.0 * 0.3  # Max 30% blend to preserve bass
                    
                    if len(current_data.shape) == 1:
                        filtered = dsp.highpass_filter(current_data, cutoff, sr)
                        current_data = current_data * (1 - blend) + filtered * blend
                    else:
                        for ch in range(current_data.shape[1]):
                            filtered = dsp.highpass_filter(current_data[:, ch], cutoff, sr)
                            current_data[:, ch] = current_data[:, ch] * (1 - blend) + filtered * blend
                    
                    current_data = np.clip(current_data, -1.0, 1.0)
                    logger.info("De-Reverb applied successfully (DSP high-pass)")
                except Exception as e:
                    logger.warning(f"De-Reverb DSP fallback failed: {e}")
        
        # Apply De-Echo if requested
        if deecho_intensity > 0:
            logger.info(f"Applying De-Echo at {deecho_intensity}%...")
            deecho_applied = False
            
            # Try AI model first (only if separator available)
            if separator:
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
                    delay_ms = 100  # Typical slapback echo delay
                    decay = 0.3 + (deecho_intensity / 100.0) * 0.3  # 0.3-0.6 decay
                    
                    if len(current_data.shape) == 1:
                        current_data = dsp.remove_echo(current_data, sr, delay_ms, decay)
                    else:
                        for ch in range(current_data.shape[1]):
                            current_data[:, ch] = dsp.remove_echo(current_data[:, ch], sr, delay_ms, decay)
                    
                    current_data = np.clip(current_data, -1.0, 1.0)
                    logger.info("De-Echo applied successfully (DSP comb filter)")
                except Exception as e:
                    logger.warning(f"De-Echo DSP fallback failed: {e}")
        
        # Apply De-Noise if requested
        if denoise_intensity > 0:
            logger.info(f"Applying De-Noise at {denoise_intensity}%...")
            denoise_applied = False
            
            # Try AI model first (only if separator available)
            if separator:
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
            
            # DSP fallback: spectral gating / noisereduce
            if not denoise_applied:
                try:
                    blend = denoise_intensity / 100.0
                    current_data = dsp.apply_noise_reduction(current_data, sr, blend)
                    
                    current_data = np.clip(current_data, -1.0, 1.0)
                    logger.info("De-Noise applied successfully (DSP)")
                    denoise_applied = True
                except Exception as e:
                    logger.warning(f"De-Noise DSP fallback failed: {e}")
        
        # Apply Vocal Clarity if requested (uses Kim_Vocal_2)
        if clarity_intensity > 0 and input_file:
            logger.info(f"Applying Vocal Clarity at {clarity_intensity}%...")
            clarity_applied = False
            
            # Try AI model first (only if separator available)
            if separator:
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
                        logger.info("Vocal Clarity applied successfully (AI model)")
                        clarity_applied = True
                except Exception as e:
                    logger.warning(f"Vocal Clarity model not available: {e}, trying DSP fallback...")
            
            # DSP Fallback: Presence Boost (2kHz - 6kHz)
            if not clarity_applied:
                try:
                    # Simple presence boost using EQ logic
                    # boost 3kHz by context amount
                    boost_db = clarity_intensity / 10.0 # up to +10dB
                    
                    # Boost High Mids (3-5kHz range)
                    current_data = dsp.apply_eq(current_data, sr, low_gain_db=0, mid_gain_db=boost_db, high_gain_db=boost_db/2)
                    current_data = np.clip(current_data, -1.0, 1.0)
                    logger.info("Vocal Clarity applied successfully (DSP Presence Boost)")
                except Exception as e:
                    logger.warning(f"Vocal Clarity DSP fallback failed: {e}")
        
        # Apply Ensemble blend if requested (blend Demucs + MDX vocals)
        # Note: Ensemble requires separator - skip if unavailable
        if ensemble_intensity > 0 and input_file and separator:
            logger.info(f"Applying Ensemble blend at {ensemble_intensity}%...")
            try:
                # Use MDX_Extra for additional vocal extraction
                separator.load_model(model_filename=constants.MODEL_MDX_VOCAL_FT)
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
                # Extract and boost bass (below 200Hz)
                if len(current_data.shape) == 1:
                    bass = dsp.lowpass_filter(current_data, 200, sr, order=3)
                else:
                    bass = np.zeros_like(current_data)
                    for ch in range(current_data.shape[1]):
                        bass[:, ch] = dsp.lowpass_filter(current_data[:, ch], 200, sr, order=3)
                
                blend = bass_boost / 100.0
                current_data = current_data + bass * blend * 0.5
                current_data = np.clip(current_data, -1.0, 1.0)
                logger.info("Bass Boost applied successfully")
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
            current_data = dsp.highpass_filter(current_data, 80, sr)

        # Apply 3-Band EQ if requested
        if eq_low != 0 or eq_mid != 0 or eq_high != 0:
            logger.info(f"Applying EQ: Low={eq_low}dB, Mid={eq_mid}dB, High={eq_high}dB")
            current_data = dsp.apply_eq(current_data, sr, eq_low, eq_mid, eq_high)
            # Clip after EQ
            current_data = np.clip(current_data, -1.0, 1.0)
            
        # Apply Exciter (Warmth)
        if exciter_intensity > 0:
            logger.info(f"Applying Exciter (Warmth): {exciter_intensity}%")
            current_data = dsp.apply_exciter(current_data, sr, exciter_intensity)
            
        # Apply Compressor (Punch)
        if compressor_intensity > 0:
            logger.info(f"Applying Compressor (Punch): {compressor_intensity}%")
            current_data = dsp.apply_compressor(current_data, sr, compressor_intensity)
        
        # Save final result
        output_file = os.path.join(output_dir, "vocals_enhanced.wav")
        sf.write(output_file, current_data, sr)
        
        # AGGRESSIVE CLEANUP
        # We scan for any leftovers similar to our known patterns. 
        # We also added retry logic for file locks.
        import time
        
        cleanup_patterns = constants.CLEANUP_PATTERNS
        
        for f in os.listdir(output_dir):
            full_path = os.path.join(output_dir, f)
            
            # Skip the output file we just wrote
            if os.path.normpath(full_path) == os.path.normpath(output_file):
                continue
                
            # Check pattern
            if any(p in f for p in cleanup_patterns):
                for attempt in range(3): # Retry 3 times
                    try:
                        if os.path.exists(full_path):
                            os.remove(full_path)
                            logger.info(f"Cleaned up temp file: {f}")
                        break
                    except PermissionError:
                        logger.warning(f"File lock on {f}, retrying cleanup in 0.5s...")
                        time.sleep(0.5)
                    except Exception as e:
                        logger.warning(f"Cleanup error for {f}: {e}")
                        break

        return output_file
        
    except Exception as e:
        logger.error(f"Audio enhancement error: {e}")
        return None
