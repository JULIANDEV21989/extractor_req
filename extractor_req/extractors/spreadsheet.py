"""Extrae contenido de hojas de cálculo Excel (.xlsx, .xls) y CSV."""

from __future__ import annotations

import os


def extract_spreadsheet(file_path: str) -> str:
    """Extrae contenido de un archivo Excel o CSV como tablas Markdown.

    Args:
        file_path: Ruta al archivo .xlsx, .xls o .csv

    Returns:
        Markdown con cada hoja como tabla
    """
    ext = os.path.splitext(file_path)[1].lower()
    name = os.path.basename(file_path)

    if ext == ".csv":
        return _extract_csv(file_path, name)
    elif ext in (".xlsx", ".xls"):
        return _extract_excel(file_path, name, ext)
    else:
        return f"[Formato de hoja de cálculo no soportado: {ext}]"


def _extract_csv(file_path: str, name: str) -> str:
    """Extrae CSV usando pandas."""
    import pandas as pd

    try:
        # Try common encodings
        for encoding in ["utf-8", "latin-1", "cp1252"]:
            try:
                df = pd.read_csv(file_path, encoding=encoding, nrows=500)
                break
            except UnicodeDecodeError:
                continue
        else:
            return f"[Error de codificación leyendo {name}]"

        rows, cols = df.shape
        parts = [
            f"**Archivo CSV:** {name}",
            f"**Dimensiones:** {rows} filas x {cols} columnas\n",
        ]

        # Limit to first 100 rows for readability
        display_df = df.head(100)
        md_table = display_df.to_markdown(index=False)
        if md_table:
            parts.append(md_table)

        if rows > 100:
            parts.append(f"\n*[Mostrando primeras 100 de {rows} filas]*")

        return "\n".join(parts)

    except Exception as e:
        return f"[Error extrayendo CSV {name}: {e}]"


def _extract_excel(file_path: str, name: str, ext: str) -> str:
    """Extrae Excel usando openpyxl + pandas."""
    import pandas as pd

    try:
        engine = "openpyxl" if ext == ".xlsx" else "xlrd"
        # Read all sheet names first
        xls = pd.ExcelFile(file_path, engine=engine)
        sheet_names = xls.sheet_names

        parts = [
            f"**Archivo Excel:** {name}",
            f"**Hojas:** {len(sheet_names)} ({', '.join(sheet_names)})\n",
        ]

        for sheet_name in sheet_names:
            try:
                df = pd.read_excel(xls, sheet_name=sheet_name, nrows=200)
                rows, cols = df.shape

                parts.append(f"#### Hoja: {sheet_name}")
                parts.append(f"*{rows} filas x {cols} columnas*\n")

                if df.empty:
                    parts.append("*[Hoja vacía]*\n")
                    continue

                # Drop completely empty columns
                df = df.dropna(axis=1, how="all")

                # Limit display
                display_df = df.head(50)
                md_table = display_df.to_markdown(index=False)
                if md_table:
                    parts.append(md_table)

                if rows > 50:
                    parts.append(f"\n*[Mostrando primeras 50 de {rows} filas]*")

                parts.append("")

            except Exception as e:
                parts.append(f"#### Hoja: {sheet_name}\n*[Error: {e}]*\n")

        return "\n".join(parts)

    except Exception as e:
        return f"[Error extrayendo Excel {name}: {e}]"
