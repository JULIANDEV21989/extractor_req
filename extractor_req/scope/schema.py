"""Schema del JSON que Claude genera para el documento de alcance.

Se usa TypedDict en vez de dataclasses para parsear directamente desde JSON.
Los renderers (mockup_generator, docx_builder) consumen estos dicts.
"""

from __future__ import annotations

from typing import TypedDict


class Quote(TypedDict, total=False):
    text: str
    author: str


class BulletPoint(TypedDict):
    bold_prefix: str
    text: str


class ProjectInfo(TypedDict):
    title: str
    subtitle: str
    company_name: str
    version: str
    date: str
    prepared_by: str
    confidentiality_notice: str


class ExecutiveSummary(TypedDict, total=False):
    problem_description: str
    problem_quote: Quote
    solution_description: str
    solution_bullets: list[BulletPoint]
    solution_quote: Quote
    unchanged_items: list[BulletPoint]


class Stakeholder(TypedDict):
    name: str
    role: str
    title: str
    approval_required: bool


class CellBadge(TypedDict):
    text: str
    color: str  # "primary", "success", "warning", "info", "danger", "muted"


class TableSpec(TypedDict, total=False):
    headers: list[str]
    rows: list[list]  # str | CellBadge
    column_widths: list[int]


class KPICard(TypedDict):
    value: str
    label: str
    accent_color: str


class AlertItem(TypedDict):
    text: str
    severity: str


class NavUser(TypedDict, total=False):
    name: str
    role: str


class ButtonSpec(TypedDict):
    text: str
    style: str


class DetailSection(TypedDict, total=False):
    title: str
    fields: list[list[str]]  # [[label, value], ...]
    table: TableSpec
    buttons: list[ButtonSpec]
    timeline_events: list[list[str]]  # [[date, description, who], ...]


class FormField(TypedDict, total=False):
    label: str
    value: str
    field_type: str  # "text", "select", "checkbox"


class ScreenDefinition(TypedDict, total=False):
    id: str
    title: str
    screen_type: str  # "dashboard" | "list" | "detail" | "form" | "validation"
    description: str
    nav_user: NavUser
    kpis: list[KPICard]
    table: TableSpec
    search_placeholder: str
    filters: list[str]
    detail_sections: list[DetailSection]
    form_fields: list[FormField]
    alerts: list[AlertItem]
    buttons: list[ButtonSpec]
    confirmation_dialog: dict  # title, items list, confirm_text


class FlowColumn(TypedDict):
    name: str
    color: str


class FlowStep(TypedDict):
    column_index: int
    text: str
    y_position: int  # relative position 0-100


class FlowAnnotation(TypedDict, total=False):
    from_column: int
    to_column: int
    y_position: int
    label: str


class ProcessFlow(TypedDict):
    title: str
    columns: list[FlowColumn]
    steps: list[FlowStep]
    annotations: list[FlowAnnotation]


class StateNode(TypedDict):
    name: str
    description: str
    triggered_by: str
    color: str


class StateLifecycle(TypedDict):
    title: str
    states: list[StateNode]


class SystemBox(TypedDict):
    name: str
    description: str
    infrastructure: str
    color: str


class SystemConnection(TypedDict):
    from_system: str
    to_system: str
    label: str
    direction: str  # "one_way" | "bidirectional"


class IntegrationDiagram(TypedDict, total=False):
    title: str
    systems: list[SystemBox]
    connections: list[SystemConnection]
    footnotes: list[str]


class ComparisonStep(TypedDict):
    number: str
    text: str
    status: str  # "neutral", "manual", "automated"


class BeforeAfterComparison(TypedDict):
    title: str
    before_title: str
    before_steps: list[ComparisonStep]
    before_time: str
    after_title: str
    after_steps: list[ComparisonStep]
    after_time: str
    improvement_callout: str


class RoleColumn(TypedDict):
    name: str
    role_label: str


class PermissionRow(TypedDict):
    action: str
    values: list[bool]


class RolesMatrix(TypedDict):
    title: str
    role_columns: list[RoleColumn]
    permissions: list[PermissionRow]


class WorkedExample(TypedDict, total=False):
    title: str
    subtitle: str
    data_table: TableSpec
    timeline: TableSpec
    documents: list[str]
    quote: Quote
    comparison_table: TableSpec


class Exclusion(TypedDict):
    item: str
    reason: str


class ProjectPhase(TypedDict):
    name: str
    duration: str
    description: str
    deliverables: list[str]
    start_day: int
    duration_days: int
    color: str


class InvestmentLine(TypedDict):
    concept: str
    cost: str
    cost_type: str


class FAQItem(TypedDict):
    question: str
    answer: str


class GlossaryTerm(TypedDict):
    term: str
    definition: str


class SignatureBlock(TypedDict):
    name: str
    title: str


class ScopeSpec(TypedDict):
    project: ProjectInfo
    executive_summary: ExecutiveSummary
    stakeholders: list[Stakeholder]
    screens: list[ScreenDefinition]
    process_flow: ProcessFlow
    state_lifecycle: StateLifecycle
    integrations: IntegrationDiagram
    before_after: BeforeAfterComparison
    roles_matrix: RolesMatrix
    examples: list[WorkedExample]
    exclusions: list[Exclusion]
    phases: list[ProjectPhase]
    investment: list[InvestmentLine]
    faq: list[FAQItem]
    glossary: list[GlossaryTerm]
    signatures: list[SignatureBlock]


# JSON Schema documentation string for embedding in Claude prompt
SCHEMA_DOCS = '''
{
  "project": {
    "title": "string - Titulo del proyecto",
    "subtitle": "string - Subtitulo (ej: Documento de Alcance para Aprobacion)",
    "company_name": "string - Nombre de la empresa",
    "version": "string - Version del documento (ej: 1.0)",
    "date": "string - Fecha (ej: Abril 2026)",
    "prepared_by": "string - Nombre del autor",
    "confidentiality_notice": "string - Aviso de confidencialidad"
  },
  "executive_summary": {
    "problem_description": "string - Descripcion del problema en 2-3 parrafos, lenguaje no tecnico",
    "problem_quote": {"text": "string - Cita textual de un stakeholder", "author": "string"},
    "solution_description": "string - Descripcion de la solucion en 1-2 parrafos",
    "solution_bullets": [{"bold_prefix": "string - Parte en negrita", "text": "string - Resto del texto"}],
    "solution_quote": {"text": "string", "author": "string"},
    "unchanged_items": [{"bold_prefix": "string", "text": "string - Lo que NO cambia"}]
  },
  "stakeholders": [{"name": "string", "role": "string", "title": "string", "approval_required": true}],
  "screens": [
    {
      "id": "string - ID unico (ej: dashboard, list_ops, detail_op, form_create, validation)",
      "title": "string - Titulo de la pantalla",
      "screen_type": "string - dashboard|list|detail|form|validation",
      "description": "string - Descripcion breve de la pantalla",
      "nav_user": {"name": "string - Usuario ejemplo", "role": "string - Rol ejemplo"},
      "kpis": [{"value": "string", "label": "string", "accent_color": "primary|success|warning|info|danger|muted"}],
      "table": {"headers": ["string"], "rows": [["string o {text,color} para badges"]], "column_widths": [100]},
      "search_placeholder": "string - Placeholder del buscador",
      "filters": ["string - Nombres de filtros"],
      "detail_sections": [{"title": "string", "fields": [["label","value"]], "table": {}, "buttons": [{"text":"string","style":"primary"}], "timeline_events": [["fecha","descripcion","quien"]]}],
      "form_fields": [{"label": "string", "value": "string", "field_type": "text|select|checkbox"}],
      "alerts": [{"text": "string", "severity": "warning|danger|info"}],
      "buttons": [{"text": "string", "style": "primary|secondary|danger|muted"}],
      "confirmation_dialog": {"title": "string", "items": ["string"], "confirm_text": "string"}
    }
  ],
  "process_flow": {
    "title": "string",
    "columns": [{"name": "string", "color": "primary|secondary|info|muted"}],
    "steps": [{"column_index": 0, "text": "string", "y_position": 0}],
    "annotations": [{"from_column": 0, "to_column": 1, "y_position": 0, "label": "string"}]
  },
  "state_lifecycle": {
    "title": "string",
    "states": [{"name": "string", "description": "string", "triggered_by": "string", "color": "info|warning|success|primary|muted|dark"}]
  },
  "integrations": {
    "title": "string",
    "systems": [{"name": "string", "description": "string", "infrastructure": "string", "color": "secondary|primary|info"}],
    "connections": [{"from_system": "string", "to_system": "string", "label": "string", "direction": "one_way|bidirectional"}],
    "footnotes": ["string"]
  },
  "before_after": {
    "title": "string",
    "before_title": "string (ej: PROCESO ACTUAL (MANUAL))",
    "before_steps": [{"number": "1", "text": "string", "status": "neutral|manual"}],
    "before_time": "string (ej: 45-60 min/operacion)",
    "after_title": "string (ej: PROCESO NUEVO (CON EL PORTAL))",
    "after_steps": [{"number": "1", "text": "string", "status": "neutral|automated"}],
    "after_time": "string (ej: 10-15 min/operacion)",
    "improvement_callout": "string (ej: 75% menos tiempo)"
  },
  "roles_matrix": {
    "title": "string",
    "role_columns": [{"name": "string", "role_label": "string"}],
    "permissions": [{"action": "string", "values": [true, false]}]
  },
  "examples": [
    {
      "title": "string - Titulo del ejemplo",
      "subtitle": "string - Descripcion breve",
      "data_table": {"headers": ["Campo", "Valor"], "rows": [["string","string"]]},
      "timeline": {"headers": ["Fecha", "Evento", "Pantalla"], "rows": [[]]},
      "documents": ["string - nombre de documento"],
      "quote": {"text": "string", "author": "string"}
    }
  ],
  "exclusions": [{"item": "string", "reason": "string"}],
  "phases": [{"name": "string", "duration": "string", "description": "string", "deliverables": ["string"], "start_day": 0, "duration_days": 5, "color": "primary|info|success"}],
  "investment": [{"concept": "string", "cost": "string", "cost_type": "string"}],
  "faq": [{"question": "string", "answer": "string"}],
  "glossary": [{"term": "string", "definition": "string"}],
  "signatures": [{"name": "string", "title": "string"}]
}
'''
