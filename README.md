# Extractor de Requerimientos Tecnicos

Pipeline inteligente que analiza documentos, videos, correos y genera un documento tecnico de desarrollo con alcance funcional completo.

## Como funciona

```
input/                          output/
├── reuniones.mp4        →      ├── consolidado.md          (texto extraido de todo)
├── transcripciones.docx →      ├── consolidado.docx        (version Word)
├── facturas.pdf         →      ├── requerimiento_tecnico.md (requerimiento generado por IA)
├── correos.eml          →      ├── requerimiento_tecnico.docx
└── diagramas.png        →      └── frames/                 (capturas de video)
```

## Instalacion

```bash
# Clonar
git clone https://github.com/JULIANDEV21989/extractor_req.git
cd extractor_req

# Instalar dependencias
pip install -e .

# Requisito del sistema: ffmpeg (para videos)
# Windows: winget install ffmpeg
# Mac: brew install ffmpeg
# Linux: sudo apt install ffmpeg
```

## Uso rapido

### 1. Coloca tus archivos en `input/`

Mete todo: PDFs, Word, videos MP4, correos (.eml/.msg), imagenes.
Puedes organizarlos en subcarpetas.

### 2. Ejecuta

```bash
# Modo completo (extraccion + analisis con Claude API)
extractor-req --api-key sk-ant-xxxxx

# Solo extraccion (sin API, para analizar manualmente)
extractor-req --skip-analysis

# Sin transcripcion de video (solo extrae frames)
extractor-req --no-transcribe

# Carpetas personalizadas
extractor-req -i mis_docs/ -o resultado/

# Modelo Whisper mas ligero (si poca RAM)
extractor-req --whisper-model small
```

### 3. Resultado en `output/`

- **consolidado.md** — Todo el texto extraido, organizado por carpeta
- **requerimiento_tecnico.md** — Requerimiento estructurado generado por Claude
- **frames/** — Capturas de video para analisis visual

## Tipos de archivo soportados

| Tipo | Extensiones | Metodo de extraccion |
|------|-------------|---------------------|
| PDF | .pdf | PyMuPDF + pymupdf4llm (tablas, estructura, OCR basico) |
| Word | .docx | python-docx (preserva headings, tablas, listas) |
| Video | .mp4 .avi .mov | ffmpeg (frames) + faster-whisper (transcripcion) |
| Imagen | .png .jpg .webp | Claude Vision API (si hay key) o registro para analisis manual |
| Email | .eml .msg | email.parser (stdlib) + extract-msg |
| Texto | .txt .md .log | Lectura directa |

## Configuracion

Copia `config.example.yaml` como `config.yaml`:

```yaml
input_dir: "input"
output_dir: "output"

video:
  frame_interval: 15        # segundos entre frames
  whisper_model: "medium"    # tiny|base|small|medium|large-v3
  language: "es"
  transcribe_audio: true

analysis:
  provider: "anthropic"
  model: "claude-sonnet-4-20250514"
  api_key: ""               # o usa ANTHROPIC_API_KEY env var
  max_tokens: 16000

output:
  formats: ["markdown", "docx"]
```

## Uso sin API (con Claude Code o claude.ai)

Si no tienes API key pero si suscripcion de Claude:

1. Ejecuta: `extractor-req --skip-analysis`
2. Abre `output/consolidado.md`
3. Pegalo en Claude Code o claude.ai con el prompt de `prompts/requirements_analysis.md`

## Estructura del proyecto

```
extractor_req/
├── src/
│   ├── cli.py              # CLI principal con rich
│   ├── config.py           # Carga de configuracion YAML
│   ├── scanner.py          # Escaneo y clasificacion de archivos
│   ├── consolidator.py     # Engine de extraccion y consolidacion
│   ├── extractors/
│   │   ├── pdf.py          # PyMuPDF + pymupdf4llm
│   │   ├── docx.py         # python-docx
│   │   ├── video.py        # ffmpeg + faster-whisper
│   │   ├── image.py        # Claude Vision o registro
│   │   └── email.py        # .eml + .msg parser
│   ├── analysis/
│   │   └── analyzer.py     # Analisis con Claude API
│   └── output/
│       └── writer.py       # Generador Markdown + DOCX
├── prompts/
│   └── requirements_analysis.md  # Prompt para uso manual
├── input/                  # Pon tus archivos aqui
├── config.example.yaml
├── pyproject.toml
└── README.md
```

## Requisitos de hardware

| Componente | Sin video | Con video (CPU) |
|------------|-----------|----------------|
| RAM | 4 GB | 8-16 GB |
| Disco | 1 GB | 5+ GB (modelos Whisper) |
| GPU | No necesaria | No necesaria (CPU funciona) |
| ffmpeg | No necesario | Requerido |
