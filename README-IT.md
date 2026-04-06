# codetranslate

codetranslate è uno strumento Python CLI che traduce docstring e documentazione Markdown in basi di codice da un linguaggio naturale all'altro. Usa i modelli Helsinki-NLP/OPUS-MT tramite i trasformatori HuggingFace e funziona interamente localmente (nessuna chiave API necessaria). Tradurre commenti, docstring e documentazione Markdown in basi di codice da un linguaggio naturale all'altro. Usa i modelli [Helsinki-NLP/OPUS-MT](https://huggingface.co/Helsinki-NLP) i modelli tramite i trasformatori HuggingFace girano interamente localmente senza chiavi API.


## Disclaimer

Attualmente in BETA. Le traduzioni sono generate da modelli di traduzione automatica neurale open-source (Helsinki-NLP/OPUS-MT). Pertanto, l'esecuzione di questo strumento utilizza un sacco di memoria e non è progettato per documenti di testo di grandi dimensioni. Alcune lingue richiedono un token di autorizzazione da HuggingFace. La qualità varia a seconda della coppia di lingua e termini tecnici contesto, idiomi, e prosa sfumata non può tradurre con precisione.


## Le traduzioni disponibili di questo documento

[English](./README.md)  
[Spagnolo](./README-ES.md)  
[Francese](./README-FR.md)  
[Italiano](./README-IT.md)  
[Olandese](./README-NL.md)  
[Russiano](./README-RU.md)  
[Cinese](./README-ZH.md)  


## Sviluppo

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

Richiede Python 3.10+ e [PyTorch](https://pytorch.org/get-started/locally/). La prima esecuzione scaricherà il modello di traduzione (~300 MB), che è cached in ~/.cache/huggingface/ per l'uso successivo.

## Quickstart Usage

### Traduci un file o una directory locale

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

### Test di installazione e esecuzione
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

### Traduci un repository GitHub

Passare qualsiasi URL repo di GitHub verrà clonato automaticamente:

```bash
# Preview translations (dry-run by default for remote repos)
codetranslate translate https://github.com/pymumu/smartdns --from zh --to en

# Write translated files to a directory
codetranslate translate https://github.com/pymumu/smartdns --from zh --to en --output ../smartdns-en

# Keep the cloned repo for inspection
codetranslate translate https://github.com/pymumu/smartdns --from zh --to en --keep-temp
```

### Lista lingue supportate

```bash
codetranslate languages
```

### Opzioni

| Flag | Descrizione |
|------|-------------|
| `--to <code>` | Lingua di destinazione (obbligatorio) |
| `--from <code>` | Lingua di origine (predefinita: `en`) |
| `--output, -o <path>` | Output file or directory (default: overwrite in place; for remote files without `--output`, prints to stdout) |
| `--dry-run` | File o directory di output (predefinito: sovrascrive in loco; per i file remoti senza `--output`, stampa su stdout) |
| `--keep-temp` | Mantieni la copia temporanea durante la traduzione di un repository remoto |
| `--verbose, -v` | Mostra nome del modello e stato di avanzamento dettagliato |
| `--no-cache` | Disabilita la cache su disco; ritraduci sempre da zero |
| `--clear-cache` | Cancella tutte le traduzioni memorizzate nella cache da `~/.cache/codetranslate/` ed esci |


## Lingue supportate

Utilizza modelli Helsinki-NLP/OPUS-MT gratuiti che possono cambiare in qualsiasi momento. Non tutte le lingue sono incluse automaticamente, devono essere scaricate al momento dell'esecuzione.

| Code | Language |
|------|----------|
| `en` | English |
| `es` | Spagnolo |
| `fr` | Francese |
| `it` | Italiano |
| `nl` | Olandese |
| `ru` | Ruota |
| `zh` | Cinese |

Il modello è risolto come Helsinki-NLP/opus-mt-{source}-{target} se una coppia diretta non esiste, controllare [Helsinki-NLP on HuggingFace](https://huggingface.co/Helsinki-NLP) per i modelli disponibili.
