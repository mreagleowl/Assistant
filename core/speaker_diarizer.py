# virtual_secretary/speaker_diarizer.py

import os
import librosa
from resemblyzer import VoiceEncoder, preprocess_wav
from sklearn.metrics.pairwise import cosine_similarity
import logging

logger = logging.getLogger(__name__)

def format_timestamp(seconds: float) -> str:
    mins = int(seconds) // 60
    secs = int(seconds) % 60
    return f"{mins}:{secs:02d}"

def load_reference_embeddings(reference_dir="reference_voices"):
    logger.info(f"Loading reference embeddings from {reference_dir}")
    encoder = VoiceEncoder()
    references = {}
    for filename in os.listdir(reference_dir):
        if filename.endswith(".wav"):
            path = os.path.join(reference_dir, filename)
            name = filename.replace(".wav", "").replace("_", " ")
            wav = preprocess_wav(path)
            embed = encoder.embed_utterance(wav)
            references[name] = embed
    return references

def identify_speakers(audio_path, transcript_segments, config=None, reference_dir="reference_voices"):
    encoder = VoiceEncoder()
    references = load_reference_embeddings(reference_dir)
    speaker_lines = []

    # Опция из конфига (если config не передан — всегда показываем тайм-коды)
    show_timestamps = True
    if config is not None:
        show_timestamps = config.get('diarization', {}).get('show_timestamps', True)

    for segment in transcript_segments:
        start = segment["start"]
        end = segment["end"]
        text = segment.get("text", "").strip()

        wav, sr = librosa.load(audio_path, sr=16000, offset=start, duration=end - start)
        segment_embed = encoder.embed_utterance(wav)

        best_match = None
        best_score = -1.0
        for name, ref_embed in references.items():
            score = cosine_similarity([segment_embed], [ref_embed])[0][0]
            if score > best_score:
                best_score = score
                best_match = name

        speaker_name = best_match if best_score > 0.75 else "Speaker"
        if show_timestamps:
            ts = format_timestamp(start)
            speaker_lines.append(f"[{ts}] {speaker_name}: {text}")
        else:
            speaker_lines.append(f"{speaker_name}: {text}")

    return "\n".join(speaker_lines)
