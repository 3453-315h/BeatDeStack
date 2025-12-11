import os
import sys
import traceback

# Ensure src is in pythonpath
sys.path.append(os.getcwd())

os.environ["TF_USE_LEGACY_KERAS"] = "1"

from src.core.midi_converter import MidiConverter
from basic_pitch import ICASSP_2022_MODEL_PATH

def test_midi():
    print(f"Model Path: {ICASSP_2022_MODEL_PATH}")
    if os.path.exists(ICASSP_2022_MODEL_PATH):
        print("Model file Exists.")
    else:
        print("Model file DOES NOT EXIST.")

    converter = MidiConverter()
    input_file = "test.mp3"
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found!")
        return

    print(f"Converting {input_file} to MIDI...")
    try:
        output = converter.convert_to_midi(input_file)
        if output and os.path.exists(output):
            print(f"SUCCESS: MIDI file created at: {output}")
        else:
            print("FAILURE: MIDI file was not created.")
    except Exception as e:
        print(f"ERROR TYPE: {type(e)}")
        print(f"ERROR REPR: {repr(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    test_midi()
