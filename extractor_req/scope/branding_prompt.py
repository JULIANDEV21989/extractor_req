"""Prompt interactivo para seleccion de colores corporativos.

Muestra los colores detectados por Claude y permite al usuario:
1. Aceptarlos
2. Elegir de paletas alternativas sugeridas
3. Introducir colores manualmente
"""

from __future__ import annotations

import re

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


def _color_block(hex_color: str) -> str:
    """Return a Rich-styled color swatch."""
    return f"[on {hex_color}]      [/on {hex_color}]"


def _is_valid_hex(color: str) -> bool:
    """Check if string is a valid hex color."""
    return bool(re.match(r"^#[0-9A-Fa-f]{6}$", color))


def prompt_branding_selection(
    branding_info: dict,
    console: Console,
) -> tuple[str, str, str]:
    """Interactive branding color selection in the terminal.

    Args:
        branding_info: Dict from branding_detector.detect_branding()
        console: Rich Console instance

    Returns:
        Tuple of (primary_color, secondary_color, company_name)
    """
    company = branding_info.get("company_name", "Empresa")
    primary = branding_info.get("primary_color", "#1565C0")
    primary_name = branding_info.get("primary_color_name", "Primario")
    secondary = branding_info.get("secondary_color", "#1A1A1A")
    secondary_name = branding_info.get("secondary_color_name", "Secundario")
    confidence = branding_info.get("confidence", "baja")
    reasoning = branding_info.get("reasoning", "")
    alternatives = branding_info.get("alternative_palettes", [])

    # Confidence indicator
    conf_style = {"alta": "[bold green]ALTA[/]", "media": "[bold yellow]MEDIA[/]", "baja": "[bold red]BAJA[/]"}
    conf_display = conf_style.get(confidence, f"[dim]{confidence}[/]")

    # Build the panel
    console.print()
    console.print(Panel.fit(
        "[bold]COLORES CORPORATIVOS DETECTADOS[/]\n"
        f"[dim]{reasoning}[/]",
        border_style="cyan",
        title="Branding",
    ))

    # Show detected colors
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("", width=8)
    table.add_column("", width=50)

    table.add_row("Empresa:", f"[bold]{company}[/]")
    table.add_row("Confianza:", conf_display)
    table.add_row("", "")
    table.add_row(
        "Primario:",
        f"{_color_block(primary)}  {primary_name} ({primary})"
    )
    table.add_row(
        "Secundario:",
        f"{_color_block(secondary)}  {secondary_name} ({secondary})"
    )
    console.print(table)
    console.print()

    # Options
    console.print("  [bold cyan][1][/]  Aceptar estos colores")

    # Alternative palettes
    for i, alt in enumerate(alternatives[:4], 2):
        alt_name = alt.get("name", f"Alternativa {i-1}")
        alt_primary = alt.get("primary_color", "#333333")
        alt_secondary = alt.get("secondary_color", "#1A1A1A")
        alt_desc = alt.get("description", "")
        console.print(
            f"  [bold cyan][{i}][/]  {alt_name}: "
            f"{_color_block(alt_primary)} {alt_primary}  "
            f"{_color_block(alt_secondary)} {alt_secondary}"
            f"  [dim]— {alt_desc}[/]"
        )

    manual_option = len(alternatives[:4]) + 2
    console.print(f"  [bold cyan][{manual_option}][/]  Introducir colores manualmente")
    console.print()

    # Get selection
    max_option = manual_option
    while True:
        try:
            choice_str = console.input("[bold]  Selecciona ([cyan]1[/cyan]-[cyan]{}[/cyan]): [/]".format(max_option))
            choice = int(choice_str.strip())
            if 1 <= choice <= max_option:
                break
            console.print(f"  [red]Opcion invalida. Elige entre 1 y {max_option}.[/]")
        except (ValueError, EOFError):
            console.print(f"  [red]Introduce un numero entre 1 y {max_option}.[/]")

    # Process selection
    if choice == 1:
        # Accept detected colors
        console.print(f"\n  [green]Colores aceptados:[/] {primary} + {secondary}\n")
        return primary, secondary, company

    elif choice == manual_option:
        # Manual entry
        console.print("\n  [bold]Introduce los colores en formato hex (#RRGGBB):[/]")

        while True:
            p = console.input("  Color primario (ej: #C41E2A): ").strip()
            if _is_valid_hex(p):
                break
            console.print("  [red]Formato invalido. Usa #RRGGBB (ej: #C41E2A)[/]")

        while True:
            s = console.input("  Color secundario (ej: #1A1A1A): ").strip()
            if _is_valid_hex(s):
                break
            console.print("  [red]Formato invalido. Usa #RRGGBB (ej: #1A1A1A)[/]")

        name = console.input(f"  Nombre de la empresa [{company}]: ").strip() or company

        console.print(
            f"\n  [green]Colores configurados:[/] "
            f"{_color_block(p)} {p}  "
            f"{_color_block(s)} {s}\n"
        )
        return p, s, name

    else:
        # Alternative palette
        alt_idx = choice - 2
        if alt_idx < len(alternatives):
            alt = alternatives[alt_idx]
            p = alt.get("primary_color", primary)
            s = alt.get("secondary_color", secondary)
            alt_name = alt.get("name", "Alternativa")
            console.print(
                f"\n  [green]Paleta seleccionada:[/] {alt_name} — "
                f"{_color_block(p)} {p}  "
                f"{_color_block(s)} {s}\n"
            )
            return p, s, company

    # Fallback
    return primary, secondary, company
