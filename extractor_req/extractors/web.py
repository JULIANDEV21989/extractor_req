"""Extrae contenido de páginas web y archivos HTML locales.

Usa trafilatura para extracción inteligente de contenido principal
(ignora menús, ads, footers, navegación).
"""

from __future__ import annotations

import os


def extract_web(file_path: str) -> str:
    """Extrae contenido de un archivo HTML local o archivo con URLs.

    Si el archivo es .html/.htm: extrae contenido directamente.
    Si el archivo es .url o .txt con URLs: descarga y extrae cada URL.
    """
    ext = os.path.splitext(file_path)[1].lower()
    name = os.path.basename(file_path)

    if ext in (".html", ".htm"):
        return _extract_local_html(file_path, name)
    else:
        return f"[Formato web no soportado: {ext}. Usa archivos .html o .htm]"


def extract_urls(urls: list[str]) -> str:
    """Extrae contenido de una lista de URLs.

    Args:
        urls: Lista de URLs a procesar

    Returns:
        Markdown con contenido extraído de cada URL
    """
    if not urls:
        return "[No se proporcionaron URLs]"

    parts = [f"**URLs procesadas:** {len(urls)}\n"]

    for url in urls:
        url = url.strip()
        if not url or url.startswith("#"):
            continue
        parts.append(f"#### {url}\n")
        content = _extract_from_url(url)
        parts.append(content)
        parts.append("")

    return "\n".join(parts)


def _extract_local_html(file_path: str, name: str) -> str:
    """Extrae contenido de un archivo HTML local."""
    try:
        import trafilatura
    except ImportError:
        return _fallback_html_extraction(file_path, name)

    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            html_content = f.read()

        text = trafilatura.extract(
            html_content,
            include_tables=True,
            include_links=True,
            include_comments=False,
            output_format="txt",
        )

        if text and len(text.strip()) > 20:
            metadata = trafilatura.extract(html_content, output_format="json")
            header = f"**Archivo HTML:** {name}\n"
            return header + text.strip()

    except Exception as e:
        return f"[Error extrayendo HTML {name}: {e}]"

    return _fallback_html_extraction(file_path, name)


def _extract_from_url(url: str) -> str:
    """Descarga y extrae contenido de una URL."""
    try:
        import trafilatura
    except ImportError:
        return (
            f"[trafilatura no instalado. Instala con: pip install trafilatura]\n"
            f"URL: {url}"
        )

    try:
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return f"[No se pudo descargar: {url}]"

        text = trafilatura.extract(
            downloaded,
            include_tables=True,
            include_links=True,
            include_comments=False,
            output_format="txt",
        )

        if text and len(text.strip()) > 20:
            return text.strip()

        return f"[Sin contenido extraíble en: {url}]"

    except Exception as e:
        return f"[Error procesando URL {url}: {e}]"


def _fallback_html_extraction(file_path: str, name: str) -> str:
    """Extracción básica de HTML sin trafilatura (BeautifulSoup o texto plano)."""
    try:
        from html.parser import HTMLParser

        class TextExtractor(HTMLParser):
            def __init__(self):
                super().__init__()
                self.texts = []
                self._skip = False

            def handle_starttag(self, tag, attrs):
                if tag in ("script", "style", "nav", "footer", "header"):
                    self._skip = True

            def handle_endtag(self, tag):
                if tag in ("script", "style", "nav", "footer", "header"):
                    self._skip = False

            def handle_data(self, data):
                if not self._skip and data.strip():
                    self.texts.append(data.strip())

        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            html = f.read()

        parser = TextExtractor()
        parser.feed(html)

        if parser.texts:
            return f"**Archivo HTML:** {name}\n\n" + "\n".join(parser.texts)

    except Exception:
        pass

    # Último recurso: texto plano
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return f"**Archivo HTML:** {name} (texto sin procesar)\n\n" + f.read()[:10000]
    except Exception as e:
        return f"[Error leyendo {name}: {e}]"
