"""Engine de consolidación: extrae contenido de todos los archivos y genera un documento maestro."""

import os
from datetime import datetime

from .scanner import FileInfo, ScanResult
from .extractors.pdf import extract_pdf
from .extractors.docx import extract_docx
from .extractors.video import extract_video
from .extractors.image import extract_image
from .extractors.email import extract_email
from .extractors.audio import extract_audio
from .extractors.pptx import extract_pptx
from .extractors.spreadsheet import extract_spreadsheet
from .extractors.web import extract_web


def _extract_text(file_path: str) -> str:
    """Extrae texto plano de un archivo .txt/.md/.log."""
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def extract_file(
    file_info: FileInfo,
    output_dir: str = "output",
    api_key: str | None = None,
    video_config: dict | None = None,
) -> str:
    """Extrae contenido de un archivo según su tipo."""
    vc = video_config or {}

    extractors = {
        "pdf": lambda fi: extract_pdf(fi.path),
        "docx": lambda fi: extract_docx(fi.path),
        "pptx": lambda fi: extract_pptx(fi.path),
        "spreadsheet": lambda fi: extract_spreadsheet(fi.path),
        "email": lambda fi: extract_email(fi.path),
        "image": lambda fi: extract_image(fi.path, api_key=api_key),
        "text": lambda fi: _extract_text(fi.path),
        "web": lambda fi: extract_web(fi.path),
        "audio": lambda fi: extract_audio(
            fi.path,
            whisper_model=vc.get("whisper_model", "medium"),
            language=vc.get("language", "es"),
        ),
        "video": lambda fi: extract_video(
            fi.path,
            output_dir=os.path.join(output_dir, "frames"),
            frame_interval=vc.get("frame_interval", 15),
            transcribe=vc.get("transcribe_audio", True),
            whisper_model=vc.get("whisper_model", "medium"),
            language=vc.get("language", "es"),
            api_key=api_key,
        ),
    }

    extractor = extractors.get(file_info.file_type)
    if not extractor:
        return f"[Tipo no soportado para extracción directa: {file_info.file_type}]"

    try:
        return extractor(file_info)
    except Exception as e:
        return f"[ERROR extrayendo {file_info.name}: {type(e).__name__}: {e}]"


def consolidate(
    scan_result: ScanResult,
    output_dir: str = "output",
    api_key: str | None = None,
    video_config: dict | None = None,
    skip_video: bool = False,
    progress_callback=None,
) -> str:
    """Extrae y consolida todo el contenido en un documento Markdown maestro.

    Args:
        scan_result: Resultado del escaneo
        output_dir: Directorio de salida
        api_key: API key de Anthropic (opcional, para análisis de imágenes)
        video_config: Configuración de extracción de video
        skip_video: Omitir extracción de video
        progress_callback: Función callback(file_name, file_type, index, total)
    """
    sections: list[str] = []
    sections.append("# Documento Consolidado - Levantamiento de Información")
    sections.append(f"**Fecha de extracción:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    sections.append("**" + "\n".join(scan_result.summary_lines()) + "**\n")

    total = len(scan_result.files)
    for idx, file_info in enumerate(scan_result.files):
        folder = file_info.folder

        # Insertar separador de carpeta si es la primera de su grupo
        prev_folder = scan_result.files[idx - 1].folder if idx > 0 else None
        if folder != prev_folder:
            sections.append(f"\n---\n## Carpeta: {folder}\n")

        if progress_callback:
            progress_callback(file_info.name, file_info.file_type, idx + 1, total)

        if skip_video and file_info.file_type == "video":
            sections.append(f"### {file_info.name}\n*[VIDEO OMITIDO]*\n")
            continue

        sections.append(f"### {file_info.name}")
        sections.append(f"*Tipo: {file_info.file_type} | Tamaño: {file_info.size_mb:.1f} MB*\n")

        content = extract_file(file_info, output_dir, api_key, video_config)
        sections.append(content)
        sections.append("")

    return "\n".join(sections)
