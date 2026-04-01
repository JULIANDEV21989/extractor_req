"""Extrae frames y transcribe audio de videos MP4."""

import os
import subprocess


def _extract_frames(file_path: str, output_dir: str, interval: int = 15) -> list[str]:
    """Extrae frames de un video cada N segundos usando ffmpeg."""
    os.makedirs(output_dir, exist_ok=True)
    pattern = os.path.join(output_dir, "frame_%04d.jpg")
    cmd = [
        "ffmpeg", "-i", file_path,
        "-vf", f"fps=1/{interval}",
        "-q:v", "3", pattern, "-y",
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return sorted([
        os.path.join(output_dir, f)
        for f in os.listdir(output_dir) if f.endswith(".jpg")
    ])


def _transcribe_audio(file_path: str, model_size: str = "medium", language: str = "es") -> str:
    """Transcribe audio de un video usando faster-whisper."""
    from faster_whisper import WhisperModel

    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, info = model.transcribe(file_path, language=language, beam_size=5, vad_filter=True)

    lines = [
        f"**Idioma:** {info.language} ({info.language_probability:.0%})",
        f"**Duración:** {info.duration:.0f}s\n",
    ]
    for seg in segments:
        m, s = divmod(int(seg.start), 60)
        h, m = divmod(m, 60)
        ts = f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"
        lines.append(f"[{ts}] {seg.text.strip()}")
    return "\n".join(lines)


def extract_video(
    file_path: str,
    output_dir: str = "output/frames",
    frame_interval: int = 15,
    transcribe: bool = True,
    whisper_model: str = "medium",
    language: str = "es",
) -> str:
    """Extrae frames y opcionalmente transcribe un video.

    Returns:
        Markdown con info de frames extraídos + transcripción si aplica.
    """
    name = os.path.splitext(os.path.basename(file_path))[0]
    safe_name = "".join(c if c.isalnum() or c in "-_ " else "_" for c in name)[:60]
    frame_dir = os.path.join(output_dir, safe_name)

    result_parts: list[str] = []

    # Extraer frames
    try:
        frames = _extract_frames(file_path, frame_dir, frame_interval)
        total_mb = sum(os.path.getsize(f) for f in frames) / 1024 / 1024
        result_parts.append(
            f"**Frames extraídos:** {len(frames)} (cada {frame_interval}s, {total_mb:.1f} MB)\n"
            f"**Directorio:** {frame_dir}\n"
            f"Los frames contienen capturas de pantallas compartidas, interfaces y documentos "
            f"mostrados durante la reunión. Deben analizarse visualmente."
        )
    except Exception as e:
        result_parts.append(f"[Error extrayendo frames: {e}]")

    # Transcribir audio
    if transcribe:
        try:
            transcript = _transcribe_audio(file_path, whisper_model, language)
            result_parts.append(f"\n#### Transcripción de Audio\n\n{transcript}")
        except Exception as e:
            result_parts.append(f"\n[Error transcribiendo audio: {e}]")

    return "\n".join(result_parts)
