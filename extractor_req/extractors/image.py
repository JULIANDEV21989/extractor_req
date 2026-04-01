"""Extrae información de archivos de imagen.

Estrategia:
1. Claude Vision API (si hay API key) — mejor calidad, describe + transcribe
2. EasyOCR local (si está instalado) — OCR offline sin costo
3. Placeholder informativo (último recurso)
"""

import base64
import os


def extract_image(file_path: str, api_key: str | None = None) -> str:
    """Extrae contenido de una imagen.

    Prioridad:
    1. Claude Vision (requiere API key) — descripción + OCR semántico
    2. EasyOCR (requiere pip install easyocr) — OCR local gratuito
    3. Placeholder con metadata
    """
    name = os.path.basename(file_path)
    size_kb = os.path.getsize(file_path) / 1024
    ext = os.path.splitext(file_path)[1].lower()

    # Opción 1: Claude Vision
    if api_key:
        try:
            return _analyze_with_claude(file_path, ext, api_key)
        except Exception as e:
            pass  # Fall through to OCR

    # Opción 2: EasyOCR local
    ocr_result = _try_easyocr(file_path)
    if ocr_result:
        return f"**Imagen:** {name} ({size_kb:.0f} KB)\n**Texto extraído (OCR):**\n\n{ocr_result}"

    # Opción 3: Placeholder
    return (
        f"[IMAGEN: {name} ({size_kb:.0f} KB)]\n"
        f"Ruta: {file_path}\n"
        f"Para extraer texto automáticamente:\n"
        f"  - Configura ANTHROPIC_API_KEY (Claude Vision)\n"
        f"  - O instala EasyOCR: pip install easyocr"
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
                    "Si contiene texto, transcríbelo completo. Si es un diagrama, describe su estructura. "
                    "Si es una captura de pantalla, describe la interfaz y datos visibles. "
                    "Si tiene tablas, reconstruye la tabla. Responde en español."
                )},
            ],
        }],
    )
    return msg.content[0].text


def _try_easyocr(file_path: str) -> str | None:
    """Intenta OCR local usando EasyOCR. Retorna None si no está instalado."""
    try:
        import easyocr
    except ImportError:
        return None

    try:
        reader = easyocr.Reader(["es", "en"], gpu=False, verbose=False)
        results = reader.readtext(file_path)
        # Filtrar por confianza y construir texto
        texts = [r[1] for r in results if r[2] > 0.3]
        if texts:
            return "\n".join(texts)
    except Exception:
        pass

    return None
