# BeatDeStack - Issues To Fix

> Code review performed 2026-02-13. Organized by severity.

---

## 🔴 Critical Bugs

### 1. `crash_handler` — Parameter Shadows `traceback` Module (main.py:19-24)
The parameter name `traceback` shadows the `traceback` module imported on line 20. When `tb.format_exception(exctype, value, traceback)` is called, it uses the parameter correctly, but it's fragile and confusing. Renaming the parameter to `tb_obj` would be safer and clearer.

### 2. `_setup_shortcuts` Called Twice (main_window.py:132, 259)
`_setup_shortcuts()` is called in `__init__` (line 132) and again inside `_setup_sidebar()` (line 259). This registers **all keyboard shortcuts twice** — causing duplicate handler invocations (double play/pause, double file dialogs, etc.).

### 3. Duplicate `_setup_shortcuts` Method Definitions (main_window.py:134 vs 940)
Two entirely different `_setup_shortcuts()` methods exist. The second definition (line 940) silently overrides the first (line 134). The first version registers Space/Escape/number keys for stem muting; the second registers Ctrl+O/Ctrl+,/Ctrl+Enter. **One set of shortcuts is completely lost.**

### 4. Duplicate `_on_queue_item_clicked` Method (main_window.py:547 vs 1036)
Two conflicting implementations exist. The second (line 1036) overrides the first (line 547). The first loads input waveform on click; the second loads stems only on "Done" items. The first version's behavior is silently lost.

### 5. `create_preview_slice` Signature Mismatch (main_window.py:844 vs preview.py:6)
`start_preview()` calls `create_preview_slice(file_path, temp_slice_path, duration=duration, start_time=start_time)` but `preview.py` defines `create_preview_slice(input_path, output_path, duration=30.0)` — **no `start_time` parameter exists**. The start_time value is silently ignored, always slicing from the middle.

### 6. Duplicate `if not stem_dict: return` Block (player.py:255-261)
Lines 255-256 and 260-261 are exact duplicates. The `first = True` assignment and stem creation loop on lines 264+ only executes if it passes two redundant empty checks. No functional harm, but indicates copy-paste error and the duplicate block should be removed.

### 7. `ensemble_blend` Ignores Sample Rate Mismatch (advanced_audio.py:47-58)
`sr2` is read from `file2` but never used. If the two files have different sample rates, the blend produces corrupted audio because `data1 + data2` mixes mismatched sample rates. Should resample `data2` to `sr1` when `sr1 != sr2`.

---

## 🟠 Logic / Correctness Issues

### 8. `_current_cached_model` Not Updated on Cache Hit (splitter.py:136-152)
When a cached model is found (line 136-140), `_current_cached_model` is not updated. If the app processes with model A, then B (clears cache), then A again (cache hit), `_current_cached_model` still points to B. This breaks the cache invalidation logic on the next switch.

### 9. Mode Filter Logic Bug — Standard Mode With Backing Track (splitter.py:387-394)
When `mode == constants.MODE_DRUMS`, the filter `"drums" not in stem_name` skips any stem that doesn't contain "drums". But Demucs produces `drums.wav`, not a stem containing just "drums" — it also produces `no_drums.wav`. `"drums" in "no_drums"` is `True`, so the `no_drums` stem would also pass the filter incorrectly.

### 10. `vocals_enhanced.wav` in CLEANUP_PATTERNS (constants.py:37)
The pattern `"vocals_enhanced"` is listed in `CLEANUP_PATTERNS`. But the final enhanced file is written as `vocals_enhanced.wav` (advanced_audio.py:541). If the cleanup runs in the same directory before the file is moved, it could **delete the final result** it just created. The skip check on line 555 should handle this, but it's fragile.

### 11. Preset `dereverb` Type Mismatch (presets.py vs enhance panel)
Default presets define `dereverb` as `True/False` (boolean), but `separate_audio()` expects `dereverb` as an integer intensity (0-100). Applying the "Karaoke Master" preset would pass `True` as intensity, which Python interprets as `1` — a near-zero effect instead of the intended full dereverb.

### 12. Settings QSettings Key Mismatch (settings_dialog.py:30 vs main_window.py:775)
`SettingsDialog` uses `QSettings("BeatDeStack", "eXtended")` (line 30) but `MainWindow.process_item()` reads from `QSettings("BeatDeStack", "BeatDeStackExtended")` (line 775). These are **different registries** — settings saved in the dialog will never be read during processing.

### 13. `_add_files` Method Referenced But Doesn't Exist (main_window.py:145)
Line 145 connects `Ctrl+O` shortcut to `self._add_files`, but no method `_add_files` exists. The correct method is `open_file_dialog` (used on line 945 in the second `_setup_shortcuts`). This shortcut binding will throw `AttributeError`.

### 14. Hardcoded `HIP_VISIBLE_DEVICES = "1"` (splitter.py:802)
`env["HIP_VISIBLE_DEVICES"] = "1"` is always set when ROCm paths exist. This forces GPU device index 1, which may not exist on single-GPU systems. Should default to `"0"` or be configurable.

### 15. `PitchShift` Uses Monkeypatched torchaudio (splitter.py:77)
`_apply_pitch_shift` uses `torchaudio.transforms.PitchShift`, but `torchaudio.load/save` has been monkeypatched at module level (lines 37-38). If `PitchShift` internally relies on standard torchaudio I/O, it may behave unexpectedly.

---

## 🟡 Code Quality / Maintenance

### 16. Logger Name Doesn't Match Project (logger.py:6)
Logger is named `"SunoSplitter"` — a leftover from an earlier project name. Should be `"BeatDeStack"` for consistency with the actual project name.

### 17. App Name Inconsistency (main.py:78)
`app.setApplicationName("StemLab")` but the window title is `"BeatDeStack eXtended v3.8.0"`. The internal app name should match the visible branding.

### 18. `time.sleep()` During Startup (main.py:89-94)
Artificial `time.sleep(1)` and `time.sleep(0.5)` calls block the main thread during startup. These provide no real benefit (splash just shows fake loading states) and add 2.5 seconds of unnecessary startup delay.

### 19. `import time` / `import math` Inside Functions (advanced_audio.py:164, settings_dialog.py:379)
Multiple places import standard library modules inside methods (`import time` at line 164 of `advanced_audio.py`, `import math` in settings_dialog). While functional, these should be at module level for clarity and marginal performance.

### 20. Missing `__init__.py` in `src/core/` and `src/utils/`
No `__init__.py` files exist in `src/core/` or `src/utils/`. Imports work because of the project structure, but adding these would make the packages explicit and enable proper tooling support.

### 21. Bare `except:` Block (main.py:31, presets.py:16)
`main.py` line 31 uses bare `except: pass` which swallows all exceptions including `KeyboardInterrupt` and `SystemExit`. `presets.py` line 16 uses bare `except:` for determining the presets directory. Both should catch specific exceptions.

### 22. `src_np` Variable Reused Across Scopes (splitter.py:482, 511, 517, 525)
The variable `src_np` is assigned in the main stem loop (line 482) and then reassigned inside the band-splitting block (lines 511, 517, 525). While Python scoping makes this technically fine, it's confusing and error-prone.

### 23. Copyright Year Outdated (settings_dialog.py:330)
Footer says `"© 2025 BeatDeStack Project"` but the current date is 2026.

### 24. Commented-Out Code Everywhere (player.py)
`player.py` is filled with commented-out code blocks (seek slider, time label, etc.) spread across 50+ lines. This dead code should be removed or extracted into a feature branch.

### 25. Unused Import: `QMimeData` (widgets.py:5)
`QMimeData` is imported but never used in `widgets.py`.

### 26. Unused Import: `QDrag` (widgets.py:6)
`QDrag` is imported but never used in `widgets.py`.

### 27. Unused Import: `QMediaPlayer` (main_window.py:12)
`QMediaPlayer` is imported at the top of `main_window.py` but never used directly (only used via `player.py`).

---

## 🔵 Performance / Resource Issues

### 28. Visualizer Timer Always Running (widgets.py:223)
`VisualizerWidget` starts a 50ms timer on construction and **never stops it**, continuously recalculating and repainting even when idle. This wastes CPU. The timer should only run when the visualizer is visible or active.

### 29. No Model Cache Cleanup on App Exit (splitter.py)
`clear_model_cache()` is defined but never called anywhere in the codebase. Cached AI models occupy GPU memory until the process terminates. Should be called in `MainWindow.closeEvent()`.

### 30. WaveformLoader Blocks on Previous Thread (waveform.py:165-166)
`self.loader.wait()` synchronously blocks the GUI thread waiting for the previous waveform load to complete. If the user rapidly clicks items, the UI freezes. Should use thread termination with `requestInterruption()` or a cancellation flag.

### 31. Process Output Read Byte-by-Byte (splitter.py:820)
`self.process.stdout.read(1)` reads subprocess output one byte at a time. This is extremely inefficient for large output streams. Should use line-buffered reading or `readline()`.

### 32. GPU Info Called Multiple Times (settings_dialog.py:270, main_window.py:566)
`get_gpu_info()` is called in multiple places, each time re-running the GPU detection logic (including potential DirectML import attempts). The result should be cached at application startup.

### 33. No Temp File Cleanup on Preview Failure (main_window.py:844-846)
If `create_preview_slice` fails, the preview source file and `Previews` directory are left on disk. No cleanup is performed.

---

## ⚪ Minor / Cosmetic

### 34. Duplicate Comment Block in `settings_dialog.py:66`
Line 66 has a duplicate comment `# Models Tab` directly above line 67.

### 35. Duplicate `setSpecialValueText("Auto")` (settings_dialog.py:183)
`self.spin_memory.setSpecialValueText("Auto")` is called twice in succession (lines 182-183).

### 36. `pass` Statement in `_on_queue_item_clicked` (main_window.py:562)
Orphaned `pass` statement after an `else:` block that's fully commented out. Just remove the dead code.

### 37. Missing Drag-and-Drop Hover Reset (widgets.py)
`DragDropWidget.dragLeaveEvent` resets to original style, but if a user drops a non-audio file, the hover style from `dragEnterEvent` isn't reset (since `dropEvent` only fires on valid drops).

### 38. Hardcoded `"ffmpeg.exe"` in `resource_utils.py`
`get_ffmpeg_path()` uses `"ffmpeg.exe"` on all platforms (lines 32, 37). On macOS/Linux this should be `"ffmpeg"` (no `.exe`). The function would fail to find bundled ffmpeg on non-Windows platforms.

### 39. `_apply_time_stretch` Uses Default `hop_length=None` (splitter.py:89)
`torch.stft` is called with `hop_length=None` and `win_length=None`, which defaults to `n_fft//4` and `n_fft` respectively. This works but is implicit — should be explicitly stated to match the `TimeStretch` transform's `hop_length` parameter.

### 40. No Input Validation on Preset Names (presets.py:117-130)
`save_preset()` accepts any string as a preset name. Names containing path separators (`/`, `\`), dots, or special characters could create files in unexpected locations or fail silently.
