import os
import shutil
import numpy as np
import soundfile as sf
import sys

# Ensure src is in path
sys.path.append(os.getcwd())

try:
    from src.core.splitter import separate_audio
    from src.core.midi_converter import MidiConverter
except ImportError as e:
    print(f"Import Error: {e}")
    print("Ensure you are running from the project root.")
    sys.exit(1)

TEST_FILE = "test.mp3"
OUTPUT_DIR = "test_output"

def create_dummy_audio(filename, duration=5.0, sr=44100):
    print(f"Generating dummy audio: {filename}...")
    t = np.linspace(0, duration, int(sr * duration))
    # Simple sine wave mix (A440 + C523)
    audio = 0.5 * np.sin(2 * np.pi * 440 * t) + 0.3 * np.sin(2 * np.pi * 523 * t)
    sf.write(filename, audio, sr)

def clean_output():
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR)

def run_test_case(name, **kwargs):
    print(f"\n--- Running Test Case: {name} ---")
    case_dir = os.path.join(OUTPUT_DIR, name)
    
    try:
        # Extract explicit args to avoid duplications in kwargs
        s_count = kwargs.pop("stem_count", 2)
        
        # Run Separation
        separate_audio(
            input_file=TEST_FILE,
            output_dir=case_dir,
            stem_count=s_count, 
            quality=0, # Fast
            export_zip=False,
            keep_original=False,
            **kwargs
        )
        
        # Verify Outputs
        print(f"Verifying outputs in {case_dir}...")
        files = os.listdir(case_dir)
        print(f"Files found: {files}")
        
        if not files:
            print("FAILED: No output files produced.")
            return False
            
        # Check specific expectations
        if kwargs.get("midi_enabled"):
            # Logic: separate_audio doesn't auto-call MIDI (SplitterWorker does).
            # So we manually call it here to verify integration logic if we were mimicking Worker.
            # But the user wants "all options", so we should test the MIDI component too.
            print("Testing MIDI generation...")
            converter = MidiConverter()
            # Assuming vocals exists
            vocab_file = os.path.join(case_dir, "vocals.wav")
            if os.path.exists(vocab_file):
                midi_path = converter.convert_to_midi(vocab_file)
                if midi_path and os.path.exists(midi_path):
                    print(f"SUCCESS: MIDI created at {midi_path}")
                else:
                    print("FAILED: MIDI output missing.")
                    return False
            else:
                 print("SKIPPING MIDI: No vocals.wav found.")
        
        if kwargs.get("dereverb", 0) > 0:
            # Check for enhanced file
            if "vocals_enhanced.wav" in files:
                print("SUCCESS: Audio Enhancement produced vocals_enhanced.wav")
            else:
                print("FAILED: Audio Enhancement missing.")
                return False

        print("PASSED.")
        return True

    except Exception as e:
        print(f"CRASH: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    if not os.path.exists(TEST_FILE):
        create_dummy_audio(TEST_FILE)

    clean_output()

    results = {}

    # Case 1: Basic Separation (2 Stems)
    results["Basic"] = run_test_case("Case_1_Basic", model="htdemucs", stem_count=2)

    # Case 2: Audio Enhancement (DeReverb)
    # Note: Demucs produces 'vocals.wav', standard logic applies enhancement to it.
    results["Enhancement"] = run_test_case("Case_2_Enhancement", model="htdemucs", stem_count=2, dereverb=50)

    # Case 3: MIDI Generation (Manual Trigger)
    results["MIDI"] = run_test_case("Case_3_MIDI", model="htdemucs", stem_count=2, midi_enabled=True)
    
    # Case 4: Full Stack (Enhance + MIDI)
    results["FullStack"] = run_test_case("Case_4_Full", model="htdemucs", stem_count=2, dereverb=20, midi_enabled=True)

    print("\n=== SUMMARY ===")
    for k, v in results.items():
        status = "PASS" if v else "FAIL"
        print(f"{k}: {status}")

if __name__ == "__main__":
    main()
