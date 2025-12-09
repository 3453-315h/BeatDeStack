import os
from basic_pitch.inference import predict_and_save
from basic_pitch import ICASSP_2022_MODEL_PATH
from src.utils.logger import logger

class MidiConverter:
    def __init__(self):
        self.output_dir = "midi_exports"
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def convert_to_midi(self, audio_path, output_path=None):
        """
        Converts an audio file to MIDI using basic-pitch.
        
        Args:
            audio_path (str): Path to the input audio file.
            output_path (str, optional): Path to save the MIDI file. 
                                         If None, saves to the same directory as input with .mid extension.
        
        Returns:
            str: Path to the generated MIDI file.
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        if output_path is None:
            base_name = os.path.splitext(os.path.basename(audio_path))[0]
            output_dir = os.path.dirname(audio_path)
            output_path = os.path.join(output_dir, f"{base_name}_midi") # predict_and_save appends extensions

        try:
            logger.info(f"Starting MIDI conversion for: {audio_path}")
            
            # predict_and_save takes a list of input audio paths and an output directory
            # It explicitly saves content, creating files like <output_path>_basic_pitch.mid
            # We want control over the filename, so we might need a slightly different approach 
            # or rename after. predict_and_save interface is high level.
            # Let's use the output_directory argument as the directory.
            
            output_directory = os.path.dirname(output_path)
            
            predict_and_save(
                [audio_path],
                output_directory,
                True, # save_midi
                False, # sonify_midi
                False, # save_model_outputs
                False, # save_notes
                ICASSP_2022_MODEL_PATH 
            )
            
            # proper cleanup/renaming might be needed because basic-pitch appends suffix
            expected_filename = os.path.splitext(os.path.basename(audio_path))[0] + "_basic_pitch.mid"
            generated_file = os.path.join(output_directory, expected_filename)
            
            final_midi_path = output_path + ".mid" if not output_path.endswith(".mid") else output_path
            
            if os.path.exists(generated_file):
                if os.path.exists(final_midi_path):
                    os.remove(final_midi_path)
                os.rename(generated_file, final_midi_path)
                logger.info(f"MIDI saved to: {final_midi_path}")
                return final_midi_path
            else:
                logger.warning(f"Expected generated file not found: {generated_file}")
                return None

        except Exception as e:
            logger.error(f"Error converting to MIDI: {e}")
            raise e
