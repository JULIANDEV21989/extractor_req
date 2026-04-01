"""Extrae transcripción de archivos de audio (mp3, wav, m4a, ogg, flac, aac, wma)."""

import os


def extract_audio(
    file_path: str,
    whisper_model: str = "medium",
    language: str = "es",
) -> str:
    """Transcribe un archivo de audio usando faster-whisper.

    Args:
        file_path: Ruta al archivo de audio
        whisper_model: Modelo Whisper (tiny, base, small, medium, large-v3)
        language: Código de idioma (es, en, auto para detección automática)

    Returns:
        Markdown con transcripción timestamped
    """
    from faster_whisper import WhisperModel

    name = os.path.basename(file_path)
    size_mb = os.path.getsize(file_path) / 1024 / 1024

    model = WhisperModel(whisper_model, device="cpu", compute_type="int8")

    lang_param = None if language == "auto" else language
    segments, info = model.transcribe(
        file_path, language=lang_param, beam_size=5, vad_filter=True,
    )

    lines = [
        f"#### Transcripción de Audio: {name}",
        f"**Idioma detectado:** {info.language} ({info.language_probability:.0%})",
        f"**Duración:** {info.duration:.0f}s ({info.duration / 60:.1f} min)",
        f"**Tamaño:** {size_mb:.1f} MB",
        f"**Modelo:** {whisper_model}\n",
    ]

    for seg in segments:
        m, s = divmod(int(seg.start), 60)
        h, m = divmod(m, 60)
        ts = f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"
        lines.append(f"[{ts}] {seg.text.strip()}")

    return "\n".join(lines)
