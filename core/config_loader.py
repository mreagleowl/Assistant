import os
import yaml
import logging
from dotenv import load_dotenv

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

    # Подхватываем API-ключ для GPT-выжимки
    openai_key = os.getenv('OPENAI_API_KEY')
    if openai_key:
        config.setdefault('gpt_summary', {})['api_key'] = openai_key
        logger.info('OpenAI API key loaded from environment')

    # Подхватываем пароль почты
    email_pass = os.getenv('EMAIL_PASSWORD')
    if email_pass:
        config.setdefault('email', {})['password'] = email_pass
        logger.info('Email password loaded from environment')

    return config