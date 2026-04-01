"""Analiza contenido consolidado con Claude para generar requerimientos estructurados."""

import os

import anthropic

SYSTEM_PROMPT = """Eres un analista de sistemas senior especializado en levantamiento de requerimientos.
Tu trabajo es analizar documentación de levantamiento de información (transcripciones de reuniones,
documentos operativos, correos, etc.) y producir un documento de requerimientos técnicos estructurado
y completo para un equipo de desarrollo.

REGLAS:
- Sé exhaustivo: no omitas información relevante
- Prioriza con MoSCoW (Must/Should/Could/Won't)
- Identifica TODOS los actores/stakeholders mencionados
- Documenta los procesos de negocio tal como se describen, no como deberían ser
- Detecta integraciones entre sistemas
- Identifica riesgos y restricciones
- Incluye un glosario con términos del dominio del negocio
- El documento debe ser accionable para un equipo de desarrollo
- Responde SIEMPRE en español"""

USER_PROMPT_TEMPLATE = """Analiza el siguiente contenido consolidado de un levantamiento de información
y genera un DOCUMENTO DE REQUERIMIENTOS TÉCNICOS completo y estructurado.

El documento DEBE contener estas secciones:

1. **Resumen Ejecutivo** - Qué se necesita construir y por qué
2. **Actores / Stakeholders** - Tabla con nombre, rol e interacción con el sistema
3. **Procesos de Negocio Detectados** - Flujos paso a paso tal como se describieron
4. **Requerimientos Funcionales** - Priorizados con MoSCoW (Must/Should/Could/Won't), cada uno con ID, nombre y detalle
5. **Requerimientos No Funcionales** - Rendimiento, seguridad, acceso, integración
6. **Integraciones Requeridas** - Tabla con sistema, tipo, dirección y datos
7. **Restricciones y Dependencias** - Limitaciones técnicas, de negocio o presupuesto
8. **Riesgos Identificados** - Tabla con probabilidad, impacto y mitigación
9. **Alcance Propuesto** - In-scope (Fase 1) y Out-of-scope (futuras fases)
10. **Glosario** - Términos del dominio con definiciones claras
11. **Datos del Contexto de Negocio** - Empresas, direcciones, contactos mencionados

---

CONTENIDO CONSOLIDADO DEL LEVANTAMIENTO:

{consolidated_content}"""


def analyze_requirements(
    consolidated_content: str,
    api_key: str | None = None,
    model: str = "claude-sonnet-4-20250514",
    max_tokens: int = 16000,
) -> str:
    """Envía el contenido consolidado a Claude para generar el requerimiento estructurado.

    Args:
        consolidated_content: Texto Markdown consolidado de todas las fuentes
        api_key: Anthropic API key (o usa env var ANTHROPIC_API_KEY)
        model: Modelo de Claude a usar
        max_tokens: Tokens máximos de respuesta

    Returns:
        Documento de requerimientos en Markdown
    """
    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise ValueError(
            "Se necesita API key de Anthropic. Configúrala en config.yaml, "
            "pásala con --api-key, o establece ANTHROPIC_API_KEY como variable de entorno."
        )

    client = anthropic.Anthropic(api_key=key)

    # Si el contenido es muy largo, truncar con aviso
    max_input_chars = 800_000  # ~200K tokens aprox
    if len(consolidated_content) > max_input_chars:
        consolidated_content = consolidated_content[:max_input_chars] + (
            "\n\n[... CONTENIDO TRUNCADO POR LÍMITE DE CONTEXTO ...]"
        )

    message = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": USER_PROMPT_TEMPLATE.format(consolidated_content=consolidated_content),
        }],
    )

    return message.content[0].text
