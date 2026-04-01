"""Genera mockups PNG profesionales a partir de un ScopeSpec.

Dispatch por screen_type + diagramas fijos (flow, states, integrations, etc.)
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from .drawing import MockupCanvas


@dataclass
class MockupResult:
    id: str
    filename: str
    caption: str
    path: str


W, H = 1400, 900  # default canvas


def generate_mockups(
    spec: dict,
    primary_color: str = "#C41E2A",
    secondary_color: str = "#1A1A1A",
    output_dir: str = "output/mockups",
) -> list[MockupResult]:
    """Generate all mockup PNGs from the scope spec."""
    os.makedirs(output_dir, exist_ok=True)
    results: list[MockupResult] = []
    idx = 1

    # === SCREEN MOCKUPS ===
    for screen in spec.get("screens", []):
        sid = screen.get("id", f"screen_{idx}")
        stype = screen.get("screen_type", "list")
        filename = f"{idx:02d}_{sid}.png"
        path = os.path.join(output_dir, filename)
        caption = screen.get("description", screen.get("title", ""))

        renderer = SCREEN_RENDERERS.get(stype, _render_list)
        renderer(screen, path, primary_color, secondary_color)

        results.append(MockupResult(id=sid, filename=filename, caption=caption, path=path))
        idx += 1

    # === DIAGRAM MOCKUPS (always generated from dedicated spec sections) ===

    # Before/After
    ba = spec.get("before_after")
    if ba:
        max_steps = max(len(ba.get("before_steps", [])), len(ba.get("after_steps", [])))
        h = 180 + max_steps * 42 + 60
        c = MockupCanvas(W, h, primary_color, secondary_color)
        c.draw_comparison(
            ba.get("before_title", "ANTES"), ba.get("before_steps", []), ba.get("before_time", ""),
            ba.get("after_title", "DESPUES"), ba.get("after_steps", []), ba.get("after_time", ""),
            ba.get("improvement_callout", ""),
        )
        fname = f"{idx:02d}_antes_despues.png"
        c.save(os.path.join(output_dir, fname))
        results.append(MockupResult("before_after", fname, ba.get("title", "Antes y Despues"), os.path.join(output_dir, fname)))
        idx += 1

    # Process Flow
    pf = spec.get("process_flow")
    if pf:
        max_y = max((s.get("y_position", 0) for s in pf.get("steps", [])), default=50)
        h = 120 + max_y * 6 + 80
        c = MockupCanvas(W, max(h, 600), primary_color, secondary_color)
        c.draw_flow_diagram(pf.get("columns", []), pf.get("steps", []), pf.get("annotations", []))
        # Title overlay
        c.d.text((30, 12), pf.get("title", "Flujo de Operacion"), fill="#FFFFFF", font=c.font_header_bar)
        fname = f"{idx:02d}_flujo_operacion.png"
        c.save(os.path.join(output_dir, fname))
        results.append(MockupResult("process_flow", fname, pf.get("title", ""), os.path.join(output_dir, fname)))
        idx += 1

    # State Lifecycle
    sl = spec.get("state_lifecycle")
    if sl:
        c = MockupCanvas(W, 350, primary_color, secondary_color)
        c.draw_state_chain(sl.get("title", ""), sl.get("states", []))
        fname = f"{idx:02d}_estados.png"
        c.save(os.path.join(output_dir, fname))
        results.append(MockupResult("state_lifecycle", fname, sl.get("title", ""), os.path.join(output_dir, fname)))
        idx += 1

    # Integrations
    intg = spec.get("integrations")
    if intg:
        c = MockupCanvas(W, 450, primary_color, secondary_color)
        c.draw_system_boxes(
            intg.get("title", ""), intg.get("systems", []),
            intg.get("connections", []), intg.get("footnotes"),
        )
        fname = f"{idx:02d}_integraciones.png"
        c.save(os.path.join(output_dir, fname))
        results.append(MockupResult("integrations", fname, intg.get("title", ""), os.path.join(output_dir, fname)))
        idx += 1

    # Roles Matrix
    rm = spec.get("roles_matrix")
    if rm:
        n_rows = len(rm.get("permissions", []))
        h = 120 + 40 + n_rows * 32
        c = MockupCanvas(W, h, primary_color, secondary_color)
        c.draw_roles_table(rm.get("title", ""), rm.get("role_columns", []), rm.get("permissions", []))
        fname = f"{idx:02d}_roles_permisos.png"
        c.save(os.path.join(output_dir, fname))
        results.append(MockupResult("roles_matrix", fname, rm.get("title", ""), os.path.join(output_dir, fname)))
        idx += 1

    # Phases/Gantt
    phases = spec.get("phases", [])
    if phases:
        h = 120 + len(phases) * 65 + 80
        c = MockupCanvas(W, h, primary_color, secondary_color)
        c.draw_gantt("Fases de Entrega y Calendario", phases)
        fname = f"{idx:02d}_fases_calendario.png"
        c.save(os.path.join(output_dir, fname))
        results.append(MockupResult("phases", fname, "Fases de Entrega", os.path.join(output_dir, fname)))
        idx += 1

    return results


# === SCREEN RENDERERS ===

def _render_dashboard(screen: dict, path: str, primary: str, secondary: str):
    kpis = screen.get("kpis", [])
    table = screen.get("table", {})
    alerts = screen.get("alerts", [])
    rows = table.get("rows", [])
    h = 280 + len(rows) * 32 + len(alerts) * 30 + 80
    c = MockupCanvas(W, max(h, 700), primary, secondary)
    nav = screen.get("nav_user", {})
    c.draw_header("Portal", nav.get("name", ""), nav.get("role", ""))

    y = c.draw_section_title(30, 75, screen.get("title", "Dashboard"))

    # KPI cards
    if kpis:
        n = len(kpis)
        card_w = min(200, (W - 60 - (n - 1) * 18) // n)
        for i, kpi in enumerate(kpis):
            c.draw_kpi_card(30 + i * (card_w + 18), y + 5, card_w, 110,
                            kpi.get("value", "0"), kpi.get("label", ""),
                            kpi.get("accent_color", "primary"))
        y += 130

    # Recent table
    if table.get("headers"):
        y = c.draw_section_title(30, y, "Operaciones Recientes")
        th = c.draw_table(30, y, table["headers"], rows,
                          table.get("column_widths", [100] * len(table["headers"])))
        y += th + 20

    # Alerts
    if alerts:
        y = c.draw_section_title(30, y, "Alertas")
        for alert in alerts:
            c.draw_alert(30, y, alert.get("text", ""), alert.get("severity", "warning"))
            y += 30

    c.save(path)


def _render_list(screen: dict, path: str, primary: str, secondary: str):
    table = screen.get("table", {})
    rows = table.get("rows", [])
    h = 260 + len(rows) * 32 + 60
    c = MockupCanvas(W, max(h, 600), primary, secondary)
    nav = screen.get("nav_user", {})
    c.draw_header("Portal", nav.get("name", ""), nav.get("role", ""))

    y = c.draw_section_title(30, 75, screen.get("title", "Lista"))

    placeholder = screen.get("search_placeholder", "Buscar...")
    c.draw_search_bar(30, y, placeholder)
    y += 48

    filters = screen.get("filters", [])
    if filters:
        c.draw_filters(30, y, filters)
        y += 40

    if table.get("headers"):
        c.draw_table(30, y, table["headers"], rows,
                     table.get("column_widths", [100] * len(table["headers"])))
        y += 32 + len(rows) * 32 + 15

    # Buttons
    for btn in screen.get("buttons", []):
        c.draw_button(W - 220, y, btn.get("text", ""), btn.get("style", "primary"))

    c.save(path)


def _render_detail(screen: dict, path: str, primary: str, secondary: str):
    # Estimate height
    sections = screen.get("detail_sections", [])
    est_h = 120
    for sec in sections:
        est_h += 60  # title
        if sec.get("fields"):
            est_h += max(len(sec["fields"]) // 2 + 1, len(sec["fields"])) * 28 + 30
        if sec.get("table"):
            est_h += 32 + len(sec["table"].get("rows", [])) * 32 + 20
        if sec.get("timeline_events"):
            est_h += len(sec["timeline_events"]) * 28 + 20
        if sec.get("buttons"):
            est_h += 50
    est_h += 60  # padding

    c = MockupCanvas(W, max(est_h, 800), primary, secondary)
    nav = screen.get("nav_user", {})
    c.draw_header("Portal", nav.get("name", ""), nav.get("role", ""))

    y = 70
    c.d.text((30, y), "< Volver a lista", fill=primary, font=c.font_body)
    c.d.text((220, y - 2), screen.get("title", "Detalle"), fill=secondary, font=c.font_subtitle)
    y += 40

    for sec in sections:
        y = c.draw_section_title(30, y, sec.get("title", ""))

        # Fields card
        fields = sec.get("fields", [])
        if fields:
            field_h = max(len(fields) // 2 + 1, 3) * 28 + 20
            c.draw_field_card(30, y, W - 60, field_h, fields)
            y += field_h + 15

        # Table
        tbl = sec.get("table")
        if tbl and tbl.get("headers"):
            # Buttons row before table
            for btn in sec.get("buttons", []):
                c.draw_button(W - 200, y - 35, btn.get("text", ""), btn.get("style", "primary"))
            th = c.draw_table(30, y, tbl["headers"], tbl.get("rows", []),
                              tbl.get("column_widths", [100] * len(tbl["headers"])))
            y += th + 15

        # Totals bar (if table had numeric data — detect by section title keywords)
        # Timeline
        events = sec.get("timeline_events", [])
        if events:
            c.draw_timeline(50, y, events)
            y += len(events) * 28 + 15

    c.save(path)


def _render_form(screen: dict, path: str, primary: str, secondary: str):
    fields = screen.get("form_fields", [])
    h = 200 + len(fields) * 45 + 200
    c = MockupCanvas(W, max(h, 600), primary, secondary)
    nav = screen.get("nav_user", {})
    c.draw_header("Portal", nav.get("name", ""), nav.get("role", ""))

    y = c.draw_section_title(30, 75, screen.get("title", "Formulario"))

    for field in fields:
        label = field.get("label", "")
        value = field.get("value", "")
        c.d.text((50, y), label, fill="#666666", font=c.font_small_bold)
        c.d.rounded_rectangle([50, y + 18, W // 2, y + 42], radius=4, outline="#E0E0E0", fill="#FFFFFF")
        c.d.text((58, y + 22), value, fill=secondary, font=c.font_small)
        y += 50

    y += 20
    for btn in screen.get("buttons", []):
        bw = c.draw_button(30, y, btn.get("text", ""), btn.get("style", "primary"))
        # Put buttons side by side... simplified: just stack them
        y += 45

    c.save(path)


def _render_validation(screen: dict, path: str, primary: str, secondary: str):
    table = screen.get("table", {})
    rows = table.get("rows", [])
    dialog = screen.get("confirmation_dialog", {})
    h = 300 + len(rows) * 32 + (250 if dialog else 0) + 200
    c = MockupCanvas(W, max(h, 700), primary, secondary)
    nav = screen.get("nav_user", {})
    c.draw_header("Portal", nav.get("name", ""), nav.get("role", ""))

    y = c.draw_section_title(30, 75, screen.get("title", "Validacion"))

    if screen.get("description"):
        c.d.text((30, y), screen["description"][:100], fill="#666666", font=c.font_body)
        y += 30

    if table.get("headers"):
        th = c.draw_table(30, y, table["headers"], rows,
                          table.get("column_widths", [100] * len(table["headers"])))
        y += th + 30

    # Confirmation dialog
    if dialog:
        dlg_y = y
        dlg_w = W - 400
        c.d.rounded_rectangle([200, dlg_y, 200 + dlg_w, dlg_y + 200], radius=12,
                              fill="#FFFFFF", outline=primary, width=3)
        c.d.rounded_rectangle([200, dlg_y, 200 + dlg_w, dlg_y + 42], radius=12, fill=primary)
        c.d.rectangle([200, dlg_y + 20, 200 + dlg_w, dlg_y + 42], fill=primary)
        c.d.text((220, dlg_y + 10), dialog.get("title", "Confirmar")[:50], fill="#FFFFFF", font=c.font_body_bold)

        dy = dlg_y + 55
        for item in dialog.get("items", [])[:5]:
            c.d.text((240, dy), f"*  {item[:70]}", fill=secondary, font=c.font_small)
            dy += 22

        dy += 15
        c.draw_button(220, dy, "Cancelar", "muted")
        c.draw_button(380, dy, dialog.get("confirm_text", "Confirmar"), "primary")

    c.save(path)


# Dispatch table
SCREEN_RENDERERS = {
    "dashboard": _render_dashboard,
    "list": _render_list,
    "detail": _render_detail,
    "form": _render_form,
    "validation": _render_validation,
}
