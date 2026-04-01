"""Extrae texto de archivos PDF usando PyMuPDF, optimizado para LLM."""

import pymupdf
import pymupdf4llm


def extract_pdf(file_path: str) -> str:
    """Extrae contenido de un PDF como Markdown.

    Intenta primero pymupdf4llm (preserva tablas y estructura).
    Si falla o el contenido es escaso, usa extracción básica de PyMuPDF.
    Para PDFs escaneados (imágenes), extrae el texto embebido en imágenes si existe.
    """
    # Intento 1: pymupdf4llm (mejor para tablas y estructura)
    try:
        md_text = pymupdf4llm.to_markdown(file_path)
        if len(md_text.strip()) > 50:
            return md_text.strip()
    except Exception:
        pass

    # Intento 2: extracción básica por página
    try:
        doc = pymupdf.open(file_path)
        pages = []
        for i, page in enumerate(doc):
            text = page.get_text("text")
            if text.strip():
                pages.append(f"### Página {i + 1}\n\n{text.strip()}")
        doc.close()
        if pages:
            return "\n\n".join(pages)
    except Exception:
        pass

    # Intento 3: extraer texto de imágenes embebidas (OCR básico de PyMuPDF)
    try:
        doc = pymupdf.open(file_path)
        all_text = []
        for page in doc:
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                if block.get("type") == 0:  # text block
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            if span.get("text", "").strip():
                                all_text.append(span["text"])
        doc.close()
        if all_text:
            return " ".join(all_text)
    except Exception:
        pass

    return "[PDF sin contenido textual extraíble - posible imagen escaneada sin OCR]"
