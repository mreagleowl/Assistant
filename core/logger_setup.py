import logging
import logging.config
import yaml
import os

def setup_logging(default_path='config/logging.yaml', default_level=logging.INFO):
    """
    Настраивает логирование для всего приложения на основе YAML-конфига.
    Если конфиг не найден — включает basicConfig на уровне INFO.
    """
    if not os.path.exists('logs'):
        os.makedirs('logs')
    try:
        with open(default_path, 'r') as f:
            config = yaml.safe_load(f.read())
            logging.config.dictConfig(config)
    except Exception as e:
        print(f"Ошибка при настройке логирования: {e}")
        logging.basicConfig(level=default_level)
