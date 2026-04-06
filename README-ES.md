# Codetranslate

`codetranslate` es una herramienta CLI de Python que traduce docstrings y documentación de Markdown en bases de código de un idioma natural a otro. Utiliza modelos Helsinki-NLP/OPUS-MT a través de HuggingFace `transformers` y se ejecuta completamente localmente (no se necesitan claves API). Traducir comentarios, docstrings y documentación de Markdown en bases de código de un idioma natural a otro. Usos [Helsinki-NLP/OPUS-MT] (https://huggingface.co/Helsinki-NLP) modelos a través de HuggingFace `transformers` se ejecuta totalmente localmente sin claves API.


## Descargo de responsabilidad

Actualmente en BETA. Las traducciones son generadas por modelos de traducción automática neuronal de código abierto (Helsinki-NLP/OPUS-MT). Por lo tanto, la ejecución de esta herramienta utiliza mucha memoria y no está diseñado para documentos de texto de gran tamaño. Algunos idiomas requieren un token de autorización de HuggingFace. La calidad varía según el par de idiomas y el contexto — términos técnicos, idiomas y prosa matizada puede no traducir con precisión. Siempre revise la salida traducida antes de utilizarla en la producción.


## Traducciones disponibles de este documento

[Inglés](./README.md)  
[Español](./README-ES.md)  
[Francés](./README-FR.md)  
[Italiano](./README-IT.md)  
[Holandés](./README-NL.md)  
[Ruso](./README-RU.md)  
[Chino](./README-ZH.md)  


## Desarrollo

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

Requiere Python 3.10+ y [PyTorch](https://pytorch.org/get-started/locally/). La primera ejecución se descargará el modelo de traducción (~300 MB), que se almacena en caché en ~/.cache/huggingface/` para su uso posterior.

## Uso de inicio rápido

### Traducir un archivo o directorio local

```bash
# Translate a single file (overwrites in place)
codetranslate translate src/utils.py --to fr

# Translate a directory recursively
codetranslate translate src/ --to es

# Write translated files to a separate directory
codetranslate translate src/ --to fr --output src-fr/

# Preview without writing
codetranslate translate src/ --to es --dry-run
```

### Pruebas de instalación y ejecución
```bash
# Install (editable, with dev deps)
pip install -e ".[dev]"

# Run tests
python -m pytest tests/ -v

# Run a single test file
python -m pytest tests/test_parsers.py -v

# Run a single test
python -m pytest tests/test_parsers.py::TestParsePythonFile::test_extracts_docstrings -v

# Run with coverage
python -m pytest tests/ --cov=code_translate

# Use the CLI — local path
codetranslate translate <path> --to <lang> [--from en] [--output <dir>] [--dry-run]

# Use the CLI — single file from GitHub (downloaded via raw API, no clone)
codetranslate translate https://github.com/user/repo/blob/main/README.md --from en --to fr
codetranslate translate https://github.com/user/repo/blob/main/README.md --from en --to fr --output ./README-fr.md
```

### Traducir un repositorio de GitHub

Pase cualquier URL de GitHub repo — se cerrará de forma poco profunda de forma automática: 

```bash
# Preview translations (dry-run by default for remote repos)
codetranslate translate https://github.com/pymumu/smartdns --from zh --to en

# Write translated files to a directory
codetranslate translate https://github.com/pymumu/smartdns --from zh --to en --output ../smartdns-en

# Keep the cloned repo for inspection
codetranslate translate https://github.com/pymumu/smartdns --from zh --to en --keep-temp
```

### Lista de idiomas soportados

```bash
codetranslate languages
```

### Opciones

| Bandera | Descripción |
|------|-------------|
| `--to <code>` | Idioma de destino (obligatorio) |
| `--from <code>` | Idioma de origen (predeterminado: `en`) |
| `--output, -o <path>` | Archivo o directorio de salida (predeterminado: sobrescribir en el lugar; para archivos remotos sin `--output`, se imprime en la salida estándar) |
| `--dry-run` | Vista previa de traducciones sin escribir archivos |
| `--keep-temp` | Mantener el clon temporal al traducir un repositorio remoto |
| `--verbose, -v` | Mostrar el nombre del modelo y el progreso detallado |
| `--no-cache` | Deshabilite el caché del disco; siempre retraducir desde cero |
| `--clear-cache` | Borre todas las traducciones almacenadas en caché de `~/.cache/codetranslate/` y salga |


## Idiomas compatibles

Utiliza modelos gratis Helsinki-NLP/OPUS-MT que pueden cambiar en cualquier momento. No todos los idiomas se incluyen automáticamente, tienen que descargar en la ejecución.

| Código | Idioma |
|------|----------|
| `en` | Inglés |
| `es` | Español |
| `fr` | Francés |
| `it` | Italiano |
| `nl` | Holandés |
| `ru` | Ruso |
| `zh` | Chino |



El modelo se resuelve como `Helsinki-NLP/opus-mt-{source}-{target — si un par directo no existe, compruebe [Helsinki-NLP en HuggingFace](https://huggingface.co/Helsinki-NLP) para los modelos disponibles.
