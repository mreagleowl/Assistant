# core/gpt_summary.py

import os
from openai import OpenAI
import logging

logger = logging.getLogger(__name__)

# Клиент OpenAI инициализируется при первом вызове
_client = None

def get_api_key_env(config_section: dict, default_env: str = "OPENAI_API_KEY") -> str:
    """
    Получает ключ для API:
    - Сначала по config_section['api_key'] (если указан явно в YAML)
    - Затем по config_section['api_key_env'] (как имя переменной .env)
    - Затем из переменной default_env (например, OPENAI_API_KEY)
    """
    if config_section is None:
        return os.getenv(default_env, "")
    if "api_key" in config_section and config_section["api_key"]:
        return config_section["api_key"]
    if "api_key_env" in config_section and config_section["api_key_env"]:
        return os.getenv(config_section["api_key_env"], "")
    return os.getenv(default_env, "")

def generate_summary(transcript_text: str, config: dict, prompt_text: str = None) -> str:
    """
    Генерирует выжимку из готовой стенограммы (transcript_text) с учётом:
      - выбранного в GUI текстового промпта (prompt_text);
      - если prompt_text не передан, берёт prompt_template из конфига;
      - если и там пусто, используется дефолтный промпт.

    Возвращает строку с итоговым текстом выжимки.
    """
    global _client

    gs = config.get('gpt_summary', {})
    if not gs.get('enabled', False):
        return 'GPT summary disabled.'

    api_key = get_api_key_env(gs)
    model = gs.get('model', 'gpt-4')
    template = gs.get('prompt_template')

    if not api_key:
        logger.error('OpenAI API key missing (нет ни api_key ни api_key_env)')
        return '[Missing API key]'

    # Инициализируем или обновляем клиента
    if _client is None:
        _client = OpenAI(api_key=api_key)
    else:
        _client.api_key = api_key

    # 1) Выбираем, какой текст использовать в качестве промпта:
    if prompt_text:
        # если передан из GUI (выбран пользователем в Combobox), используем его
        prompt = prompt_text.replace('{{ transcript }}', transcript_text)
        logger.info(f"Using custom prompt from GUI.")
    elif template:
        # если в конфиге есть prompt_template, подставляем в него {{ transcript }}
        prompt = template.replace('{{ transcript }}', transcript_text)
        logger.info(f"Using prompt template from config.")
    else:
        # дефолтный минимальный промпт
        prompt = "Analyze meeting transcript and output summary with tasks: " + transcript_text
        logger.info(f"Using default prompt.")

    try:
        temp = gs.get('temperature', 0.3)   # если в конфиге нет, по умолчанию 0.3
        response = _client.chat.completions.create(
            model=model,
            messages=[
                {'role': 'system', 'content': 'Assistant for meeting analysis.'},
                {'role': 'user', 'content': prompt}
            ],
            temperature=temp
        )
        content = response.choices[0].message.content
        return content.strip()
    except Exception as e:
        logger.exception('GPT API error')
        return f'[Error in GPT: {e}]'
