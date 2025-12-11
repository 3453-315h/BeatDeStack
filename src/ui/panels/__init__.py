# Panel components for the main window
from .stem_options import StemOptionsPanel
from .audio_enhancement import AudioEnhancementPanel
from .quality_mode import QualityModePanel
from .manipulation import ManipulationPanel
from .output_options import OutputPanel
from .advanced_settings import AdvancedSettingsPanel

__all__ = [
    'StemOptionsPanel',
    'AudioEnhancementPanel', 
    'QualityModePanel',
    'ManipulationPanel',
    'OutputPanel',
    'AdvancedSettingsPanel'
]
