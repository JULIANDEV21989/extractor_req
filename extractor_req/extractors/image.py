"""Extrae información de archivos de imagen."""

import base64
import os


def extract_image(file_path: str, api_key: str | None = None) -> str:
    """Extrae descripción de una imagen.

    Si hay API key de Anthropic disponible, usa Claude Vision para describir la imagen.
    Si no, registra la imagen para análisis manual posterior.
    """
    name = os.path.basename(file_path)
    size_kb = os.path.getsize(file_path) / 1024
    ext = os.path.splitext(file_path)[1].lower()

    # Si tenemos API key, usar Claude Vision
    if api_key:
        try:
            return _analyze_with_claude(file_path, ext, api_key)
        except Exception as e:
            return f"[Error analizando imagen con Claude Vision: {e}]\nRuta: {file_path}"

    return (
        f"[IMAGEN: {name} ({size_kb:.0f} KB)]\n"
        f"Ruta: {file_path}\n"
        f"Esta imagen debe analizarse visualmente para extraer su contenido."
    )


def _analyze_with_claude(file_path: str, ext: str, api_key: str) -> str:
    """Analiza una imagen usando Claude Vision API."""
    import anthropic

    media_types = {
        ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".bmp": "image/bmp", ".tiff": "image/tiff", ".gif": "image/gif",
        ".webp": "image/webp",
    }
    media_type = media_types.get(ext, "image/png")

    with open(file_path, "rb") as f:
        data = base64.standard_b64encode(f.read()).decode("utf-8")

    client = anthropic.Anthropic(api_key=api_key)
    msg = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": data}},
                {"type": "text", "text": (
                    "Describe detalladamente el contenido de esta imagen. "
                    "Si contiene texto, transcríbelo. Si es un diagrama, describe su estructura. "
                    "Si es una captura de pantalla, describe la interfaz y datos visibles. Responde en español."
                )},
            ],
        }],
    )
    return msg.content[0].text
