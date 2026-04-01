"""Genera la especificacion JSON del documento de alcance usando Claude.

Segundo call a Claude: toma el requerimiento tecnico + consolidado y produce
un JSON estructurado que los renderers (mockups + DOCX) consumen.
"""

from __future__ import annotations

import json
import os
import re

import anthropic

from ..scope.schema import SCHEMA_DOCS

SYSTEM_PROMPT = """Eres un consultor senior de tecnologia especializado en crear documentos de alcance
para stakeholders no tecnicos.

Tu trabajo es analizar un documento de requerimientos tecnicos y el contenido consolidado
del levantamiento de informacion original, y producir una ESPECIFICACION ESTRUCTURADA EN JSON
que servira para generar automaticamente:
1. Mockups visuales (imagenes PNG) de las pantallas propuestas
2. Diagramas profesionales (flujo, estados, integraciones, antes/despues, roles)
3. Un documento DOCX profesional de alcance para aprobacion de stakeholders

REGLAS CRITICAS:
- Responde EXCLUSIVAMENTE con un JSON valido. Sin texto antes ni despues del JSON.
- Si necesitas envolver el JSON en un bloque de codigo, usa ```json ... ```
- Usa datos REALES extraidos del levantamiento (nombres de personas, cifras, operaciones, clientes).
- Las pantallas deben reflejar la solucion concreta descrita en los requerimientos.
- Incluye citas textuales de los stakeholders cuando las haya en el contenido consolidado.
- Los roles y permisos deben coincidir con los actores identificados.
- Los estados y flujos deben coincidir con los procesos de negocio documentados.
- Escribe TODO el contenido del JSON en espanol.
- Los datos de ejemplo en tablas y KPIs deben ser verosimiles y coherentes entre si.
- Cada pantalla debe tener datos suficientes para renderizar un mockup completo.
- Genera al menos 5 pantallas: dashboard, lista, detalle, formulario, validacion.
- Genera al menos 1 ejemplo completo con datos reales (walked example).
- Los KPIs del dashboard deben usar cifras realistas basadas en el volumen de operaciones mencionado.
- El cronograma debe ser realista y mencionar desarrollo con IA si el requerimiento lo indica."""

USER_PROMPT_TEMPLATE = """A partir del siguiente requerimiento tecnico y contenido consolidado del levantamiento,
genera una especificacion JSON COMPLETA para el documento de alcance de stakeholders.

El JSON debe seguir EXACTAMENTE esta estructura:

{schema_docs}

INSTRUCCIONES ESPECIFICAS:

1. **project**: Usa el nombre real del proyecto, empresa y personas del levantamiento.
2. **executive_summary**: Redacta en lenguaje no tecnico. Incluye citas textuales de stakeholders si existen en el consolidado.
3. **screens**: Genera al menos 5 pantallas con datos reales o verosimiles:
   - dashboard: con 4-6 KPIs y tabla de operaciones recientes
   - list: con busqueda, filtros, y tabla con badges de estado
   - detail: con secciones de datos, costes, documentos, historial
   - form o validation: segun el flujo del negocio
   - Una pantalla adicional relevante al dominio
4. **process_flow**: 3-4 columnas representando actores/sistemas. Los steps usan y_position de 0 a 100 para posicionar verticalmente.
5. **state_lifecycle**: 4-6 estados que representen el ciclo de vida de la entidad principal.
6. **before_after**: Comparativa concreta del proceso manual vs automatizado, con tiempos estimados.
7. **roles_matrix**: Basada en los actores reales identificados.
8. **examples**: Al menos 1 ejemplo con datos reales del levantamiento (nombres, cifras, fechas).
9. **phases**: Cada fase con start_day y duration_days para el gantt.
10. **signatures**: Incluye a los stakeholders que deben aprobar.

---

REQUERIMIENTO TECNICO:

{requirements_content}

---

CONTENIDO CONSOLIDADO DEL LEVANTAMIENTO (extracto):

{consolidated_content}"""


def _extract_json(text: str) -> dict:
    """Extract and parse JSON from Claude's response, handling common issues."""
    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try extracting from ```json ... ``` block
    match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Try extracting from first { to last }
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = text[start:end + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            # Try cleaning trailing commas
            cleaned = re.sub(r",\s*([}\]])", r"\1", candidate)
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                pass

    raise ValueError(
        "No se pudo parsear el JSON de la respuesta de Claude. "
        f"Primeros 500 chars: {text[:500]}"
    )


def generate_scope_spec(
    requirements_content: str,
    consolidated_content: str,
    api_key: str | None = None,
    model: str = "claude-sonnet-4-20250514",
    max_tokens: int = 16000,
) -> dict:
    """Generate the scope specification JSON using Claude.

    Args:
        requirements_content: The requirements document (from analyzer phase)
        consolidated_content: The consolidated content from extraction
        api_key: Anthropic API key
        model: Claude model to use
        max_tokens: Max response tokens

    Returns:
        Parsed ScopeSpec dict conforming to the schema
    """
    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise ValueError("Se necesita API key de Anthropic para generar el documento de alcance.")

    client = anthropic.Anthropic(api_key=key)

    # Truncate inputs if needed to stay within context limits
    max_req = 100_000
    max_consolidated = 400_000
    if len(requirements_content) > max_req:
        requirements_content = requirements_content[:max_req] + "\n[... TRUNCADO ...]"
    if len(consolidated_content) > max_consolidated:
        consolidated_content = consolidated_content[:max_consolidated] + "\n[... TRUNCADO ...]"

    user_prompt = USER_PROMPT_TEMPLATE.format(
        schema_docs=SCHEMA_DOCS,
        requirements_content=requirements_content,
        consolidated_content=consolidated_content,
    )

    message = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    response_text = message.content[0].text
    return _extract_json(response_text)
