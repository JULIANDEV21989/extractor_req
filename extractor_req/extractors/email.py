"""Extrae contenido de archivos de correo electrónico (.eml y .msg)."""

import email
import os
from email import policy


def extract_email(file_path: str) -> str:
    """Extrae contenido de un archivo de correo (.eml o .msg)."""
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".eml":
        return _extract_eml(file_path)
    elif ext == ".msg":
        return _extract_msg(file_path)
    return f"[Formato de correo no soportado: {ext}]"


def _extract_eml(file_path: str) -> str:
    """Extrae contenido de un archivo .eml."""
    with open(file_path, "rb") as f:
        msg = email.message_from_binary_file(f, policy=policy.default)

    parts = [
        f"**De:** {msg.get('From', 'N/A')}",
        f"**Para:** {msg.get('To', 'N/A')}",
        f"**CC:** {msg.get('Cc', 'N/A')}" if msg.get('Cc') else "",
        f"**Fecha:** {msg.get('Date', 'N/A')}",
        f"**Asunto:** {msg.get('Subject', 'N/A')}",
        "",
    ]

    # Extraer cuerpo
    body = msg.get_body(preferencelist=("plain", "html"))
    if body:
        content = body.get_content()
        if isinstance(content, bytes):
            content = content.decode("utf-8", errors="replace")
        parts.append(content)

    # Listar adjuntos
    attachments = [part.get_filename() for part in msg.iter_attachments()]
    if attachments:
        parts.append(f"\n**Adjuntos:** {', '.join(a for a in attachments if a)}")

    return "\n".join(p for p in parts if p)


def _extract_msg(file_path: str) -> str:
    """Extrae contenido de un archivo .msg de Outlook."""
    try:
        import extract_msg
        msg = extract_msg.Message(file_path)
        parts = [
            f"**De:** {msg.sender or 'N/A'}",
            f"**Para:** {msg.to or 'N/A'}",
            f"**CC:** {msg.cc}" if msg.cc else "",
            f"**Fecha:** {msg.date or 'N/A'}",
            f"**Asunto:** {msg.subject or 'N/A'}",
            "",
            msg.body or "[Sin cuerpo]",
        ]
        if msg.attachments:
            names = [a.longFilename or a.shortFilename for a in msg.attachments]
            parts.append(f"\n**Adjuntos:** {', '.join(n for n in names if n)}")
        msg.close()
        return "\n".join(p for p in parts if p)
    except ImportError:
        return "[Para procesar .msg instala: pip install extract-msg]"
