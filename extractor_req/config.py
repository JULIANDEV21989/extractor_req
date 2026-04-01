"""Carga y gestión de configuración."""

import os
from dataclasses import dataclass, field

import yaml


@dataclass
class VideoConfig:
    frame_interval: int = 15
    whisper_model: str = "medium"
    language: str = "es"
    transcribe_audio: bool = True


@dataclass
class AnalysisConfig:
    provider: str = "anthropic"
    model: str = "claude-sonnet-4-20250514"
    api_key: str = ""
    max_tokens: int = 16000


@dataclass
class OutputConfig:
    formats: list[str] = field(default_factory=lambda: ["markdown", "docx"])


@dataclass
class AppConfig:
    input_dir: str = "input"
    output_dir: str = "output"
    video: VideoConfig = field(default_factory=VideoConfig)
    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)
    output: OutputConfig = field(default_factory=OutputConfig)

    @property
    def effective_api_key(self) -> str | None:
        """Retorna la API key desde config o variable de entorno."""
        return self.analysis.api_key or os.environ.get("ANTHROPIC_API_KEY") or None


def load_config(config_path: str = "config.yaml") -> AppConfig:
    """Carga configuración desde archivo YAML. Usa defaults si no existe."""
    if not os.path.exists(config_path):
        return AppConfig()

    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    video_data = data.get("video", {})
    analysis_data = data.get("analysis", {})
    output_data = data.get("output", {})

    return AppConfig(
        input_dir=data.get("input_dir", "input"),
        output_dir=data.get("output_dir", "output"),
        video=VideoConfig(**{k: v for k, v in video_data.items() if k in VideoConfig.__dataclass_fields__}),
        analysis=AnalysisConfig(**{k: v for k, v in analysis_data.items() if k in AnalysisConfig.__dataclass_fields__}),
        output=OutputConfig(**{k: v for k, v in output_data.items() if k in OutputConfig.__dataclass_fields__}),
    )
