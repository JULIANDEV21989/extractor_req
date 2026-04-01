"""Extractores de contenido por tipo de archivo."""

from .pdf import extract_pdf
from .docx import extract_docx
from .video import extract_video
from .image import extract_image
from .email import extract_email

__all__ = ["extract_pdf", "extract_docx", "extract_video", "extract_image", "extract_email"]
