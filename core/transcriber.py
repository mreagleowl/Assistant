# core/transcriber.py

import soundfile as sf
import whisper
from core.speaker_diarizer import identify_speakers
from logger import logger   # обязательно, чтобы не было NameError

# Кэш самой модели и её имени
_model = None
_current_model_name = None

def transcribe_audio(file_path, config=None, model_name=None):
    """
    Транскрибирует WAV-файл через Whisper и идентифицирует говорящих.
    При каждом вызове сверяет, совпадает ли требуемая модель с загруженной,
    и при необходимости подгружает новую.
    """

    global _model, _current_model_name

    # 1) Выбор модели: явно переданный model_name > конфиг > 'medium' по умолчанию
    if model_name is None and config:
        model_name = config.get('transcription', {}).get('model', 'medium')
    model_name = model_name or 'medium'

    # 2) Логируем, какую модель хотим использовать
    logger.info(f"Requested Whisper model: '{model_name}'")

    # 3) Если нужная модель ещё не загружена или отличается от текущей, перезагружаем
    if _model is None or _current_model_name != model_name:
        logger.info(f"Loading Whisper model '{model_name}' (this may take a while)...")
        _model = whisper.load_model(model_name)
        _current_model_name = model_name
        logger.info(f"Whisper model loaded: '{model_name}'")

    # 4) Читаем и приводим аудио к float32
    audio, sr = sf.read(file_path)
    if audio.dtype != 'float32':
        audio = audio.astype('float32')

    # 5. Определяем язык из конфига (если есть)
    lang = None
    if config:
        lang = config.get("transcription", {}).get("language")

    # 6. Транскрипция с учётом языка (или автодетект, если lang=None)
    if lang:
        logger.info(f"Transcribing with forced language: '{lang}'")
        result = _model.transcribe(audio, language=lang)
    else:
        result = _model.transcribe(audio)

    segments = result.get('segments', [])
    if not segments:
        return '[Empty transcription]'

    return identify_speakers(file_path, segments, config)
