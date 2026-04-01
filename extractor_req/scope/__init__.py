"""Generador de documento de alcance profesional para stakeholders."""

from .mockup_generator import generate_mockups
from .docx_builder import build_scope_docx

__all__ = ["generate_mockups", "build_scope_docx"]
