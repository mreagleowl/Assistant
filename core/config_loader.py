import os
import yaml
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# Явно указываем путь к .env в папке config
dotenv_path = os.path.join(os.path.dirname(__file__), '..', 'config', '.env')
load_dotenv(dotenv_path)

def load_config(path='config/settings.yaml'):
    """
    Загружает настройки из YAML и подмешивает секреты из .env.
    """
    config = {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        logger.info(f"Config loaded from {path}")
    except FileNotFoundError:
        logger.error(f"Config file not found at: {path}")
    except yaml.YAMLError as e:
        logger.error(f"YAML parsing error: {e}")
   
    # Подхватываем пароль почты
    email_pass = os.getenv('EMAIL_PASSWORD')
    if email_pass:
        config.setdefault('email', {})['password'] = email_pass
        logger.info('Email password loaded from environment')

    return config
def get_api_key_env(section_cfg, default_env="OPENAI_API_KEY"):
    """
    Универсальная функция для получения нужного ключа.
    Порядок:
      - section_cfg['api_key'] если явно задан,
      - os.getenv(section_cfg['api_key_env']) если есть api_key_env,
      - os.getenv(default_env) если ничего не указано.
    """
    if not section_cfg:
        return os.getenv(default_env, "")
    if "api_key" in section_cfg and section_cfg["api_key"]:
        return section_cfg["api_key"]
    if "api_key_env" in section_cfg and section_cfg["api_key_env"]:
        return os.getenv(section_cfg["api_key_env"], "")
    return os.getenv(default_env, "")
