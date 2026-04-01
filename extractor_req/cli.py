"""CLI principal del extractor de requerimientos."""

import argparse
import os
import sys
import time

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table

from .config import load_config
from .scanner import scan_directory
from .consolidator import consolidate
from .analysis.analyzer import analyze_requirements
from .output.writer import save_markdown, save_docx

console = Console()


def main():
    parser = argparse.ArgumentParser(
        description="Extractor de Requerimientos Técnicos - Analiza documentos y genera especificaciones",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  extractor-req                          # Usa config.yaml, analiza input/ y genera output/
  extractor-req -i docs/ -o resultado/   # Carpetas personalizadas
  extractor-req --skip-video             # Omite transcripción de video
  extractor-req --skip-analysis          # Solo consolida, sin análisis LLM
  extractor-req --api-key sk-ant-xxx     # API key inline
        """,
    )
    parser.add_argument("-i", "--input", help="Carpeta con documentos fuente")
    parser.add_argument("-o", "--output", help="Carpeta de salida")
    parser.add_argument("-c", "--config", default="config.yaml", help="Archivo de configuración (default: config.yaml)")
    parser.add_argument("--api-key", help="API key de Anthropic")
    parser.add_argument("--model", help="Modelo de Claude (default: claude-sonnet-4-20250514)")
    parser.add_argument("--skip-video", action="store_true", help="Omitir extracción de video")
    parser.add_argument("--skip-analysis", action="store_true", help="Solo consolidar, sin análisis LLM")
    parser.add_argument("--whisper-model", choices=["tiny", "base", "small", "medium", "large-v3"])
    parser.add_argument("--no-transcribe", action="store_true", help="Solo extraer frames, sin transcribir audio")

    args = parser.parse_args()

    # Cargar config
    config = load_config(args.config)
    input_dir = args.input or config.input_dir
    output_dir = args.output or config.output_dir
    api_key = args.api_key or config.effective_api_key

    if args.model:
        config.analysis.model = args.model
    if args.whisper_model:
        config.video.whisper_model = args.whisper_model
    if args.no_transcribe:
        config.video.transcribe_audio = False

    # Resolver rutas absolutas
    base = os.getcwd()
    input_path = os.path.join(base, input_dir) if not os.path.isabs(input_dir) else input_dir
    output_path = os.path.join(base, output_dir) if not os.path.isabs(output_dir) else output_dir

    # Banner
    console.print(Panel.fit(
        "[bold cyan]EXTRACTOR DE REQUERIMIENTOS TECNICOS[/]\n"
        "[dim]Analiza documentos, videos y correos para generar especificaciones de desarrollo[/]",
        border_style="cyan",
    ))

    # ==================== FASE 1: ESCANEO ====================
    console.print("\n[bold yellow]FASE 1:[/] Escaneando archivos...\n")

    try:
        scan = scan_directory(input_path)
    except FileNotFoundError:
        console.print(f"[red]Error:[/] Directorio no encontrado: {input_path}")
        console.print(f"[dim]Crea la carpeta y coloca tus documentos ahí.[/]")
        sys.exit(1)

    if not scan.files:
        console.print(f"[red]No se encontraron archivos soportados en:[/] {input_path}")
        sys.exit(1)

    # Tabla resumen
    table = Table(title="Archivos Detectados", show_header=True)
    table.add_column("Tipo", style="cyan")
    table.add_column("Cantidad", justify="right")
    table.add_column("Tamaño", justify="right")
    for ftype, files in sorted(scan.by_type.items()):
        total_mb = sum(f.size_bytes for f in files) / 1024 / 1024
        table.add_row(ftype, str(len(files)), f"{total_mb:.1f} MB")
    table.add_row("[bold]TOTAL[/]", f"[bold]{len(scan.files)}[/]", f"[bold]{scan.total_size_bytes / 1024 / 1024:.1f} MB[/]")
    console.print(table)

    # ==================== FASE 2: EXTRACCION ====================
    console.print("\n[bold yellow]FASE 2:[/] Extrayendo contenido...\n")

    start = time.time()
    video_cfg = {
        "frame_interval": config.video.frame_interval,
        "whisper_model": config.video.whisper_model,
        "language": config.video.language,
        "transcribe_audio": config.video.transcribe_audio,
    }

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Procesando...", total=len(scan.files))

        def on_progress(name, ftype, idx, total):
            progress.update(task, completed=idx, description=f"[cyan]{name}[/] ({ftype})")

        consolidated = consolidate(
            scan,
            output_dir=output_path,
            api_key=api_key,
            video_config=video_cfg,
            skip_video=args.skip_video,
            progress_callback=on_progress,
        )

    elapsed = time.time() - start
    console.print(f"\n[green]Extracción completada[/] en {elapsed:.1f}s — {len(consolidated):,} caracteres")

    # Guardar consolidado
    os.makedirs(output_path, exist_ok=True)
    md_path = save_markdown(consolidated, os.path.join(output_path, "consolidado.md"))
    console.print(f"  Consolidado: [link file://{md_path}]{md_path}[/]")

    # ==================== FASE 3: ANALISIS LLM ====================
    if not args.skip_analysis:
        console.print("\n[bold yellow]FASE 3:[/] Analizando con Claude...\n")

        if not api_key:
            console.print(
                "[yellow]Sin API key configurada.[/] El consolidado se generó correctamente.\n"
                "Para el análisis LLM tienes 2 opciones:\n"
                "  1. Configura ANTHROPIC_API_KEY y re-ejecuta\n"
                "  2. Copia el contenido de consolidado.md a [bold]claude.ai[/] o [bold]Claude Code[/]\n"
            )
        else:
            with console.status("[bold cyan]Generando requerimientos con Claude...[/]", spinner="dots"):
                try:
                    requirements = analyze_requirements(
                        consolidated,
                        api_key=api_key,
                        model=config.analysis.model,
                        max_tokens=config.analysis.max_tokens,
                    )
                    # Guardar requerimientos
                    req_md = save_markdown(requirements, os.path.join(output_path, "requerimiento_tecnico.md"))
                    console.print(f"  [green]Requerimiento:[/] [link file://{req_md}]{req_md}[/]")

                    if "docx" in config.output.formats:
                        req_docx = save_docx(
                            requirements,
                            os.path.join(output_path, "requerimiento_tecnico.docx"),
                            "Documento de Requerimientos Técnicos",
                        )
                        console.print(f"  [green]DOCX:[/] [link file://{req_docx}]{req_docx}[/]")
                except Exception as e:
                    console.print(f"[red]Error en análisis LLM:[/] {e}")
                    console.print("[dim]El consolidado se generó correctamente. Puedes analizarlo manualmente.[/]")
    else:
        console.print("\n[dim]Análisis LLM omitido (--skip-analysis)[/]")

    # ==================== FASE 4: SALIDA ====================
    if "docx" in config.output.formats:
        docx_path = save_docx(consolidated, os.path.join(output_path, "consolidado.docx"), "Consolidado de Levantamiento")
        console.print(f"  Consolidado DOCX: [link file://{docx_path}]{docx_path}[/]")

    # Resumen final
    console.print(Panel.fit(
        f"[bold green]COMPLETADO[/]\n\n"
        f"Archivos procesados: {len(scan.files)}\n"
        f"Contenido extraído: {len(consolidated):,} caracteres\n"
        f"Salida en: [bold]{output_path}[/]",
        border_style="green",
    ))


if __name__ == "__main__":
    main()
