import os
import shutil
from src.utils.logger import logger

class ModelManager:
    def __init__(self, base_path=None):
        import sys
        
        # 1. Determine where "Built-in" models live (read-only in EXE)
        if base_path is None:
             # If frozen, built-ins are in sys._MEIPASS/models
             if getattr(sys, 'frozen', False):
                 self.builtin_models_dir = os.path.join(sys._MEIPASS, "models")
             else:
                 # In dev, relative to source
                 self.builtin_models_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "models")
        else:
             self.builtin_models_dir = os.path.join(base_path, "models")

        # 2. Determine where "Custom/Downloaded" models live (Persistent)
        if getattr(sys, 'frozen', False):
             # In EXE, use the folder where the EXE lives (Portable)
             # Or AppData if we wanted to be strict, but portable is better for this tool.
             self.persistent_root = os.path.dirname(sys.executable)
        else:
             # In dev, use project root
             self.persistent_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
             
        self.models_dir = os.path.join(self.persistent_root, "models")
        self.custom_models_dir = os.path.join(self.models_dir, "custom")
        
        # Ensure persistent dirs exist
        os.makedirs(self.models_dir, exist_ok=True)
        os.makedirs(self.custom_models_dir, exist_ok=True)
        
        self.default_models = [
            "htdemucs", "htdemucs_6s",
            "model_bs_roformer_ep_317_sdr_12.9755.ckpt", 
            "vocals_mel_band_roformer.ckpt",
            "MDX23C-8KFFT-InstVoc_HQ.ckpt",
            "UVR_MDXNET_KARA.onnx"
        ]
        self.custom_models = []
        self.refresh_models()
        
    def refresh_models(self):
        """Scan models directory for downloaded/custom models"""
        self.custom_models = []
        
        # Helper to scan a directory
        def scan_dir(d):
            found = []
            if os.path.exists(d):
                for f in os.listdir(d):
                    if f.endswith(('.pth', '.onnx', '.yaml', '.ckpt')):
                        found.append(f)
            return found

        # Scan Built-in models folder (Read-Only Bundle)
        builtin_files = scan_dir(self.builtin_models_dir)
        
        # Scan Persistent "models" folder (User Data)
        persistent_files = scan_dir(self.models_dir)
        
        # Scan Persistent "models/custom" folder
        custom_files = scan_dir(self.custom_models_dir)
        
        # Merge lists, avoiding duplicates with defaults
        all_found = set(builtin_files + persistent_files + custom_files)
        
        for f in all_found:
            # If it's not in the hardcoded defaults list, treat as custom/downloaded
            if f not in self.default_models:
                self.custom_models.append(f)
                    
    def get_all_models(self):
        """Return list of all available models (defaults + downloaded/custom)"""
        return self.default_models + self.custom_models

    def import_model(self, file_path):
        """Copy a model file to the custom directory"""
        try:
            filename = os.path.basename(file_path)
            dest = os.path.join(self.custom_models_dir, filename)
            shutil.copy2(file_path, dest)
            logger.info(f"Imported model: {filename}")
            self.refresh_models()
            return True
        except Exception as e:
            logger.error(f"Failed to import model {file_path}: {e}")
            return False
            
    def get_model_path(self, model_name):
        """Get absolute path for a model."""
        # 1. Check Custom Dir (Persistent)
        p = os.path.join(self.custom_models_dir, model_name)
        if os.path.exists(p): return p
        
        # 2. Check Models Dir (Persistent)
        p = os.path.join(self.models_dir, model_name)
        if os.path.exists(p): return p
        
        # 3. Check Built-in Dir (Bundle)
        p = os.path.join(self.builtin_models_dir, model_name)
        if os.path.exists(p): return p
            
        # Default fallback (often just the name for Demucs internal load)
        return model_name

    def get_model_paths(self):
        """Return list of directories to search for models."""
        return [self.models_dir, self.custom_models_dir]
    
    def delete_model(self, model_name):
        """Delete a downloaded/custom model. Default models cannot be deleted."""
        if model_name in self.default_models:
            logger.warning(f"Cannot delete default model: {model_name}")
            return False
        
        # Check both directories for the model
        possible_paths = [
            os.path.join(self.models_dir, model_name),
            os.path.join(self.custom_models_dir, model_name),
        ]
        
        for model_path in possible_paths:
            if os.path.exists(model_path):
                try:
                    os.remove(model_path)
                    logger.info(f"Deleted model: {model_name} from {model_path}")
                    self.refresh_models()
                    return True
                except Exception as e:
                    logger.error(f"Failed to delete model {model_name}: {e}")
                    return False
        
        logger.warning(f"Model not found for deletion: {model_name}")
        return False

