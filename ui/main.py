from ui.gui import VirtualSecretaryGUI
from core.config_loader import load_config
from core.gpt_summary import generate_summary
from core.recorder import AudioRecorder
from core.logger_setup import setup_logging
setup_logging()


if __name__=='__main__':
    cfg = load_config('config/settings.yaml')
    rec = AudioRecorder()
    app = VirtualSecretaryGUI(cfg, generate_summary, rec)
    app.run()
