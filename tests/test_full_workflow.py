import os
import sys
import glob

# Ensure src is in pythonpath
sys.path.append(os.getcwd())

# MUST SET THIS FOR MIDI EXPORT
os.environ["TF_USE_LEGACY_KERAS"] = "1"

from src.core.splitter import separate_audio
from src.core.midi_converter import MidiConverter

def test_full_workflow():
    input_file = "test.mp3"
    output_dir = "test_workflow_output"
    
    # 1. Separation
    print(f"--- Step 1: Separating {input_file} (Model: htdemucs_6s) ---")
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found!")
        return

    try:
        # Using htdemucs_6s for maximum default stems (6 stems)
        separate_audio(
            input_file, 
            output_dir, 
            stem_count=6, 
            quality=0, # Fast mode for testing
            export_zip=False, 
            keep_original=False,
            model="htdemucs_6s",
             # segment=10 removed as htdemucs max is ~7.8
        )
    except Exception as e:
        print(f"Separation Failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # 2. MIDI Conversion
    print("\n--- Step 2: Converting Stems to MIDI ---")
    
    # Find the output folder (it's usually a subdir inside output_dir)
    # The splitter creates "test - Stems" inside output_dir? 
    # Let's check splitter.py logic: 
    # base_name = os.path.splittext(filename)[0]
    # output_dir is passed in... wait.
    # In splitter.py: os.makedirs(output_dir, exist_ok=True)
    # dest = os.path.join(output_dir, f"{rel_path}.{final_ext}")
    # So the files are directly in output_dir/filename_pattern ?
    # Default pattern is "{stem}". So they will be in output_dir directly or ?
    # Wait, line 84: base_name = ...
    # line 436 (Worker): output_dir = parent/basename - Stems.
    # But direct call separate_audio uses passed output_dir.
    # And line 244: dst = os.path.join(output_dir, f"{rel_path}.{final_ext}")
    # So if I pass "test_workflow_output", files like "vocals.wav" will be there.
    
    search_path = os.path.join(output_dir, "*.wav")
    stems = glob.glob(search_path)
    
    if not stems:
        print("No stems found! Separation failed?")
        return
        
    print(f"Found {len(stems)} stems: {[os.path.basename(s) for s in stems]}")
    
    converter = MidiConverter()
    
    for stem in stems:
        print(f"\nProcessing: {os.path.basename(stem)}")
        try:
            midi_path = converter.convert_to_midi(stem)
            if midi_path and os.path.exists(midi_path):
                print(f"  [SUCCESS] -> {midi_path}")
            else:
                print(f"  [FAILURE] Could not create MIDI.")
        except Exception as e:
             print(f"  [ERROR] {e}")

if __name__ == "__main__":
    test_full_workflow()
