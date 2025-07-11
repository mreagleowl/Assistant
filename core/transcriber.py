# core/transcriber.py

import soundfile as sf
import whisper
from core.speaker_diarizer import identify_speakers
import logging

logger = logging.getLogger(__name__)

try:
    import openai
except ImportError:
    openai = None

# Кэш самой модели и её имени (для offline)
_model = None
_current_model_name = None

def transcribe_audio(file_path, config=None, model_name=None):
    """
    Транскрибирует WAV-файл через Whisper (локально или через API) и идентифицирует говорящих.
    """
    # 1. Определяем режим
    mode = 'offline'
    if config:
        mode = config.get('transcription', {}).get('mode', 'offline')

    # --- OFFLINE Whisper (локальный) ---
    if mode == 'offline':
        global _model, _current_model_name

        if model_name is None and config:
            model_name = config.get('transcription', {}).get('model', 'medium')
        model_name = model_name or 'medium'

        logger.info(f"[OFFLINE] Requested Whisper model: '{model_name}'")

        if _model is None or _current_model_name != model_name:
            logger.info(f"[OFFLINE] Loading Whisper model '{model_name}' (this may take a while)...")
            _model = whisper.load_model(model_name)
            _current_model_name = model_name
            logger.info(f"[OFFLINE] Whisper model loaded: '{model_name}'")

        audio, sr = sf.read(file_path)
        if audio.dtype != 'float32':
            audio = audio.astype('float32')

        lang = None
        if config:
            lang = config.get("transcription", {}).get("language")

        if lang:
            logger.info(f"[OFFLINE] Transcribing with forced language: '{lang}'")
            result = _model.transcribe(audio, language=lang)
        else:
            result = _model.transcribe(audio)

        segments = result.get('segments', [])
        if not segments:
            return '[Empty transcription]'

        return identify_speakers(file_path, segments, config)

         # --- ONLINE Whisper API ---
    elif mode == 'online':
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("Для online-режима нужен пакет openai: pip install openai")

        from core.config_loader import get_api_key_env
        section_cfg = config.get("transcription", {}) if config else {}
        api_key = get_api_key_env(section_cfg)
        lang = section_cfg.get("language")

        if not api_key:
            raise ValueError("API-ключ для online-режима не задан (ни api_key, ни api_key_env, ни OPENAI_API_KEY)")

        client = OpenAI(api_key=api_key)

        logger.info("[ONLINE] Загружаем аудиофайл для отправки в OpenAI Whisper API")
        with open(file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=lang,
                response_format="verbose_json"
            )

        segments = getattr(transcript, "segments", [])
        if not segments:
            return '[Empty transcription]'

        return identify_speakers(file_path, segments, config)

    else:
        raise ValueError(f"Неизвестный режим транскрипции: {mode}")
