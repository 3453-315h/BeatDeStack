
## 🚀 New Features

### High Priority

#### 1. Batch Processing Presets

Complexity: Low | Impact: High

- Save/load processing configurations (model + enhancements + output format)
- Quick-switch between "Vocal Extraction", "Full Band Split", "Karaoke Master" presets
- Files: src/ui/settings_dialog.py, new presets.py

> 💬 Your comments: yes

---

#### 2. Stem Blending/Mixing Export

Complexity: Low-Medium | Impact: High

- Export custom mixes with per-stem volume levels baked in
- Use existing player volume sliders to define the mix
- Add "Export Mix" button to player
- Files: src/ui/player.py, src/core/audio_utils.py

> 💬 Your comments: yes

---

#### 3. BPM & Key Detection

Complexity: Medium | Impact: Medium

- Auto-detect tempo and musical key of input files
- Display in queue item and export to filename/metadata
- Libraries: librosa (already likely installed) or essentia
- Files: New analysis.py, src/ui/main_window.py

> 💬 Your comments: yes

---

### Medium Priority

#### 4. A/B Model Comparison Viewer

Complexity: Medium | Impact: Medium

- Side-by-side comparison of the same stem processed by different models
- Quick toggle between outputs before committing
- Useful for finding the "best" model for specific content
- Files: New comparison_view.py, src/ui/player.py

> 💬 Your comments: no rubbish

---

#### 5. Spectral Visualization (Spectrogram)

Complexity: Medium | Impact: Medium

- Real-time frequency analysis display
- Show before/after comparison for enhancements
- Helps users "see" what de-reverb/de-noise is doing
- Files: New spectrogram.py, src/ui/waveform.py

> 💬 Your comments: yes

---

#### 6. Lyrics Extraction (Whisper Integration)

Complexity: Medium-High | Impact: Medium

- Transcribe vocals to text using OpenAI Whisper
- Export as .lrc (timed lyrics) or .txt
- Optional: word-level timestamps
- Files: New lyrics.py, src/ui/workers.py

> 💬 Your comments: yes

---

### Lower Priority / Future

#### 7. Vocal Quality Score

Complexity: High | Impact: Low-Medium

- AI-based assessment of vocal isolation quality
- Show "bleed score" (0-100%) for each stem
- Requires training a small classifier model
- Files: New quality_scorer.py

> 💬 Your comments: yes

---

#### 8. Cloud Processing Backend

Complexity: High | Impact: High (for CPU-only users)

- Optional offload to cloud GPU for users without capable hardware
- Requires server infrastructure (RunPod, Lambda Labs, etc.)
- Files: New cloud_worker.py, src/ui/settings_dialog.py

> 💬 Your comments: yes

---

## ⚡️ Performance Optimizations

### High Priority

#### 9. Model Hot-Loading (Keep Warm)

Complexity: Low-Medium | Impact: Very High

- Keep the current model loaded in GPU memory between files
- Avoid reloading model weights for each file in batch
- Could reduce batch processing time by 30-50%
- Files: src/core/splitter.py, src/core/model_manager.py

> 💬 Your comments: yes

---

#### 10. ONNX Runtime Conversion

Complexity: Medium | Impact: Very High

- Convert Roformer/MDX models to ONNX format
- 2-3x inference speedup with DirectML/CUDA/CPU
- Better cross-platform GPU support
- Files: New onnx_inference.py, src/core/splitter.py

> 💬 Your comments: yes

---

#### 11. Half-Precision (FP16) Inference

Complexity: Low | Impact: Medium-High

- Use torch.float16 on compatible GPUs
- ~2x memory reduction, faster inference
- May require quality testing for each model
- Files: src/core/splitter.py

> 💬 Your comments: yes

---

### Medium Priority

#### 12. Parallel Stem Export

Complexity: Low | Impact: Medium

- Export WAV/FLAC/MP3 files in parallel threads
- Currently sequential, wastes CPU time
- Use concurrent.futures.ThreadPoolExecutor
- Files: src/core/splitter.py

> 💬 Your comments: yes

---

#### 13. Audio Streaming (Reduce RAM)

Complexity: Medium | Impact: Medium

- Stream audio in chunks instead of loading entire file
- Reduces peak RAM usage for large files
- More complex to implement with current architecture
- Files: src/core/splitter.py, src/core/audio_utils.py

> 💬 Your comments: yes

---

#### 14. GPU Memory Pool Optimization

Complexity: Low | Impact: Low-Medium

- Use torch.cuda.memory.set_per_process_memory_fraction()
- Reduce CUDA memory fragmentation
- Files: src/core/gpu_utils.py

> 💬 Your comments: yes

---

## 🎨 UI/UX Improvements

### High Priority

#### 15. Multi-Stem Waveform Display

Complexity: Medium | Impact: Very High

- Stacked multi-track waveform view (DAW-style)
- See all stems simultaneously with color coding
- Click to solo/mute directly on waveform
- Files: src/ui/waveform.py, src/ui/player.py

> 💬 Your comments: yes and have it's own section one can access via icon left bar menu

--

#### 16. Detailed Progress Phases

Complexity: Low | Impact: High

- Replace generic "Processing..." with specific phases:
  - "Loading model (htdemucs)..."
  - "Separating vocals (45%)..."
  - "Applying de-reverb..."
  - "Exporting stems..."
- Files: src/core/splitter.py, src/ui/main_window.py

> 💬 Your comments: yes

---

#### 17. Keyboard Shortcuts

Complexity: Low | Impact: Medium-High

- Space = Play/Pause
- 1-6 = Toggle Mute for stems
- Shift+1-6 = Solo stems  
- Ctrl+S = Save/Export
- Ctrl+O = Open file
- Files: src/ui/main_window.py, src/ui/player.py

> 💬 Your comments: yes

---

### Medium Priority

#### 18. Consistent Stem Color Coding

Complexity: Low | Impact: Medium

- 🔵 Vocals | 🟢 Drums | 🟠 Bass | 🟣 Other | 🔴 Guitar | 🟡 Piano
- Apply across waveform, player tracks, and queue items
- Files: src/ui/style.py, src/ui/player.py

> 💬 Your comments: yes

---

#### 19. Light/Dark Theme Toggle

Complexity: Medium | Impact: Medium

- Add light theme option
- System-follow mode (match Windows/macOS setting)
- Files: src/ui/style.py, src/ui/settings_dialog.py

> 💬 Your comments: no

---

#### 20. Model Selection Visual Indicators

Complexity: Low | Impact: Medium

- Add icons/badges to model dropdown:
  - ⭐️ Recommended
  - 🚀 Fast
  - 💎 Best Quality
  - 📦 Size (500MB)
- Files: src/core/model_manager.py, panels

> 💬 Your comments: yes

---

#### 21. User-Friendly Error Messages

Complexity: Low | Impact: Medium

- Replace technical errors with actionable solutions:
  - "CUDA out of memory" → "GPU memory full. Try 'Fast' quality mode or reduce batch size."
  - "Model not found" → "Model file missing. Click here to download."
- Files: src/core/splitter.py, src/ui/main_window.py

> 💬 Your comments: yes

---

### Lower Priority

#### 22. First-Run Onboarding Wizard

Complexity: Medium | Impact: Low-Medium

- Welcome screen for new users
- Explain stem modes and model choices
- GPU detection and recommendation
- Files: New onboarding.py

> 💬 Your comments: we can test it out see if its ok

---

#### 23. Queue Multi-Select & Batch Actions

Complexity: Low-Medium | Impact: Medium

- Shift+Click to select multiple queue items
- Right-click menu for batch delete/re-process/export
- Files: src/ui/main_window.py

> 💬 Your comments: yes

---

#### 24. Animated Drop Zone

Complexity: Low | Impact: Low

- Visual feedback when dragging files over the window
- Pulsing border, icon animation
- Files: src/ui/main_window.py

> 💬 Your comments: yes