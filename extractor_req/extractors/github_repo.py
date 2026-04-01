"""Extrae contenido relevante de repositorios GitHub.

Estrategia:
1. Clonar repo (shallow clone para velocidad)
2. Extraer README, estructura de archivos, archivos clave
3. Filtro inteligente: ignorar node_modules, .git, dist, build, venv, etc.
"""

from __future__ import annotations

import os
import shutil
import tempfile


# Directorios a ignorar siempre
IGNORE_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", "env",
    "dist", "build", ".next", ".nuxt", ".output", "coverage",
    ".idea", ".vscode", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    "vendor", "target", "bin", "obj", ".gradle",
}

# Extensiones de archivos relevantes para extracción
RELEVANT_EXTENSIONS = {
    ".md", ".txt", ".rst",  # Documentación
    ".py", ".js", ".ts", ".jsx", ".tsx",  # Código principal
    ".java", ".go", ".rs", ".rb", ".php", ".cs",
    ".json", ".yaml", ".yml", ".toml",  # Configuración
    ".sql", ".graphql",  # Schemas
    ".env.example", ".env.template",  # Env templates (no secrets)
    ".sh", ".bash",  # Scripts
    ".html", ".css", ".scss",  # Frontend
    ".dockerfile", ".dockerignore",  # Docker
}

# Archivos prioritarios (siempre incluir si existen)
PRIORITY_FILES = {
    "README.md", "readme.md", "README.rst", "README.txt",
    "CLAUDE.md", "CONTRIBUTING.md", "CHANGELOG.md",
    "package.json", "pyproject.toml", "setup.py", "setup.cfg",
    "Cargo.toml", "go.mod", "pom.xml", "build.gradle",
    "docker-compose.yml", "docker-compose.yaml", "Dockerfile",
    ".env.example", "Makefile", "justfile",
}

MAX_FILE_SIZE = 100_000  # 100KB máx por archivo
MAX_FILES = 50  # Máximo de archivos a extraer
MAX_TOTAL_CHARS = 500_000  # 500K chars total


def extract_github_repo(repo_url: str, branch: str = "main") -> str:
    """Extrae contenido relevante de un repositorio GitHub.

    Args:
        repo_url: URL del repo (https://github.com/user/repo o user/repo)
        branch: Branch a clonar (default: main)

    Returns:
        Markdown con estructura y contenido del repo
    """
    try:
        import git
    except ImportError:
        return (
            f"[gitpython no instalado. Instala con: pip install gitpython]\n"
            f"Repo: {repo_url}"
        )

    # Normalizar URL
    if not repo_url.startswith("http"):
        repo_url = f"https://github.com/{repo_url}"
    repo_url = repo_url.rstrip("/")
    if repo_url.endswith(".git"):
        repo_url = repo_url[:-4]

    repo_name = repo_url.split("/")[-1]
    parts: list[str] = [f"## Repositorio: {repo_name}\n**URL:** {repo_url}\n"]

    # Clonar en directorio temporal
    tmp_dir = tempfile.mkdtemp(prefix="extractor_repo_")
    try:
        try:
            repo = git.Repo.clone_from(
                repo_url + ".git", tmp_dir,
                depth=1, branch=branch, single_branch=True,
            )
        except git.GitCommandError:
            # Intentar sin branch específico
            try:
                repo = git.Repo.clone_from(repo_url + ".git", tmp_dir, depth=1)
            except Exception as e:
                return f"[Error clonando {repo_url}: {e}]"

        # Estructura de archivos
        tree = _build_file_tree(tmp_dir)
        parts.append("### Estructura del Proyecto\n```\n" + tree + "\n```\n")

        # Extraer archivos relevantes
        files_content = _extract_relevant_files(tmp_dir, repo_name)
        parts.append(files_content)

    finally:
        # Limpiar directorio temporal
        try:
            shutil.rmtree(tmp_dir, ignore_errors=True)
        except Exception:
            pass

    return "\n".join(parts)


def extract_repos_from_list(urls: list[str]) -> str:
    """Extrae contenido de múltiples repos."""
    if not urls:
        return "[No se proporcionaron URLs de repositorios]"

    parts = [f"**Repositorios procesados:** {len(urls)}\n"]
    for url in urls:
        url = url.strip()
        if not url or url.startswith("#"):
            continue
        parts.append(extract_github_repo(url))
        parts.append("\n---\n")

    return "\n".join(parts)


def _build_file_tree(root: str, prefix: str = "", max_depth: int = 4, depth: int = 0) -> str:
    """Construye un árbol de archivos estilo tree."""
    if depth >= max_depth:
        return prefix + "...\n"

    entries = sorted(os.listdir(root))
    entries = [e for e in entries if e not in IGNORE_DIRS and not e.startswith(".")]

    lines = []
    dirs = [e for e in entries if os.path.isdir(os.path.join(root, e))]
    files = [e for e in entries if os.path.isfile(os.path.join(root, e))]

    for f in files[:20]:
        lines.append(f"{prefix}{f}")
    if len(files) > 20:
        lines.append(f"{prefix}... ({len(files) - 20} más)")

    for d in dirs[:15]:
        lines.append(f"{prefix}{d}/")
        sub = _build_file_tree(os.path.join(root, d), prefix + "  ", max_depth, depth + 1)
        if sub:
            lines.append(sub.rstrip())
    if len(dirs) > 15:
        lines.append(f"{prefix}... ({len(dirs) - 15} carpetas más)")

    return "\n".join(lines)


def _extract_relevant_files(root: str, repo_name: str) -> str:
    """Extrae contenido de archivos relevantes del repo."""
    parts: list[str] = ["### Contenido de Archivos Clave\n"]
    total_chars = 0
    files_extracted = 0

    # Primero: archivos prioritarios
    for pf in PRIORITY_FILES:
        fp = os.path.join(root, pf)
        if os.path.isfile(fp):
            content = _read_file_safe(fp)
            if content:
                parts.append(f"#### {pf}\n```\n{content}\n```\n")
                total_chars += len(content)
                files_extracted += 1

    # Luego: recorrer el repo buscando archivos relevantes
    for dirpath, dirnames, filenames in os.walk(root):
        # Filtrar directorios ignorados
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS and not d.startswith(".")]

        for filename in sorted(filenames):
            if files_extracted >= MAX_FILES or total_chars >= MAX_TOTAL_CHARS:
                parts.append(f"\n*[Límite alcanzado: {files_extracted} archivos, {total_chars:,} caracteres]*")
                return "\n".join(parts)

            ext = os.path.splitext(filename)[1].lower()
            full_path = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(full_path, root)

            # Saltar si ya fue extraído como prioritario
            if filename in PRIORITY_FILES:
                continue

            if ext not in RELEVANT_EXTENSIONS:
                continue

            size = os.path.getsize(full_path)
            if size > MAX_FILE_SIZE or size == 0:
                continue

            content = _read_file_safe(full_path)
            if content and len(content.strip()) > 10:
                parts.append(f"#### {rel_path}\n```\n{content}\n```\n")
                total_chars += len(content)
                files_extracted += 1

    parts.append(f"\n**Total:** {files_extracted} archivos extraídos ({total_chars:,} caracteres)")
    return "\n".join(parts)


def _read_file_safe(file_path: str) -> str | None:
    """Lee un archivo de texto de forma segura."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read(MAX_FILE_SIZE)
        return content
    except Exception:
        return None
