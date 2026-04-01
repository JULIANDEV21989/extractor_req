"""Detecta colores corporativos y datos de branding a partir del contenido consolidado.

Usa una llamada ligera a Claude para analizar menciones de empresa, logos,
colores, y contexto del negocio, y sugiere una paleta de colores apropiada.
"""

from __future__ import annotations

import json
import os
import re

import anthropic

SYSTEM_PROMPT = """Eres un experto en branding corporativo. Tu trabajo es analizar documentacion
de un proyecto y detectar o inferir los colores corporativos de la empresa involucrada.

REGLAS:
- Responde EXCLUSIVAMENTE con un JSON valido. Sin texto antes ni despues.
- Si encuentras menciones explicitas de colores, usalos.
- Si encuentras el nombre de la empresa, busca en tu conocimiento si conoces sus colores.
- Si no hay informacion clara, infiere colores apropiados segun el sector/industria.
- Siempre sugiere un color primario y uno secundario en formato hex.
- Incluye una breve justificacion de por que sugieres esos colores.
- Responde en espanol."""

USER_PROMPT_TEMPLATE = """Analiza el siguiente extracto de documentacion de un proyecto y detecta
o infiere los colores corporativos de la empresa principal involucrada.

Responde con este JSON exacto:

{{
  "company_name": "Nombre de la empresa detectada",
  "industry": "Sector/industria (ej: logistica, tecnologia, salud)",
  "primary_color": "#XXXXXX",
  "primary_color_name": "nombre del color (ej: Rojo corporativo)",
  "secondary_color": "#XXXXXX",
  "secondary_color_name": "nombre del color (ej: Negro)",
  "confidence": "alta|media|baja",
  "reasoning": "Explicacion breve de por que sugieres estos colores",
  "alternative_palettes": [
    {{
      "name": "Nombre de la alternativa (ej: Profesional Azul)",
      "primary_color": "#XXXXXX",
      "secondary_color": "#XXXXXX",
      "description": "Descripcion breve"
    }},
    {{
      "name": "Nombre de la alternativa (ej: Corporativo Verde)",
      "primary_color": "#XXXXXX",
      "secondary_color": "#XXXXXX",
      "description": "Descripcion breve"
    }}
  ]
}}

Siempre incluye al menos 2 paletas alternativas ademas de la principal.
Las alternativas deben ser profesionales y apropiadas para el sector.

---

EXTRACTO DE LA DOCUMENTACION (primeros 5000 caracteres):

{content_extract}"""


def _extract_json(text: str) -> dict:
    """Extract JSON from Claude response."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            cleaned = re.sub(r",\s*([}\]])", r"\1", text[start:end + 1])
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                pass
    return {}


def detect_branding(
    consolidated_content: str,
    api_key: str | None = None,
    model: str = "claude-sonnet-4-20250514",
) -> dict:
    """Analyze consolidated content and suggest branding colors.

    Args:
        consolidated_content: The consolidated markdown content
        api_key: Anthropic API key
        model: Claude model to use (uses a fast/cheap call)

    Returns:
        Dict with company_name, primary_color, secondary_color,
        confidence, reasoning, and alternative_palettes.
    """
    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return _fallback_branding()

    client = anthropic.Anthropic(api_key=key)

    # Only send first 5000 chars — enough to detect company/context
    extract = consolidated_content[:5000]

    try:
        message = client.messages.create(
            model=model,
            max_tokens=1500,
            system=SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": USER_PROMPT_TEMPLATE.format(content_extract=extract),
            }],
        )
        result = _extract_json(message.content[0].text)
        if result and result.get("primary_color"):
            return result
    except Exception:
        pass

    return _fallback_branding()


def _fallback_branding() -> dict:
    """Return default branding when detection fails."""
    return {
        "company_name": "Empresa",
        "industry": "General",
        "primary_color": "#1565C0",
        "primary_color_name": "Azul profesional",
        "secondary_color": "#1A1A1A",
        "secondary_color_name": "Negro",
        "confidence": "baja",
        "reasoning": "No se pudo detectar la empresa. Se usan colores profesionales por defecto.",
        "alternative_palettes": [
            {
                "name": "Corporativo Rojo",
                "primary_color": "#C41E2A",
                "secondary_color": "#1A1A1A",
                "description": "Rojo ejecutivo con negro — transmite energia y profesionalismo",
            },
            {
                "name": "Moderno Verde",
                "primary_color": "#2E7D32",
                "secondary_color": "#212121",
                "description": "Verde oscuro — confianza, sostenibilidad, tecnologia",
            },
        ],
    }
