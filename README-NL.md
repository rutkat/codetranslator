# codetranslate

codetranslate is een Python CLI tool die docstrings en Markdown documentatie vertaalt in codebases van de ene natuurlijke taal naar de andere. Het maakt gebruik van Helsinki-NLP/OPUS-MT modellen via HuggingFace transformatoren en draait volledig lokaal (geen API sleutels nodig). Vertaal commentaar, docstrings, en markdown documentatie in codebases van de ene natuurlijke taal naar de andere. Gebruikt [Helsinki-NLP/OPUS-MT](https://huggingface.co/Helsinki-NLP) modellen via HuggingFace transformatoren draait volledig lokaal met geen API sleutels.


## Disclaimer

Momenteel in BETA. Vertalingen worden gegenereerd door open-source neurale machine vertaling modellen (Helsinki-NLP/OPUS-MT). Daarom het uitvoeren van deze tool maakt gebruik van veel geheugen en is niet ontworpen voor grote tekstdocumenten. Sommige talen vereisen een autorisatie token van HuggingFace. Kwaliteit varieert per taal paar en context technische termen, idiomen, en genuanceerde proza kan niet correct vertalen. Altijd de vertaalde output te beoordelen voordat u het in productie.


## De beschikbare vertalingen van dit document

[Engels](./README.md)  
[Spaans](./README-ES.md)  
[Frans](./README-FR.md)  
[Italiaans](./README-IT.md)  
[Nederlands](./README-NL.md)  
[Russisch](./README-RU.md)  
[Chinees](./README-ZH.md)  
 
 
Ontwikkeling

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

Vereist Python 3.10+ en [PyTorch](https://pytorch.org/get-started/locally/). De eerste run downloadt het vertaalmodel (~300 MB), dat wordt gecached in ~/.cache/huggingface/ voor later gebruik.

## Quickstart Usage

### Een lokaal bestand of map vertalen

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

Installeren en uitvoeren van tests
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
python -m pytest tests/ --cov=codetranslate

# Use the CLI — local path
codetranslate translate <path> --to <lang> [--from en] [--output <dir>] [--dry-run]

# Use the CLI — single file from GitHub (downloaded via raw API, no clone)
codetranslate translate https://github.com/user/repo/blob/main/README.md --from en --to fr
codetranslate translate https://github.com/user/repo/blob/main/README.md --from en --to fr --output ./README-fr.md
```

Vertaal een GitHub repository

Pass elke GitHub repo-URL het zal worden ondiep-cloned automatisch:

```bash
# Preview translations (dry-run by default for remote repos)
codetranslate translate https://github.com/pymumu/smartdns --from zh --to en

# Write translated files to a directory
codetranslate translate https://github.com/pymumu/smartdns --from zh --to en --output ../smartdns-en

# Keep the cloned repo for inspection
codetranslate translate https://github.com/pymumu/smartdns --from zh --to en --keep-temp
```

Lijst ondersteunde talen

```bash
codetranslate languages
```

### Opties

| Flag | Description |
|------|-------------|
| `--to <code>` | Doeltaal (vereist) |
| `--from <code>` | Brontaal (standaard: `en`) |
| `--output, -o <path>` | Uitvoerbestand of map (standaard: overschrijven ter plaatse; voor bestanden op afstand zonder `--output`, wordt afgedrukt naar stdout) |
| `--dry-run` | Bekijk een voorbeeld van vertalingen zonder bestanden te schrijven|
| `--keep-temp` | Bewaar de tijdelijke kloon bij het vertalen van een externe opslagplaats|
| `--verbose, -v` | Toon modelnaam en gedetailleerde voortgang|
| `--no-cache` | Schakel de schijfcache uit; altijd opnieuw vertalen vanaf nul |
| `--clear-cache` | Wis alle in de cache opgeslagen vertalingen van `~/.cache/codetranslate/` en sluit af|


## Ondersteunde talen

Maakt gebruik van gratis Helsinki-NLP/OPUS-MT-modellen die op elk moment kunnen veranderen. Niet alle talen zijn automatisch inbegrepen; ze moeten bij uitvoering worden gedownload.

| Code | Language |
|------|----------|
| `en` | Engels |
| `es` | Spaans |
| `fr` | Frans |
| `it` | Italiaans |
| `nl` | Nederlands |
| `ru` | Russisch |
| `zh` | Chinees |

Het model wordt omgezet als `Helsinki-NLP/opus-mt-{source}-{target}` — als er geen direct paar bestaat, controleer dan [Helsinki-NLP op HuggingFace](https://huggingface.co/Helsinki-NLP) voor beschikbare modellen.
