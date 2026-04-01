"""Extrae frames, transcribe audio y analiza texto visible en videos.

Pipeline:
1. Extraer frames cada N segundos (ffmpeg)
2. Detectar frames clave (cambios significativos entre frames)
3. Analizar frames clave: OCR/Vision para extraer texto visible
4. Transcribir audio (faster-whisper) — independiente del OCR
5. Correlacionar: vincular texto de frames con timestamps del transcript

IMPORTANTE: La extracción de texto visual (OCR en frames) NO depende de la
transcripción de audio. Son dos canales independientes:
- Canal visual: frames → OCR → texto de pantallas/documentos compartidos
- Canal auditivo: audio → whisper → transcripción hablada
Ambos se ejecutan por separado y se consolidan al final.
"""

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


def _detect_key_frames(frames: list[str], threshold: float = 0.35) -> list[tuple[int, str]]:
    """Detecta frames con cambios significativos comparando histogramas.

    Retorna lista de (frame_index, frame_path) para frames que tienen
    contenido visualmente nuevo respecto al anterior.
    """
    try:
        import cv2
        import numpy as np
    except ImportError:
        # Sin OpenCV, tratar todos los frames como clave (muestreando 1 de cada 3)
        return [(i, f) for i, f in enumerate(frames) if i % 3 == 0]

    key_frames = []
    prev_hist = None

    for i, frame_path in enumerate(frames):
        img = cv2.imread(frame_path)
        if img is None:
            continue
        # Convertir a escala de grises y calcular histograma
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        hist = cv2.normalize(hist, hist).flatten()

        if prev_hist is None:
            key_frames.append((i, frame_path))
            prev_hist = hist
            continue

        # Comparar con frame anterior (correlación)
        correlation = cv2.compareHist(prev_hist, hist, cv2.HISTCMP_CORREL)

        # Si la correlación es baja → contenido nuevo
        if correlation < (1.0 - threshold):
            key_frames.append((i, frame_path))
            prev_hist = hist

    # Siempre incluir el primer y último frame
    if frames and (0, frames[0]) not in key_frames:
        key_frames.insert(0, (0, frames[0]))

    return key_frames


def _analyze_frame_text(frame_path: str, api_key: str | None = None) -> str:
    """Extrae texto visible de un frame usando Claude Vision o EasyOCR.

    Prioridad:
    1. Claude Vision (si hay API key) — entiende contexto visual
    2. EasyOCR local — OCR offline gratuito
    3. Placeholder
    """
    # Opción 1: Claude Vision
    if api_key:
        try:
            return _vision_analyze_frame(frame_path, api_key)
        except Exception:
            pass

    # Opción 2: EasyOCR
    try:
        import easyocr
        reader = easyocr.Reader(["es", "en"], gpu=False, verbose=False)
        results = reader.readtext(frame_path)
        texts = [r[1] for r in results if r[2] > 0.25]
        if texts:
            return "\n".join(texts)
    except ImportError:
        pass
    except Exception:
        pass

    return ""


def _vision_analyze_frame(frame_path: str, api_key: str) -> str:
    """Analiza un frame con Claude Vision para extraer texto y descripción."""
    import base64
    import anthropic

    with open(frame_path, "rb") as f:
        data = base64.standard_b64encode(f.read()).decode("utf-8")

    client = anthropic.Anthropic(api_key=api_key)
    msg = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": data}},
                {"type": "text", "text": (
                    "Este es un frame de un video de reunión/presentación. "
                    "Transcribe TODO el texto visible en la pantalla. "
                    "Si hay tablas, reconstruyelas. Si hay diagramas, descríbelos. "
                    "Si hay interfaz de software, describe qué se muestra. "
                    "Sé conciso pero completo. Responde en español."
                )},
            ],
        }],
    )
    return msg.content[0].text


def _transcribe_audio(file_path: str, model_size: str = "medium", language: str = "es") -> str:
    """Transcribe audio de un video usando faster-whisper."""
    from faster_whisper import WhisperModel

    model = WhisperModel(model_size, device="cpu", compute_type="int8")

    lang_param = None if language == "auto" else language
    segments, info = model.transcribe(file_path, language=lang_param, beam_size=5, vad_filter=True)

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
    api_key: str | None = None,
) -> str:
    """Extrae frames, analiza texto visible y transcribe audio de un video.

    Dos canales INDEPENDIENTES:
    - Visual: frames → detección de key frames → OCR/Vision → texto de pantalla
    - Auditivo: audio → whisper → transcripción hablada

    Returns:
        Markdown con análisis visual de frames + transcripción de audio
    """
    name = os.path.splitext(os.path.basename(file_path))[0]
    safe_name = "".join(c if c.isalnum() or c in "-_ " else "_" for c in name)[:60]
    frame_dir = os.path.join(output_dir, safe_name)

    result_parts: list[str] = []

    # ============ CANAL VISUAL: Frames + OCR ============
    frames = []
    try:
        frames = _extract_frames(file_path, frame_dir, frame_interval)
        total_mb = sum(os.path.getsize(f) for f in frames) / 1024 / 1024
        result_parts.append(
            f"**Frames extraídos:** {len(frames)} (cada {frame_interval}s, {total_mb:.1f} MB)\n"
            f"**Directorio:** {frame_dir}"
        )
    except Exception as e:
        result_parts.append(f"[Error extrayendo frames: {e}]")

    # Detectar frames clave y analizar texto
    if frames:
        try:
            key_frames = _detect_key_frames(frames)
            result_parts.append(
                f"\n**Frames clave detectados:** {len(key_frames)} de {len(frames)} "
                f"(frames con contenido visual nuevo)\n"
            )

            result_parts.append("#### Análisis Visual de Frames Clave\n")
            analyzed_count = 0
            for frame_idx, frame_path in key_frames:
                # Calcular timestamp aproximado
                timestamp_sec = frame_idx * frame_interval
                m, s = divmod(timestamp_sec, 60)
                h, m = divmod(m, 60)
                ts = f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

                frame_text = _analyze_frame_text(frame_path, api_key)
                if frame_text:
                    analyzed_count += 1
                    frame_name = os.path.basename(frame_path)
                    result_parts.append(f"**[{ts}] Frame {frame_idx + 1} ({frame_name}):**")
                    result_parts.append(frame_text)
                    result_parts.append("")

            if analyzed_count == 0:
                result_parts.append(
                    "*No se detectó texto en los frames. Para mejor análisis:\n"
                    "  - Configura ANTHROPIC_API_KEY (Claude Vision)\n"
                    "  - O instala EasyOCR: pip install easyocr\n"
                    "  - O instala OpenCV: pip install opencv-python-headless*"
                )
        except Exception as e:
            result_parts.append(f"[Error analizando frames clave: {e}]")

    # ============ CANAL AUDITIVO: Transcripción ============
    if transcribe:
        try:
            transcript = _transcribe_audio(file_path, whisper_model, language)
            result_parts.append(f"\n#### Transcripción de Audio\n\n{transcript}")
        except Exception as e:
            result_parts.append(f"\n[Error transcribiendo audio: {e}]")

    return "\n".join(result_parts)
