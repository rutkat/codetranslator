# codetranslate

`codetranslate` est un outil Python CLI qui traduit les docstrings et la documentation Markdown dans les bases de code d'un langage naturel à un autre. Il utilise les modèles Helsinki-NLP/OPUS-MT via les « transformateurs » HuggingFace et s'exécute entièrement localement (aucune clé API n'est nécessaire).
Traduisez les commentaires, les docstrings et la documentation Markdown dans les bases de code d'un langage naturel à un autre. Utilise les modèles [Helsinki-NLP/OPUS-MT](https://huggingface.co/Helsinki-NLP) via les « transformateurs » HuggingFace s'exécute entièrement localement sans clé API.


## Avertissement

Actuellement en version bêta. Les traductions sont générées par des modèles de traduction automatique neuronale open source (Helsinki-NLP/OPUS-MT). Par conséquent, l’exécution de cet outil utilise beaucoup de mémoire et n’est pas conçu pour les documents texte volumineux. Certaines langues nécessitent un jeton d'autorisation de HuggingFace. La qualité varie selon la paire de langues et le contexte : les termes techniques, les expressions idiomatiques et la prose nuancée peuvent ne pas être traduits avec précision. Examinez toujours la sortie traduite avant de l’utiliser en production.


## Traductions disponibles de ce document

[Anglais](./README.md)  
[Espagnol](./README-ES.md)  
[Français](./README-FR.md)  
[Italien](./README-IT.md)  
[Néerlandais](./README-NL.md)  
[Russe](./README-RU.md)  
[Chinois](./README-ZH.md)  

 
## Développement

```bash
pip install -e ".[dev]"
pytest tests/ -v
```


Nécessite Python 3.10+ et [PyTorch](https://pytorch.org/get-started/locally/). La première exécution téléchargera le modèle de traduction (~ 300 Mo), qui est mis en cache dans `~/.cache/huggingface/` pour une utilisation ultérieure.

## Utilisation du démarrage rapide

### Traduire un fichier ou un répertoire local

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

### Installation et exécution de tests
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

### Traduire un dépôt GitHub

Transmettez n'importe quelle URL de dépôt GitHub — elle sera automatiquement clonée superficiellement :

```bash
# Preview translations (dry-run by default for remote repos)
codetranslate translate https://github.com/pymumu/smartdns --from zh --to en

# Write translated files to a directory
codetranslate translate https://github.com/pymumu/smartdns --from zh --to en --output ../smartdns-en

# Keep the cloned repo for inspection
codetranslate translate https://github.com/pymumu/smartdns --from zh --to en --keep-temp
```

### Liste des langues prises en charge

```bash
codetranslate languages
```

### Possibilités

| Flag | Description |
|------|-------------|
| `--to <code>` | Langue cible (obligatoire) |
| `--from <code>` | Langue source (par défaut: `en`) |
| `--output, -o <path>` | Output file or directory (default: overwrite in place; for remote files without `--output`, prints to stdout) |
| `--dry-run` | Fichier ou répertoire de sortie (par défaut: écrasement sur place; pour les fichiers distants sans `--output`, imprime sur la sortie standard) |
| `--keep-temp` | Conservez le clone temporaire lors de la traduction d'un dépôt distant |
| `--verbose, -v` | Afficher le nom du modèle et la progression détaillée |
| `--no-cache` | Désactivez le cache disque; toujours retraduire à partir de zéro |
| `--clear-cache` | Effacez toutes les traductions en cache de `~/.cache/codetranslate/` et quittez |


## Langues prises en charge

Utilise des modèles gratuits Helsinki-NLP/OPUS-MT qui peuvent changer à tout moment. Toutes les langues ne sont pas incluses automatiquement, elles doivent être téléchargées lors de l'exécution.

| Code | Language |
|------|----------|
| `fr` | Anglais |
| `es` | Espagnol |
| `fr` | français |
| `it` | Italien |
| `nl` | Néerlandais |
| `ru` | russe |
| `zh` | Chinois |


Le modèle est résolu comme `Helsinki-NLP/opus-mt-{source}-{target}` — si une paire directe n'existe pas, consultez [Helsinki-NLP sur HuggingFace](https://huggingface.co/Helsinki-NLP) pour les modèles disponibles.