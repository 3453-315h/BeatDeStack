import os
import shutil
import sys
import subprocess
import json
import torch
import torchaudio
import soundfile as sf
import demucs.separate
from PyQt6.QtCore import QThread, pyqtSignal
from src.utils.logger import logger

try:
    from src.core.advanced_audio import AdvancedAudioProcessor, apply_audio_enhancement
except ImportError:
    AdvancedAudioProcessor = None
    apply_audio_enhancement = None
    logger.warning("AdvancedAudioProcessor not available (audio-separator missing?)")

# Monkeypatch torchaudio to use soundfile directly (Fix for Python 3.14 / torchaudio 2.9.1)
def custom_load(filepath, *args, **kwargs):
    wav, sr = sf.read(filepath)
    wav = torch.tensor(wav).float()
    if wav.ndim == 1:
        wav = wav.unsqueeze(0)
    else:
        wav = wav.t()
    return wav, sr

def custom_save(filepath, src, sample_rate, **kwargs):
    src = src.detach().cpu().t().numpy()
    sf.write(filepath, src, sample_rate)

torchaudio.load = custom_load
torchaudio.save = custom_save

# Default Demucs models that use demucs.separate
DEMUCS_MODELS = ["htdemucs", "htdemucs_ft", "htdemucs_6s", "mdx_extra", "hdemucs_mmi"]

def _is_demucs_model(model_name):
    """Check if model is a Demucs model (uses demucs.separate)."""
    # Demucs models are the defaults or don't have file extensions
    if model_name in DEMUCS_MODELS:
        return True
    # If it has a known extension, it's NOT a Demucs model
    if any(model_name.endswith(ext) for ext in [".onnx", ".pth", ".ckpt", ".yaml"]):
        return False
    # Default to Demucs for unknown model names
    return True

def _run_audio_separator(input_file, model_name, output_dir, **kwargs):
    """Run separation using audio-separator library for non-Demucs models."""
    try:
        from audio_separator.separator import Separator
    except ImportError:
        logger.error("audio-separator not installed. Cannot use non-Demucs models.")
        return []
    
    logger.info(f"Using audio-separator for model: {model_name}")
    
    # Get project models directory
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    models_dir = os.path.join(project_root, "models")
    
    try:
        separator = Separator(
            output_dir=output_dir,
            model_file_dir=models_dir,
            output_format=kwargs.get("format", "WAV"),
            normalization_threshold=kwargs.get("normalization", 0.9)
        )
        separator.load_model(model_name)
        # batch_size is an arg for separate(), not __init__
        output_files = separator.separate(input_file, batch_size=kwargs.get("batch_size", 1))
        logger.info(f"audio-separator produced: {output_files}")
        return output_files if output_files else []
    except Exception as e:
        logger.error(f"audio-separator failed for {model_name}: {e}")
        return []


def separate_audio(input_file, output_dir, stem_count, quality, export_zip, keep_original, **kwargs):
    filename = os.path.basename(input_file)
    base_name = os.path.splitext(filename)[0]
    os.makedirs(output_dir, exist_ok=True)

    # Models to run
    models = [kwargs.get("model", "htdemucs")]
    if kwargs.get("ensemble_enabled", False):
        ens_models = kwargs.get("ensemble_models", [])
        if ens_models:
            models = ens_models
            logger.info(f"Ensemble Mode Enabled: Running models {models}")

    temp_root = os.path.join(output_dir, "temp_ensemble")
    if os.path.exists(temp_root):
        shutil.rmtree(temp_root)
    os.makedirs(temp_root, exist_ok=True)

    # Common options
    shifts = 1
    overlap = 0.25
    segment = 0
    jobs = 0
    clip_mode = "rescale"
    
    if quality == 0: # Fast
        shifts = 0
        overlap = 0.1
    elif quality == 2: # Best
        shifts = 2
        overlap = 0.25

    # Overrides
    if kwargs.get("shifts") is not None: shifts = kwargs["shifts"]
    if kwargs.get("overlap") is not None: overlap = kwargs["overlap"]
    if kwargs.get("segment") is not None: segment = kwargs["segment"]
    if kwargs.get("jobs") is not None: jobs = kwargs["jobs"]
    if kwargs.get("clip_mode"): clip_mode = kwargs["clip_mode"]

    # Track audio-separator outputs separately
    audio_sep_outputs = []
    
    # Run separation for each model
    for model_name in models:
        logger.info(f"Running Model: {model_name}")
        
        if _is_demucs_model(model_name):
            # Use Demucs for default models
            args = [
                "-n", model_name,
                "--shifts", str(shifts),
                "--overlap", str(overlap),
                "--clip-mode", clip_mode,
                "-o", temp_root
            ]
            
            if segment > 0: args.extend(["--segment", str(segment)])
            if jobs > 0: args.extend(["-j", str(jobs)])
            if stem_count == 2: args.append("--two-stems=vocals")
            
            # Format (Intermediate is always WAV/Float32 for precision blending)
            args.append("--float32") 
            args.append("--filename")
            args.append("{track}/{stem}.wav")
            
            # GPU
            from src.core.gpu_utils import get_gpu_info
            _, _, device_type = get_gpu_info()
            if device_type == "cpu": args.extend(["-d", "cpu"])
            elif device_type == "mps": args.extend(["-d", "mps"])
            elif device_type == "directml": args.extend(["-d", "cpu"])
            
            args.append(input_file)
            
            try:
                demucs.separate.main(args)
            except Exception as e:
                logger.error(f"Demucs model {model_name} failed: {e}")
        else:
            # Use audio-separator for ONNX/PTH/CKPT models
            sep_outputs = _run_audio_separator(input_file, model_name, output_dir, **kwargs)
            audio_sep_outputs.extend(sep_outputs)
    
    # If only using audio-separator models (no Demucs), we're done
    if not any(_is_demucs_model(m) for m in models):
        logger.info(f"audio-separator complete. Outputs: {audio_sep_outputs}")
        return
            
    # Blending / Moving Logic (for Demucs models)
    first_model_dir = os.path.join(temp_root, models[0], base_name)
    if not os.path.exists(first_model_dir):
        logger.error("First model failed to produce output.")
        return

    stems = os.listdir(first_model_dir)
    
    # Determining Final format options
    output_format = kwargs.get("format", "WAV").lower()
    bit_depth = kwargs.get("bit_depth", "16-bit")
    
    final_ext = "wav"
    if output_format == "mp3": final_ext = "mp3"
    elif output_format == "flac": final_ext = "flac"
    elif output_format == "ogg": final_ext = "ogg"
    elif output_format == "aiff": final_ext = "aiff"
    
    # Process each stem
    for stem_file in stems:
        if not stem_file.endswith(".wav"): continue
        
        stem_name = os.path.splitext(stem_file)[0]
        
        # Filter based on mode (vocals_only etc)
        mode = kwargs.get("mode", "standard")
        should_keep = True
        if mode == "vocals_only" and "vocals" not in stem_name: should_keep = False
        elif mode == "instrumental" and "no_vocals" not in stem_name: should_keep = False
        elif mode == "drums_only" and "drums" not in stem_name: should_keep = False
        elif mode == "bass_only" and "bass" not in stem_name: should_keep = False
        elif mode == "guitar_only" and "guitar" not in stem_name: should_keep = False
        elif mode == "piano_only" and "piano" not in stem_name: should_keep = False
        
        if not should_keep: continue
        
        # Collect waveforms
        waveforms = []
        for model_name in models:
            p = os.path.join(temp_root, model_name, base_name, stem_file)
            if os.path.exists(p):
                w, sr = torchaudio.load(p) # Loaded as float32 due to args
                waveforms.append(w)
        
        if not waveforms: continue
        
        # Blend (Average)
        min_len = min(w.shape[1] for w in waveforms)
        waveforms = [w[:, :min_len] for w in waveforms]
        stacked = torch.stack(waveforms)
        
        algo = kwargs.get("ensemble_algo", "Average (Mean)")
        current_sr = sr # from load
        
        if "Max" in algo:
            blended = torch.max(stacked, dim=0)[0]
        elif "Min" in algo:
            blended = torch.min(stacked, dim=0)[0]
        else: # Mean
            blended = torch.mean(stacked, dim=0)
            
        # Target Path Construction
        pattern = kwargs.get("filename_pattern", "{stem}")
        # Sanitize pattern to ensure stem is included if checking completeness, 
        # but realistically user might want fixed names? No, must separate stems.
        if "{stem}" not in pattern:
             pattern += "_{stem}"
             
        # Resolve Pattern
        # base_name = Track Name (already defined)
        # stem_name = Stem Type (vocals, drums)
        rel_path = pattern.replace("{track}", base_name).replace("{stem}", stem_name)
        
        # Ensure extension
        dst = os.path.join(output_dir, f"{rel_path}.{final_ext}")
        
        # Create subdirs if pattern contained slashes
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        
        # Resample if needed
        target_sr = kwargs.get("sample_rate", 44100)
        if current_sr != target_sr:
             resampler = torchaudio.transforms.Resample(current_sr, target_sr)
             blended = resampler(blended)
             current_sr = target_sr

        # Apply Manipulation (Pitch Shift & Time Stretch)
        pitch = kwargs.get("pitch_shift", 0)
        speed = kwargs.get("time_stretch", 1.0)
        
        if pitch != 0:
            try:
                # PitchShift expects waveform
                eff = torchaudio.transforms.PitchShift(current_sr, n_steps=pitch)
                blended = eff(blended)
            except Exception as e:
                logger.error(f"Pitch shift failed: {e}")
                
        if speed != 1.0 and abs(speed - 1.0) > 0.01:
            try:
                # TimeStretch requires complex spectrogram
                n_fft = 2048
                stft = torch.stft(blended, n_fft=n_fft, hop_length=None, win_length=None, return_complex=True)
                stretcher = torchaudio.transforms.TimeStretch(hop_length=n_fft//4, n_freq=n_fft//2+1)
                stft_stretched = stretcher(stft, speed)
                # Estimate length
                target_len = int(blended.shape[1] / speed)
                blended = torch.istft(stft_stretched, n_fft=n_fft, length=target_len)
            except Exception as e:
                 logger.error(f"Time stretch failed: {e}")

        # Generate Subtype if needed
        subtype = None
        if final_ext in ['wav', 'flac', 'aiff']:
             if "32" in bit_depth: subtype = "FLOAT"
             elif "24" in bit_depth: subtype = "PCM_24"
             else: subtype = "PCM_16"
        
        # Save using sf.write directly
        src_np = blended.detach().cpu().t().numpy()
        sf.write(dst, src_np, current_sr, subtype=subtype)
        
        # Post-Conversion for MP3 (if needed)
        # sf.write usually creates standard WAV if filename is mp3 but library doesn't support it?
        # Actually sf depends on libsndfile. If enabled, it writes mp3.
        # If not, we might need ffmpeg check.
        # But let's assume if user selected MP3, system supports it or we fallback.
        # Ideally, we write WAV then convert with FFmpeg if we want to be 100% sure of bitrate.
        if final_ext == "mp3":
             # We can use our ffmpeg fallback if we want specific bitrate like 320k
             # Check if sf.write actually wrote output.
             if not os.path.exists(dst) or os.path.getsize(dst) < 100:
                 # Retry by writing WAV then converting
                 temp_wav = dst.replace(".mp3", ".wav")
                 sf.write(temp_wav, src_np, current_sr)
                 subprocess.run(["ffmpeg", "-y", "-i", temp_wav, "-b:a", "320k", dst], 
                               capture_output=True)
                 if os.path.exists(temp_wav): os.remove(temp_wav)

        # Band Splitting (Low/Mid/High)
        if kwargs.get("split_bands", False):
            try:
                # Low (< 300Hz)
                low_stem = torchaudio.functional.lowpass_biquad(blended, current_sr, cutoff_freq=300)
                path_low = dst.replace(f".{final_ext}", f"_Low.{final_ext}")
                src_np = low_stem.detach().cpu().t().numpy()
                sf.write(path_low, src_np, current_sr, subtype=subtype)
                
                # High (> 4000Hz)
                high_stem = torchaudio.functional.highpass_biquad(blended, current_sr, cutoff_freq=4000)
                path_high = dst.replace(f".{final_ext}", f"_High.{final_ext}")
                src_np = high_stem.detach().cpu().t().numpy()
                sf.write(path_high, src_np, current_sr, subtype=subtype)
                
                # Mid (300Hz - 4000Hz)
                # Apply Highpass(300) then Lowpass(4000)
                mid_stem = torchaudio.functional.highpass_biquad(blended, current_sr, cutoff_freq=300)
                mid_stem = torchaudio.functional.lowpass_biquad(mid_stem, current_sr, cutoff_freq=4000)
                path_mid = dst.replace(f".{final_ext}", f"_Mid.{final_ext}")
                src_np = mid_stem.detach().cpu().t().numpy()
                sf.write(path_mid, src_np, current_sr, subtype=subtype)
                
            except Exception as e:
                logger.error(f"Band splitting failed for {stem_name}: {e}")

    # Cleanup Temp
    shutil.rmtree(temp_root, ignore_errors=True)
    
    # Copy Original if requested
    if keep_original:
        try:
            shutil.copy(input_file, os.path.join(output_dir, f"original.{final_ext}"))
        except Exception as e:
            logger.warning(f"Failed to copy original file: {e}")
        
    # No more complex Organize/Filter logic needed as we filtered in loop above.
    # No more Enhancement logic? Wait, enhancement logic should run on the FINAL outputs.
    # Re-add enhancement logic block here
    
    # De-Reverb and De-Echo Processing
    dereverb_intensity = kwargs.get("dereverb", 0)
    deecho_intensity = kwargs.get("deecho", 0)
    denoise_intensity = kwargs.get("denoise", 0)
    clarity_intensity = kwargs.get("clarity", 0)
    ensemble_intensity = kwargs.get("ensemble", 0) # This refers to MDX ensemble
    bass_boost = kwargs.get("bass_boost", 0)
    stereo_width = kwargs.get("stereo_width", 100)
    
    any_enhancement = (dereverb_intensity > 0 or deecho_intensity > 0 or denoise_intensity > 0 or 
                       clarity_intensity > 0 or ensemble_intensity > 0 or bass_boost > 0 or stereo_width != 100)
    
    if any_enhancement and AdvancedAudioProcessor:
        try:
            # Reconstruct vocals file path
            vocals_file = os.path.join(output_dir, f"vocals.{final_ext}")
            if os.path.exists(vocals_file):
                logger.info("Applying Audio Enhancements...")
                apply_audio_enhancement(
                    vocals_file, 
                    output_dir, # writes back to dir
                    input_file=input_file,
                    dereverb_intensity=dereverb_intensity,
                    deecho_intensity=deecho_intensity,
                    denoise_intensity=denoise_intensity,
                    clarity_intensity=clarity_intensity,
                    ensemble_intensity=ensemble_intensity,
                    bass_boost=bass_boost,
                    stereo_width=stereo_width,
                    low_cut=kwargs.get("low_cut", False),
                    eq_low=kwargs.get("eq_low", 0),
                    eq_mid=kwargs.get("eq_mid", 0),
                    eq_high=kwargs.get("eq_high", 0),
                    compressor_intensity=kwargs.get("compressor", 0),
                    exciter_intensity=kwargs.get("exciter", 0)
                )
        except Exception as e:
            logger.error(f"Enhancement failed: {e}")
            
    # Advanced Pipeline (Vocals Only - Ultra Clean & Invert)
    mode = kwargs.get("mode", "standard")
    if mode == "vocals_only" and AdvancedAudioProcessor:
        vocals_file = os.path.join(output_dir, f"vocals.{final_ext}")
        if os.path.exists(vocals_file):
            logger.info("Starting Vocals Only Pipeline (Ultra Clean / Invert)...")
            try:
                processor = AdvancedAudioProcessor(output_dir)
                
                # Ultra Clean
                final_vocals = processor.process_vocals_ultra_clean(input_file, vocals_file)
                if final_vocals and os.path.exists(final_vocals):
                    target_name = f"vocals_ultra_clean.{final_ext}"
                    dest_path = os.path.join(output_dir, target_name)
                    if os.path.exists(dest_path): os.remove(dest_path)
                    shutil.move(final_vocals, dest_path)
                    
                    # Invert
                    if kwargs.get("invert", False):
                         inst_path = os.path.join(output_dir, f"instrumental_inverted.{final_ext}")
                         processor.invert_audio(input_file, dest_path, inst_path)
                         logger.info(f"Created Inverted Instrumental: {inst_path}")
            except Exception as e:
                logger.error(f"Advanced Pipeline failed: {e}")

    # Zip if requested
    if export_zip:
        shutil.make_archive(output_dir, 'zip', output_dir)

class SplitterWorker(QThread):
    progress_updated = pyqtSignal(str, int, str) # filename, progress, status
    finished = pyqtSignal(str) # filename
    error_occurred = pyqtSignal(str, str) # filename, error message
    log_message = pyqtSignal(str) # log text for GUI display

    def __init__(self, file_path, options):
        super().__init__()
        self.file_path = file_path
        self.options = options
        self.process = None
        self.is_cancelled = False

    def run(self):
        filename = os.path.basename(self.file_path)
        logger.info(f"Starting processing for {filename} with options: {self.options}")
        
        try:
            base_name = os.path.splitext(filename)[0]
            output_dir = os.path.join(os.path.dirname(self.file_path), f"{base_name} - Stems")
            
            # Reconstruct config dict for subprocess
            config = {
                "input_file": self.file_path,
                "output_dir": output_dir,
                "stem_count": self.options.get("stem_count", 4),
                "quality": self.options.get("quality", 2),
                "export_zip": self.options.get("export_zip", False),
                "keep_original": self.options.get("keep_original", True),
                "format": self.options.get("format", "WAV"),
                "sample_rate": self.options.get("sample_rate", 44100),
                "bit_depth": self.options.get("bit_depth", "16-bit"),
                "mode": self.options.get("mode", "standard"),
                "dereverb": self.options.get("dereverb", 0),
                "deecho": self.options.get("deecho", 0),
                "denoise": self.options.get("denoise", 0),
                "clarity": self.options.get("clarity", 0),
                "ensemble": self.options.get("ensemble", 0),
                "bass_boost": self.options.get("bass_boost", 0),
                "stereo_width": self.options.get("stereo_width", 100),
                "low_cut": self.options.get("low_cut", False),
                "eq_low": self.options.get("eq_low", 0),
                "eq_mid": self.options.get("eq_mid", 0),
                "eq_high": self.options.get("eq_high", 0),
                "compressor": self.options.get("compressor", 0),
                "exciter": self.options.get("exciter", 0),
                "model": self.options.get("model", "htdemucs"),
                "shifts": self.options.get("shifts", 1),
                "overlap": self.options.get("overlap", 0.25),
                "segment": self.options.get("segment", 0),
                "jobs": self.options.get("jobs", 0),
                "batch_size": self.options.get("batch_size", 1),
                "normalization": self.options.get("normalization", 0.9),
                "clip_mode": self.options.get("clip_mode", "rescale"),
                
                # New Ensemble Args
                "ensemble_enabled": self.options.get("ensemble_enabled", False),
                "ensemble_models": self.options.get("ensemble_models", []),
                "ensemble_algo": self.options.get("ensemble_algo", "Average (Mean)")
            }
            
            config_json = json.dumps(config)
            
            cmd = [sys.executable, "-u", "main.py", "--worker", config_json]
            if getattr(sys, 'frozen', False):
                cmd = [sys.executable, "--worker", config_json]
            
            self.progress_updated.emit(filename, 10, "Starting Worker...")
            
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            env = os.environ.copy()
            env["PYTHONUNBUFFERED"] = "1"
            
            script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            rocm_bin = os.path.join(script_dir, "rocm_runtime", "bin")
            rocm_lib = os.path.join(script_dir, "rocm_runtime", "lib")
            
            venv_site = os.path.dirname(os.path.dirname(sys.executable))
            if "site-packages" not in venv_site:
                venv_site = os.path.join(venv_site, "Lib", "site-packages")
            rocm_sdk_bin = os.path.join(venv_site, "_rocm_sdk_core", "bin")
            rocm_sdk_lib = os.path.join(venv_site, "_rocm_sdk_libraries_custom", "bin")
            
            extra_paths = []
            for p in [rocm_bin, rocm_lib, rocm_sdk_bin, rocm_sdk_lib]:
                if os.path.exists(p):
                    extra_paths.append(p)
            if extra_paths:
                env["PATH"] = os.pathsep.join(extra_paths) + os.pathsep + env.get("PATH", "")
                env["HIP_VISIBLE_DEVICES"] = "1"
            
            self.process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT,
                text=False,
                startupinfo=startupinfo,
                bufsize=0,
                env=env
            )
            
            self.progress_updated.emit(filename, 20, "Separating...")
            
            buffer = b""
            while True:
                if self.is_cancelled: break
                
                chunk = self.process.stdout.read(1)
                if not chunk and self.process.poll() is not None: break
                
                if chunk:
                    buffer += chunk
                    if chunk in (b'\n', b'\r'):
                        try:
                            line = buffer.decode('utf-8', errors='replace').strip()
                        except Exception:
                            line = ""
                        buffer = b""
                        
                        if line:
                            if "%" in line and "|" in line:
                                try:
                                    parts = line.split('%')[0].split()
                                    if parts:
                                        pct = int(parts[-1])
                                        total_progress = 20 + int(pct * 0.7)
                                        self.progress_updated.emit(filename, total_progress, f"Separating: {pct}%")
                                except Exception:
                                    pass
                            
                            is_progress_bar = "%" in line and "|" in line
                            if not is_progress_bar:
                                logger.info(f"[Worker] {line}")
                                self.log_message.emit(f"[Worker] {line}")
                                if "Separating" in line:
                                    self.progress_updated.emit(filename, 20, "Separating...")
                                elif "Loading" in line:
                                    self.progress_updated.emit(filename, 10, "Loading Models...")
            
            if self.is_cancelled: return

            return_code = self.process.poll()
            if return_code != 0:
                raise Exception(f"Worker failed with code {return_code}")
            
            self.progress_updated.emit(filename, 100, "Done")
            self.finished.emit(filename)
            
        except Exception as e:
            if not self.is_cancelled:
                logger.error(f"Error processing {filename}: {e}")
                self.error_occurred.emit(filename, str(e))

    def terminate(self):
        self.is_cancelled = True
        if self.process:
            try:
                self.process.kill()
            except Exception:
                pass
