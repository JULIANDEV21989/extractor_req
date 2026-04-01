"""Escanea una carpeta recursivamente y clasifica archivos por tipo."""

import os
from dataclasses import dataclass, field
from pathlib import Path

EXTENSION_MAP: dict[str, str] = {
    ".pdf": "pdf",
    ".docx": "docx", ".doc": "docx",
    ".png": "image", ".jpg": "image", ".jpeg": "image", ".bmp": "image",
    ".tiff": "image", ".gif": "image", ".webp": "image",
    ".mp4": "video", ".avi": "video", ".mov": "video",
    ".mkv": "video", ".webm": "video",
    ".eml": "email", ".msg": "email",
    ".xlsx": "spreadsheet", ".xls": "spreadsheet", ".csv": "spreadsheet",
    ".txt": "text", ".md": "text", ".log": "text",
}


@dataclass
class FileInfo:
    path: str
    name: str
    extension: str
    file_type: str
    size_bytes: int
    folder: str

    @property
    def size_mb(self) -> float:
        return self.size_bytes / 1024 / 1024


@dataclass
class ScanResult:
    files: list[FileInfo] = field(default_factory=list)
    total_size_bytes: int = 0

    @property
    def by_type(self) -> dict[str, list[FileInfo]]:
        result: dict[str, list[FileInfo]] = {}
        for f in self.files:
            result.setdefault(f.file_type, []).append(f)
        return result

    @property
    def by_folder(self) -> dict[str, list[FileInfo]]:
        result: dict[str, list[FileInfo]] = {}
        for f in self.files:
            result.setdefault(f.folder, []).append(f)
        return result

    def summary_lines(self) -> list[str]:
        lines = [f"Total: {len(self.files)} archivos ({self.total_size_bytes / 1024 / 1024:.1f} MB)"]
        for ftype, files in sorted(self.by_type.items()):
            total_mb = sum(f.size_bytes for f in files) / 1024 / 1024
            lines.append(f"  {ftype}: {len(files)} ({total_mb:.1f} MB)")
        return lines


def scan_directory(root_path: str) -> ScanResult:
    """Escanea una carpeta recursivamente y clasifica archivos."""
    root = Path(root_path)
    if not root.exists():
        raise FileNotFoundError(f"Directorio no encontrado: {root_path}")

    result = ScanResult()
    for dirpath, _, filenames in os.walk(root):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            ext = os.path.splitext(filename)[1].lower()
            file_type = EXTENSION_MAP.get(ext, "unknown")
            if file_type == "unknown":
                continue
            size = os.path.getsize(filepath)
            result.files.append(FileInfo(
                path=filepath,
                name=filename,
                extension=ext,
                file_type=file_type,
                size_bytes=size,
                folder=os.path.basename(dirpath),
            ))
            result.total_size_bytes += size
    return result
