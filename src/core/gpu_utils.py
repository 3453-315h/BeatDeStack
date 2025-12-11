import torch
from src.utils.logger import logger

def get_gpu_info():
    """
    Detects available GPU acceleration with priority: CUDA > DirectML > MPS > CPU
    
    Returns:
        tuple: (is_available: bool, device_name: str, device_type: str)
        
    Device types:
        - "cuda": NVIDIA CUDA or AMD ROCm (HIP)
        - "directml": DirectML (AMD/Intel/NVIDIA via DirectX 12)
        - "mps": Apple Silicon Metal Performance Shaders
        - "cpu": No GPU acceleration available
    """
    # Priority 1: NVIDIA CUDA
    if torch.cuda.is_available():
        # Check if this is actually ROCm (AMD HIP runtime)
        if hasattr(torch.version, 'hip') and torch.version.hip is not None:
            device_name = "AMD ROCm GPU"
            logger.info(f"GPU Detected: {device_name} (via HIP)")
            return True, device_name, "cuda"  # ROCm uses cuda device type
        else:
            device_name = torch.cuda.get_device_name(0)
            logger.info(f"GPU Detected: {device_name}")
            return True, device_name, "cuda"
    
    # Priority 2: DirectML (AMD/Intel/NVIDIA via DirectX 12)
    try:
        import torch_directml
        dml_device = torch_directml.device()
        device_name = "DirectML GPU"
        # Try to get more specific device info
        try:
            device_name = f"DirectML ({torch_directml.device_name(0)})"
        except Exception:
            pass
        logger.info(f"GPU Detected: {device_name}")
        return True, device_name, "directml"
    except ImportError:
        pass
    except Exception as e:
        logger.debug(f"DirectML not available: {e}")
    
    # Priority 3: Apple Silicon MPS
    if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        # Additional check for MPS build availability
        if torch.backends.mps.is_built():
            device_name = "Apple Silicon (MPS)"
            logger.info(f"GPU Detected: {device_name}")
            return True, device_name, "mps"
    
    # Fallback: CPU only
    logger.info("No GPU detected, using CPU.")
    return False, "CPU", "cpu"


def get_device():
    """
    Returns the best available PyTorch device.
    
    Returns:
        torch.device: The device to use for tensor operations
    """
    _, _, device_type = get_gpu_info()
    if device_type == "directml":
        import torch_directml
        return torch_directml.device()
    return torch.device(device_type)
