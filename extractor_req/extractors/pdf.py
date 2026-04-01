"""Extrae texto de archivos PDF usando PyMuPDF, optimizado para LLM.

Incluye OCR automático para PDFs escaneados (páginas sin texto seleccionable).
"""

import pymupdf
import pymupdf4llm


def extract_pdf(file_path: str) -> str:
    """Extrae contenido de un PDF como Markdown.

    Estrategia de 4 niveles:
    1. pymupdf4llm con OCR automático (detecta páginas escaneadas)
    2. pymupdf4llm sin OCR (si el OCR falla por dependencias)
    3. Extracción básica por página con PyMuPDF
    4. Extracción profunda de bloques de texto
    """
    # Intento 1: pymupdf4llm con OCR habilitado (auto-detecta páginas escaneadas)
    try:
        md_text = pymupdf4llm.to_markdown(file_path, show_progress=False)
        if len(md_text.strip()) > 50:
            return md_text.strip()
    except Exception:
        pass

    # Intento 2: pymupdf4llm estándar (sin OCR, por si el OCR no está instalado)
    try:
        md_text = pymupdf4llm.to_markdown(file_path, show_progress=False)
        if len(md_text.strip()) > 50:
            return md_text.strip()
    except Exception:
        pass

    # Intento 3: extracción básica por página
    try:
        doc = pymupdf.open(file_path)
        pages = []
        has_text = False
        for i, page in enumerate(doc):
            text = page.get_text("text")
            if text.strip():
                has_text = True
                pages.append(f"### Página {i + 1}\n\n{text.strip()}")
        doc.close()
        if pages:
            return "\n\n".join(pages)

        # Si no hay texto en ninguna página, intentar OCR con EasyOCR
        if not has_text:
            ocr_result = _try_easyocr_on_pdf(file_path)
            if ocr_result:
                return ocr_result
    except Exception:
        pass

    # Intento 4: extracción profunda de bloques
    try:
        doc = pymupdf.open(file_path)
        all_text = []
        for page in doc:
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                if block.get("type") == 0:
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            if span.get("text", "").strip():
                                all_text.append(span["text"])
        doc.close()
        if all_text:
            return " ".join(all_text)
    except Exception:
        pass

    return "[PDF sin contenido textual extraíble - posible imagen escaneada. Instala easyocr para OCR: pip install easyocr]"


def _try_easyocr_on_pdf(file_path: str) -> str | None:
    """Intenta OCR en páginas del PDF usando EasyOCR (si está instalado)."""
    try:
        import easyocr
        import io
    except ImportError:
        return None

    try:
        doc = pymupdf.open(file_path)
        reader = easyocr.Reader(["es", "en"], gpu=False, verbose=False)
        pages_text = []

        for i, page in enumerate(doc):
            # Renderizar página como imagen
            pix = page.get_pixmap(dpi=200)
            img_bytes = pix.tobytes("png")

            # OCR en la imagen
            results = reader.readtext(img_bytes)
            page_text = " ".join([r[1] for r in results if r[2] > 0.3])  # confianza > 30%
            if page_text.strip():
                pages_text.append(f"### Página {i + 1} (OCR)\n\n{page_text.strip()}")

        doc.close()
        if pages_text:
            return "\n\n".join(pages_text)
    except Exception:
        pass

    return None
