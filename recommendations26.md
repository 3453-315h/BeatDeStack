# BeatDeStack — Recommendations (Feb 2026)

## 🏗️ Architecture

1. **Split `splitter.py` (900 lines)** — Extract subprocess worker, model caching, and post-processing into separate modules (`worker.py`, `model_cache.py`, `postprocess.py`). Current file does too much.

2. **Decompose `main_window.py` (1100+ lines)** — Extract queue management, preset management, and preview logic into dedicated controller classes. The God-class pattern makes changes risky.

3. **Add `__init__.py` to `src/core/` and `src/utils/`** — Currently implicit namespace packages. Explicit packages improve IDE support and make imports unambiguous.

4. **Replace global mutable state** — `_separator_cache` and `_current_cached_model` in `splitter.py` are module-level globals. Wrap in a `ModelCache` singleton class with proper thread-safety (`threading.Lock`).

5. **Centralize QSettings keys** — Settings keys are scattered as magic strings (`"output/filename_pattern"`, `"processing/threads"`, etc.). Define them as constants in one place.

---

## 🔒 Security & Robustness

6. **Add hash verification for downloaded models** — `DownloadThread` downloads model files without verifying checksums. Add SHA256 hashes to `AVAILABLE_MODELS` and verify after download.

7. **Add subprocess timeouts** — `Popen` in `SplitterWorker.run()` has no timeout. A hung subprocess blocks the worker forever. Add `watchdog_timer` or periodic `poll()` with max duration.

8. **Sanitize all file paths** — `os.path.join(output_dir, f"{base_name} - Stems")` builds paths from user filenames. Filenames with `..` or special chars could write outside intended directories. Use `pathlib.Path` and validate.

9. **Guard `sys._MEIPASS` access** — Multiple files access `sys._MEIPASS` with bare try/except. Use a centralized helper: `get_base_path()` in `resource_utils.py`.

---

## 🧪 Testing

10. **Add unit tests for core logic** — `dsp.py`, `analysis.py`, `presets.py`, and `preview.py` have pure functions that can be tested without AI models. Create `tests/test_dsp.py`, `tests/test_presets.py`, etc.

11. **Mock the Separator for integration tests** — Current tests in `run_comprehensive_tests.py` require actual Demucs models. Add a mock `Separator` that returns dummy audio for CI testing.

12. **Add a CI pipeline** — No GitHub Actions or similar. Even a basic `python -m py_compile` + unit test run on push would catch regressions.

---

## ⚡ Performance

13. **Lazy-load UI panels** — All 6 settings panels are created at startup. Defer construction until the panel is first expanded (via `QGroupBox.toggled` signal).

14. **Cache BPM/Key analysis results** — `analysis.py` recomputes BPM/key every time. Cache results keyed by file path + modification time.

15. **Use `QThreadPool` instead of raw `QThread`** — `SplitterWorker`, `WaveformLoader`, `DownloadThread` all create standalone threads. A shared thread pool with `QRunnable` would be more efficient and prevent thread explosion in batch mode.

16. **Add `bufsize=-1` for subprocess** — `splitter.py` sets `bufsize=0` (unbuffered). Combined with the now-fixed `readline()`, using `bufsize=-1` (default buffering) would improve throughput.

---

## 🎨 UX Improvements

17. **Add drag-to-reorder in the queue** — `QListWidget` supports drag-and-drop reordering with `setDragDropMode()`. Users expect to reorder processing priority.

18. **Add a "Cancel All" button** — Currently only individual items can be cancelled. Batch users need a way to abort the entire queue.

19. **Show estimated time remaining** — Track processing speed (seconds per file) and display ETA for remaining queue items.

20. **Persist window geometry** — Save `QMainWindow` size/position in QSettings and restore on launch. Users resize for their workflow and expect it to stick.

21. **Add confirmation dialog for destructive actions** — "Clear Queue" and "Delete Preset" should prompt for confirmation.

---

## 📦 Build & Distribution

22. **Complete `requirements.txt`** — Currently lists only 4 packages. Missing: `PyQt6`, `soundfile`, `librosa`, `noisereduce`, `basic-pitch`, `audio-separator`, `scipy`. Add pinned versions.

23. **Add a `pyproject.toml`** — Modern Python packaging standard. Replaces `requirements.txt` + `setup.py` with a single standardized file.

24. **Create cross-platform build scripts** — Only Windows `.spec` files exist. Add macOS and Linux build configurations.

---

## 📝 Documentation

25. **Add architecture diagram** — A Mermaid diagram showing the relationship between `MainWindow` → `SplitterWorker` → `Separator`/`Demucs` → post-processing → output would help new contributors.

26. **Document the model compatibility matrix** — Which models work with which stem counts, which require `audio-separator` vs `demucs.separate`, and GPU requirements per model.

27. **Add developer setup guide** — README covers user installation but not dev environment setup (venv, pre-commit hooks, running tests).

---

## 🧹 Code Cleanup & Minor Fixes

28. **Clean up Dead Code** — `player.py` contains multiple blocks of commented-out, unused code related to an old seek slider, time label, and cursor updates. These should be removed to keep the codebase clean.

29. **Fix Duplicate Comments** — `settings_dialog.py` has a redundant duplicate comment block before the Models Tab creation (`# Models Tab` appears twice consecutively).
