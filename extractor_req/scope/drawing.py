"""Primitivas de dibujo Pillow para mockups profesionales.

Generalizado del prototipo generar_mockups.py de TFM Maritimo.
Todas las primitivas reciben datos como parametros — sin logica de dominio.
"""

from __future__ import annotations

import os
import platform

from PIL import Image, ImageDraw, ImageFont

# Semantic color palette — resolved against branding at runtime
SEMANTIC_PALETTE = {
    "success": "#4CAF50",
    "warning": "#FF9800",
    "danger": "#FF5722",
    "info": "#2196F3",
    "muted": "#9E9E9E",
    "dark": "#616161",
}

DPI = 144


def _find_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Cross-platform font resolver."""
    system = platform.system()
    candidates = []
    if system == "Windows":
        candidates = [
            "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        ]
    elif system == "Darwin":
        candidates = [
            "/System/Library/Fonts/Helvetica.ttc",
            "/Library/Fonts/Arial.ttf",
        ]
    else:  # Linux
        candidates = [
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold
            else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
            else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


class MockupCanvas:
    """Wraps a PIL Image/Draw with branded colors, fonts, and reusable drawing primitives."""

    def __init__(self, width: int, height: int, primary_color: str, secondary_color: str):
        self.width = width
        self.height = height
        self.primary = primary_color
        self.secondary = secondary_color
        self.img = Image.new("RGB", (width, height), "#FFFFFF")
        self.d = ImageDraw.Draw(self.img)

        # Pre-load fonts
        self.font_title = _find_font(28, bold=True)
        self.font_subtitle = _find_font(20, bold=True)
        self.font_body = _find_font(16)
        self.font_body_bold = _find_font(16, bold=True)
        self.font_small = _find_font(13)
        self.font_small_bold = _find_font(13, bold=True)
        self.font_tiny = _find_font(11)
        self.font_kpi = _find_font(42, bold=True)
        self.font_kpi_label = _find_font(14, bold=True)
        self.font_header_bar = _find_font(18, bold=True)
        self.font_header_user = _find_font(14)

    def resolve_color(self, semantic: str) -> str:
        """Resolve semantic color name to hex."""
        if semantic == "primary":
            return self.primary
        if semantic == "secondary":
            return self.secondary
        return SEMANTIC_PALETTE.get(semantic, semantic)  # fallback: treat as hex

    def draw_header(self, app_title: str = "", user: str = "", role: str = ""):
        """Draw the top navigation bar."""
        self.d.rectangle([0, 0, self.width, 56], fill=self.secondary)
        self.d.rectangle([0, 56, self.width, 60], fill=self.primary)
        if app_title:
            self.d.text((20, 14), app_title, fill="#FFFFFF", font=self.font_header_bar)
        if user:
            txt = f"{user}  |  {role}  |  Salir"
            bbox = self.d.textbbox((0, 0), txt, font=self.font_header_user)
            tw = bbox[2] - bbox[0]
            self.d.text((self.width - tw - 20, 18), txt, fill="#CCCCCC", font=self.font_header_user)

    def draw_section_title(self, x: int, y: int, text: str) -> int:
        """Draw a section title with red underline accent. Returns new y position."""
        self.d.text((x, y), text, fill=self.secondary, font=self.font_subtitle)
        self.d.rectangle([x, y + 28, x + 60, y + 31], fill=self.primary)
        return y + 40

    def draw_kpi_card(self, x: int, y: int, w: int, h: int, value: str, label: str, accent: str):
        """Draw a KPI card with shadow, accent top bar, centered value and label."""
        color = self.resolve_color(accent)
        self.d.rectangle([x + 3, y + 3, x + w + 3, y + h + 3], fill="#E8E8E8")
        self.d.rectangle([x, y, x + w, y + h], fill="#FFFFFF", outline="#E0E0E0", width=1)
        self.d.rectangle([x, y, x + w, y + 4], fill=color)
        # Value centered
        vbbox = self.d.textbbox((0, 0), str(value), font=self.font_kpi)
        vw = vbbox[2] - vbbox[0]
        self.d.text((x + (w - vw) // 2, y + 20), str(value), fill=self.secondary, font=self.font_kpi)
        # Label centered
        lbbox = self.d.textbbox((0, 0), label, font=self.font_kpi_label)
        lw = lbbox[2] - lbbox[0]
        self.d.text((x + (w - lw) // 2, y + h - 35), label, fill="#666666", font=self.font_kpi_label)

    def draw_table(self, x: int, y: int, headers: list[str], rows: list[list],
                   col_widths: list[int], row_height: int = 32) -> int:
        """Draw a styled table. Returns total height drawn.

        Cell values can be str or dict {"text": str, "color": str} for badges.
        """
        # Normalize col_widths to pixels (proportional)
        total_prop = sum(col_widths)
        available_w = self.width - x - 30
        pixel_widths = [int(cw / total_prop * available_w) for cw in col_widths]

        # Header
        cx = x
        for hdr, pw in zip(headers, pixel_widths):
            self.d.rectangle([cx, y, cx + pw, y + row_height], fill=self.secondary)
            self.d.text((cx + 8, y + 7), str(hdr), fill="#FFFFFF", font=self.font_small_bold)
            cx += pw

        # Rows
        for ri, row in enumerate(rows):
            ry = y + row_height + ri * row_height
            bg = "#F5F5F5" if ri % 2 == 0 else "#FFFFFF"
            cx = x
            for ci, (cell, pw) in enumerate(zip(row, pixel_widths)):
                self.d.rectangle([cx, ry, cx + pw, ry + row_height], fill=bg, outline="#E0E0E0", width=1)
                if isinstance(cell, dict) and "text" in cell:
                    # Badge
                    badge_color = self.resolve_color(cell.get("color", "muted"))
                    tbbox = self.d.textbbox((0, 0), cell["text"], font=self.font_tiny)
                    tw = tbbox[2] - tbbox[0]
                    bx, by = cx + 8, ry + 7
                    self.d.rounded_rectangle([bx, by, bx + tw + 12, by + 18], radius=4, fill=badge_color)
                    self.d.text((bx + 6, by + 1), cell["text"], fill="#FFFFFF", font=self.font_tiny)
                else:
                    self.d.text((cx + 8, ry + 7), str(cell)[:40], fill=self.secondary, font=self.font_small)
                cx += pw

        total_h = row_height + len(rows) * row_height
        total_w = sum(pixel_widths)
        self.d.rectangle([x, y, x + total_w, y + total_h], outline="#E0E0E0", width=2)
        return total_h

    def draw_badge(self, x: int, y: int, text: str, color: str) -> int:
        """Draw a colored badge. Returns badge width."""
        c = self.resolve_color(color)
        tbbox = self.d.textbbox((0, 0), text, font=self.font_tiny)
        tw = tbbox[2] - tbbox[0]
        self.d.rounded_rectangle([x, y, x + tw + 14, y + 20], radius=5, fill=c)
        self.d.text((x + 7, y + 3), text, fill="#FFFFFF", font=self.font_tiny)
        return tw + 14

    def draw_button(self, x: int, y: int, text: str, style: str = "primary") -> int:
        """Draw a styled button. Returns button width."""
        bg = self.resolve_color(style)
        tbbox = self.d.textbbox((0, 0), text, font=self.font_small_bold)
        tw = tbbox[2] - tbbox[0]
        pad_x, pad_y = 16, 8
        self.d.rounded_rectangle([x, y, x + tw + pad_x * 2, y + tbbox[3] - tbbox[1] + pad_y * 2],
                                 radius=6, fill=bg)
        self.d.text((x + pad_x, y + pad_y), text, fill="#FFFFFF", font=self.font_small_bold)
        return tw + pad_x * 2

    def draw_alert(self, x: int, y: int, text: str, severity: str = "warning") -> int:
        """Draw an alert bar. Returns height."""
        colors = {"warning": ("#FFF3E0", "#FF9800"), "danger": ("#FFEBEE", "#F44336"), "info": ("#E3F2FD", "#2196F3")}
        bg, fg = colors.get(severity, ("#FFF3E0", "#FF9800"))
        self.d.rounded_rectangle([x, y, self.width - 30, y + 26], radius=4, fill=bg)
        self.d.text((x + 10, y + 4), text, fill=fg, font=self.font_small_bold)
        return 30

    def draw_search_bar(self, x: int, y: int, placeholder: str, width: int = 470) -> int:
        """Draw a search bar with button. Returns height."""
        self.d.rounded_rectangle([x, y, x + width, y + 36], radius=6, outline="#E0E0E0", width=2, fill="#FFFFFF")
        self.d.text((x + 12, y + 8), placeholder, fill="#BBBBBB", font=self.font_small)
        self.d.rounded_rectangle([x + width, y, x + width + 60, y + 36], radius=6, fill=self.primary)
        self.d.text((x + width + 12, y + 8), "Buscar", fill="#FFFFFF", font=self.font_tiny)
        return 44

    def draw_filters(self, x: int, y: int, filters: list[str]) -> int:
        """Draw a row of filter dropdowns. Returns height."""
        fx = x
        for f in filters:
            tbbox = self.d.textbbox((0, 0), f, font=self.font_small)
            tw = tbbox[2] - tbbox[0]
            self.d.rounded_rectangle([fx, y, fx + tw + 20, y + 28], radius=4,
                                     outline="#E0E0E0", width=1, fill="#FFFFFF")
            self.d.text((fx + 10, y + 5), f, fill="#666666", font=self.font_small)
            fx += tw + 30
        return 36

    def draw_field_card(self, x: int, y: int, w: int, h: int, fields: list[list[str]]):
        """Draw a card with label-value field pairs."""
        self.d.rounded_rectangle([x, y, x + w, y + h], radius=8, fill="#F5F5F5", outline="#E0E0E0")
        mid = w // 2
        for i, pair in enumerate(fields):
            if i >= len(fields):
                break
            label = pair[0] if len(pair) > 0 else ""
            value = pair[1] if len(pair) > 1 else ""
            fy = y + 12 + i * 28
            if i < len(fields) // 2 + 1:
                self.d.text((x + 15, fy), label, fill="#666666", font=self.font_small_bold)
                self.d.text((x + 150, fy), value, fill=self.secondary, font=self.font_small)
            else:
                col2_i = i - (len(fields) // 2 + 1)
                if col2_i < 0:
                    continue
                fy2 = y + 12 + col2_i * 28
                self.d.text((x + mid + 15, fy2), label, fill="#666666", font=self.font_small_bold)
                self.d.text((x + mid + 150, fy2), value, fill=self.secondary, font=self.font_small)

    def draw_timeline(self, x: int, y: int, events: list[list[str]]) -> int:
        """Draw a vertical timeline with dots. Returns height."""
        for i, event in enumerate(events):
            ey = y + i * 28
            date = event[0] if len(event) > 0 else ""
            desc = event[1] if len(event) > 1 else ""
            who = event[2] if len(event) > 2 else ""
            self.d.ellipse([x, ey + 4, x + 12, ey + 16], fill=self.primary)
            if i < len(events) - 1:
                self.d.line([x + 6, ey + 16, x + 6, ey + 28], fill="#E0E0E0", width=2)
            self.d.text((x + 22, ey), date, fill="#666666", font=self.font_small_bold)
            self.d.text((x + 110, ey), desc[:60], fill=self.secondary, font=self.font_small)
            if who:
                self.d.text((self.width - 150, ey), who, fill="#666666", font=self.font_small)
        return len(events) * 28

    def draw_totals_bar(self, x: int, y: int, items: list[tuple[str, str]]) -> int:
        """Draw a dark totals bar with labeled values. Returns height."""
        self.d.rounded_rectangle([x, y, self.width - 30, y + 40], radius=6, fill=self.secondary)
        spacing = (self.width - x - 60) // max(len(items), 1)
        for i, (label, value) in enumerate(items):
            tx = x + 20 + i * spacing
            color = self.primary if i == len(items) - 1 else "#FFFFFF"
            self.d.text((tx, y + 10), f"{label}: {value}", fill=color, font=self.font_small_bold)
        return 45

    # === DIAGRAM PRIMITIVES ===

    def draw_flow_diagram(self, columns: list[dict], steps: list[dict], annotations: list[dict]):
        """Draw a multi-column process flow diagram."""
        self.d.rectangle([0, 0, self.width, 50], fill=self.secondary)
        self.d.rectangle([0, 50, self.width, 54], fill=self.primary)

        col_w = self.width // max(len(columns), 1)
        for i, col in enumerate(columns):
            color = self.resolve_color(col.get("color", "muted"))
            x = i * col_w
            self.d.rectangle([x, 65, x + col_w, 100], fill=color)
            name = col.get("name", "")
            lbbox = self.d.textbbox((0, 0), name, font=self.font_body_bold)
            lw = lbbox[2] - lbbox[0]
            self.d.text((x + (col_w - lw) // 2, 72), name, fill="#FFFFFF", font=self.font_body_bold)

        # Steps
        for step in steps:
            col_idx = step.get("column_index", 0)
            text = step.get("text", "")
            y_pos = step.get("y_position", 0)
            sy = 110 + y_pos * 6  # scale y_position to pixels
            x = col_idx * col_w + 20
            bw = col_w - 40
            lines = text.split("\n")
            bh = 8 + len(lines) * 16 + 8
            color = self.resolve_color(columns[col_idx].get("color", "muted")) if col_idx < len(columns) else "#666666"
            self.d.rounded_rectangle([x, sy, x + bw, sy + bh], radius=6, fill="#FFFFFF", outline=color, width=2)
            for li, line in enumerate(lines):
                self.d.text((x + 10, sy + 5 + li * 16), line[:50], fill=self.secondary, font=self.font_small)

        # Annotations (arrows)
        for ann in annotations:
            fc = ann.get("from_column", 0)
            tc = ann.get("to_column", 1)
            ay = 110 + ann.get("y_position", 0) * 6
            label = ann.get("label", "")
            fx = fc * col_w + col_w // 2
            tx = tc * col_w + col_w // 2
            self.d.line([fx, ay, tx, ay], fill=self.primary, width=2)
            if tx > fx:
                self.d.polygon([(tx - 8, ay - 5), (tx, ay), (tx - 8, ay + 5)], fill=self.primary)
            else:
                self.d.polygon([(tx + 8, ay - 5), (tx, ay), (tx + 8, ay + 5)], fill=self.primary)
            if label:
                mid_x = (fx + tx) // 2
                lbbox = self.d.textbbox((0, 0), label, font=self.font_tiny)
                lw = lbbox[2] - lbbox[0]
                self.d.rounded_rectangle([mid_x - lw // 2 - 6, ay - 18, mid_x + lw // 2 + 6, ay - 2],
                                         radius=4, fill="#FFF3E0")
                self.d.text((mid_x - lw // 2, ay - 16), label, fill="#FF9800", font=self.font_tiny)

    def draw_state_chain(self, title: str, states: list[dict]):
        """Draw a horizontal state lifecycle diagram."""
        self.d.rectangle([0, 0, self.width, 50], fill=self.secondary)
        self.d.rectangle([0, 50, self.width, 54], fill=self.primary)
        self.d.text((30, 12), title, fill="#FFFFFF", font=self.font_header_bar)

        y_center = 180
        state_w = 155
        state_h = 55
        gap = 40
        n = max(len(states), 1)
        total_w = n * state_w + (n - 1) * gap
        start_x = max((self.width - total_w) // 2, 20)

        for i, state in enumerate(states):
            x = start_x + i * (state_w + gap)
            color = self.resolve_color(state.get("color", "muted"))
            self.d.rounded_rectangle([x, y_center - state_h // 2, x + state_w, y_center + state_h // 2],
                                     radius=10, fill=color)
            name = state.get("name", "")
            nbbox = self.d.textbbox((0, 0), name, font=self.font_small_bold)
            nw = nbbox[2] - nbbox[0]
            self.d.text((x + (state_w - nw) // 2, y_center - 18), name, fill="#FFFFFF", font=self.font_small_bold)
            desc = state.get("description", "")
            dbbox = self.d.textbbox((0, 0), desc[:20], font=self.font_tiny)
            dw = dbbox[2] - dbbox[0]
            self.d.text((x + (state_w - dw) // 2, y_center + 5), desc[:20], fill="#FFFFFFCC", font=self.font_tiny)

            if i < len(states) - 1:
                ax = x + state_w + 5
                self.d.line([ax, y_center, ax + gap - 10, y_center], fill=self.primary, width=3)
                self.d.polygon([(ax + gap - 10, y_center - 6), (ax + gap - 2, y_center),
                                (ax + gap - 10, y_center + 6)], fill=self.primary)

        # Triggered by labels
        y_who = y_center + 50
        for i, state in enumerate(states):
            x = start_x + i * (state_w + gap)
            who = state.get("triggered_by", "")
            wbbox = self.d.textbbox((0, 0), who[:20], font=self.font_tiny)
            ww = wbbox[2] - wbbox[0]
            self.d.text((x + (state_w - ww) // 2, y_who), who[:20], fill="#666666", font=self.font_tiny)

    def draw_system_boxes(self, title: str, systems: list[dict], connections: list[dict],
                          footnotes: list[str] | None = None):
        """Draw an integration diagram with system boxes and connections."""
        self.d.rectangle([0, 0, self.width, 50], fill=self.secondary)
        self.d.rectangle([0, 50, self.width, 54], fill=self.primary)
        self.d.text((30, 12), title, fill="#FFFFFF", font=self.font_header_bar)

        y_center = 200
        n = max(len(systems), 1)
        box_w = min(280, (self.width - 80) // n - 40)
        total_w = n * box_w + (n - 1) * 80
        start_x = max((self.width - total_w) // 2, 40)
        box_h = 140

        box_positions = {}
        for i, sys in enumerate(systems):
            x = start_x + i * (box_w + 80)
            color = self.resolve_color(sys.get("color", "muted"))
            name = sys.get("name", "")
            box_positions[name] = (x, x + box_w)

            self.d.rounded_rectangle([x, y_center - box_h // 2, x + box_w, y_center + box_h // 2],
                                     radius=12, fill="#FFFFFF", outline=color, width=3)
            # Header inside box
            self.d.rounded_rectangle([x, y_center - box_h // 2, x + box_w, y_center - box_h // 2 + 38],
                                     radius=12, fill=color)
            self.d.rectangle([x, y_center - box_h // 2 + 20, x + box_w, y_center - box_h // 2 + 38], fill=color)
            nbbox = self.d.textbbox((0, 0), name, font=self.font_body_bold)
            nw = nbbox[2] - nbbox[0]
            self.d.text((x + (box_w - nw) // 2, y_center - box_h // 2 + 8), name,
                        fill="#FFFFFF", font=self.font_body_bold)

            desc = sys.get("description", "")
            for li, line in enumerate(desc.split("\n")[:2]):
                self.d.text((x + 20, y_center - 15 + li * 18), line[:30], fill=self.secondary, font=self.font_small)
            infra = sys.get("infrastructure", "")
            for li, line in enumerate(infra.split("\n")[:2]):
                self.d.text((x + 20, y_center + 25 + li * 14), line[:30], fill="#666666", font=self.font_tiny)

        # Connections
        for conn in connections:
            from_name = conn.get("from_system", "")
            to_name = conn.get("to_system", "")
            if from_name not in box_positions or to_name not in box_positions:
                continue
            fx_end = box_positions[from_name][1] + 10
            tx_start = box_positions[to_name][0] - 10
            color = self.resolve_color("info")
            self.d.line([fx_end, y_center - 10, tx_start, y_center - 10], fill=color, width=3)
            self.d.polygon([(tx_start - 8, y_center - 16), (tx_start, y_center - 10),
                            (tx_start - 8, y_center - 4)], fill=color)
            if conn.get("direction") == "bidirectional":
                self.d.line([tx_start, y_center + 10, fx_end, y_center + 10], fill=color, width=2)
                self.d.polygon([(fx_end + 8, y_center + 4), (fx_end, y_center + 10),
                                (fx_end + 8, y_center + 16)], fill=color)
            label = conn.get("label", "")
            if label:
                mid_x = (fx_end + tx_start) // 2
                lbbox = self.d.textbbox((0, 0), label[:30], font=self.font_tiny)
                lw = lbbox[2] - lbbox[0]
                self.d.rounded_rectangle([mid_x - lw // 2 - 6, y_center - 48, mid_x + lw // 2 + 6, y_center - 30],
                                         radius=4, fill="#E3F2FD")
                self.d.text((mid_x - lw // 2, y_center - 46), label[:30], fill="#1565C0", font=self.font_tiny)

        if footnotes:
            for i, note in enumerate(footnotes[:4]):
                self.d.text((30, y_center + box_h // 2 + 30 + i * 20), f"* {note}",
                            fill="#666666", font=self.font_small)

    def draw_comparison(self, before_title: str, before_steps: list[dict], before_time: str,
                        after_title: str, after_steps: list[dict], after_time: str,
                        improvement: str):
        """Draw a before/after comparison diagram."""
        self.d.rectangle([0, 0, self.width, 50], fill=self.secondary)
        self.d.rectangle([0, 50, self.width, 54], fill=self.primary)

        half = self.width // 2 - 15
        step_h = 42
        max_steps = max(len(before_steps), len(after_steps))
        panel_h = 115 + max_steps * step_h + 25

        # BEFORE panel
        self.d.rounded_rectangle([20, 70, half, 70 + panel_h], radius=12, fill="#FFEBEE", outline=self.primary, width=2)
        self.d.rounded_rectangle([20, 70, half, 108], radius=12, fill=self.primary)
        self.d.rectangle([20, 90, half, 108], fill=self.primary)
        self.d.text((40, 78), before_title[:40], fill="#FFFFFF", font=self.font_body_bold)

        for i, step in enumerate(before_steps):
            sy = 125 + i * step_h
            color = self.primary if step.get("status") == "manual" else self.secondary
            self.d.rounded_rectangle([40, sy, half - 20, sy + 34], radius=6, fill="#FFFFFF", outline=color, width=1)
            self.d.ellipse([48, sy + 7, 68, sy + 27], fill=color)
            self.d.text((53, sy + 9), step.get("number", ""), fill="#FFFFFF", font=self.font_small_bold)
            self.d.text((78, sy + 9), step.get("text", "")[:45], fill=self.secondary, font=self.font_small)

        self.d.text((40, 70 + panel_h - 25), f"Tiempo: {before_time}", fill=self.primary, font=self.font_small_bold)

        # AFTER panel
        dx = half + 10
        green = "#4CAF50"
        self.d.rounded_rectangle([dx, 70, self.width - 20, 70 + panel_h], radius=12, fill="#E8F5E9", outline=green, width=2)
        self.d.rounded_rectangle([dx, 70, self.width - 20, 108], radius=12, fill=green)
        self.d.rectangle([dx, 90, self.width - 20, 108], fill=green)
        self.d.text((dx + 20, 78), after_title[:40], fill="#FFFFFF", font=self.font_body_bold)

        for i, step in enumerate(after_steps):
            sy = 125 + i * step_h
            color = green if step.get("status") == "automated" else self.secondary
            self.d.rounded_rectangle([dx + 20, sy, self.width - 40, sy + 34], radius=6, fill="#FFFFFF", outline=color, width=1)
            self.d.ellipse([dx + 28, sy + 7, dx + 48, sy + 27], fill=color)
            self.d.text((dx + 33, sy + 9), step.get("number", ""), fill="#FFFFFF", font=self.font_small_bold)
            self.d.text((dx + 58, sy + 9), step.get("text", "")[:45], fill=self.secondary, font=self.font_small)

        self.d.text((dx + 20, 70 + panel_h - 25), f"Tiempo: {after_time}", fill=green, font=self.font_small_bold)

        # Improvement callout
        if improvement:
            cy = 70 + panel_h + 12
            self.d.rounded_rectangle([self.width // 2 - 90, cy, self.width // 2 + 90, cy + 38], radius=8, fill=self.primary)
            ibbox = self.d.textbbox((0, 0), improvement, font=self.font_body_bold)
            iw = ibbox[2] - ibbox[0]
            self.d.text((self.width // 2 - iw // 2, cy + 8), improvement, fill="#FFFFFF", font=self.font_body_bold)

    def draw_roles_table(self, title: str, role_columns: list[dict], permissions: list[dict]):
        """Draw a roles/permissions matrix with check circles."""
        self.d.rectangle([0, 0, self.width, 50], fill=self.secondary)
        self.d.rectangle([0, 50, self.width, 54], fill=self.primary)
        self.d.text((30, 12), title, fill="#FFFFFF", font=self.font_header_bar)

        y = 75
        action_w = 340
        role_w = (self.width - 60 - action_w) // max(len(role_columns), 1)

        # Header
        self.d.rectangle([30, y, 30 + action_w, y + 40], fill=self.secondary)
        self.d.text((38, y + 10), "Accion", fill="#FFFFFF", font=self.font_small_bold)
        for i, rc in enumerate(role_columns):
            cx = 30 + action_w + i * role_w
            self.d.rectangle([cx, y, cx + role_w, y + 40], fill=self.secondary)
            self.d.text((cx + 8, y + 4), rc.get("name", "")[:15], fill="#FFFFFF", font=self.font_small_bold)
            self.d.text((cx + 8, y + 20), rc.get("role_label", "")[:15], fill="#CCCCCC", font=self.font_tiny)

        # Rows
        for ri, perm in enumerate(permissions):
            ry = y + 40 + ri * 32
            bg = "#F5F5F5" if ri % 2 == 0 else "#FFFFFF"
            self.d.rectangle([30, ry, 30 + action_w, ry + 32], fill=bg, outline="#E0E0E0", width=1)
            self.d.text((38, ry + 7), perm.get("action", "")[:40], fill=self.secondary, font=self.font_small)
            for vi, val in enumerate(perm.get("values", [])):
                cx = 30 + action_w + vi * role_w
                self.d.rectangle([cx, ry, cx + role_w, ry + 32], fill=bg, outline="#E0E0E0", width=1)
                center_x = cx + role_w // 2
                center_y = ry + 16
                if val:
                    self.d.ellipse([center_x - 10, center_y - 10, center_x + 10, center_y + 10], fill="#4CAF50")
                    self.d.text((center_x - 5, center_y - 7), "Si", fill="#FFFFFF", font=self.font_tiny)
                else:
                    self.d.ellipse([center_x - 10, center_y - 10, center_x + 10, center_y + 10], fill="#EEEEEE")
                    self.d.text((center_x - 3, center_y - 6), "-", fill="#666666", font=self.font_tiny)

    def draw_gantt(self, title: str, phases: list[dict], dependency_note: str = ""):
        """Draw a Gantt-style phase timeline."""
        self.d.rectangle([0, 0, self.width, 50], fill=self.secondary)
        self.d.rectangle([0, 50, self.width, 54], fill=self.primary)
        self.d.text((30, 12), title, fill="#FFFFFF", font=self.font_header_bar)

        y = 68
        if dependency_note:
            self.d.rounded_rectangle([30, y, self.width - 30, y + 30], radius=6, fill="#FFF3E0")
            self.d.text((45, y + 6), dependency_note[:100], fill="#FF9800", font=self.font_small)
            y += 40

        # Calculate scale
        max_days = max((p.get("start_day", 0) + p.get("duration_days", 1) for p in phases), default=15)
        scale_x = 350
        scale_w = self.width - scale_x - 40
        day_w = scale_w / max(max_days, 1)

        # Day labels
        self.d.text((scale_x - 5, y), "Dias:", fill="#666666", font=self.font_small)
        for dd in range(max_days):
            dx = scale_x + dd * day_w
            self.d.text((dx + day_w // 2 - 3, y + 14), str(dd + 1), fill="#666666", font=self.font_tiny)
        y += 32

        bar_h = 50
        gap_y = 15
        for phase in phases:
            name = phase.get("name", "")
            duration = phase.get("duration", "")
            desc = phase.get("description", "")
            color = self.resolve_color(phase.get("color", "primary"))
            start_d = phase.get("start_day", 0)
            dur_d = phase.get("duration_days", 5)

            self.d.text((30, y + 8), name, fill=self.secondary, font=self.font_body_bold)
            self.d.text((30, y + 32), duration, fill="#666666", font=self.font_small)

            bx = scale_x + start_d * day_w
            bw = max(dur_d * day_w, 40)
            self.d.rounded_rectangle([bx, y, bx + bw, y + bar_h], radius=8, fill=color)
            max_chars = max(int(bw / 6), 10)
            self.d.text((bx + 10, y + 10), desc[:max_chars], fill="#FFFFFF", font=self.font_tiny)
            if len(desc) > max_chars:
                self.d.text((bx + 10, y + 26), desc[max_chars:max_chars * 2], fill="#FFFFFFCC", font=self.font_tiny)

            y += bar_h + gap_y

        # Total line
        total_days = max_days
        self.d.rectangle([30, y + 5, self.width - 30, y + 6], fill="#E0E0E0")
        total_text = f"TOTAL: {total_days} DIAS HABILES"
        self.d.text((30, y + 12), total_text, fill=self.primary, font=self.font_body_bold)

    def save(self, path: str):
        """Save the canvas as PNG."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.img.save(path, dpi=(DPI, DPI))
