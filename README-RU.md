# Перевод кода

"Codetranslate" - это инструмент Python CLI, который переводит комментарии, докстринги и документацию маркирования в кодовых базах с одного естественного языка на другой. Он использует модели Helsinki-NLP/OPS-MT через HuggingFace "transformers" и работает полностью на местном уровне (не требуется ключей API). Переведите комментарии, докструкции и документацию маркирования в кодовых базах с одного естественного языка на другой. Использование [Helsinki-NLP/OPS-MT] (https://huggingface.co/Helsinki-NLP) моделей через HuggingFace "transformers" работает полностью на местном уровне без ключей API.


# # Отказываюсь

В настоящее время в БЕТА. Переводы производятся открытыми исходными моделями нейронного перевода (Helsinki-NLP/OPUS-MT). Таким образом, использование этого инструмента использует много памяти и не предназначено для больших текстовых документов. Некоторые языки нуждаются в символе разрешения от HuggingFace. Качество варьируется в зависимости от пары языков и контекста — технические термины, идиомы и нюансовые прозы могут не переводиться точно.


# # Этот документ доступен для перевода

[английском](./README.md)  
[Испаноязычный](./README-ES.md)  
[французский](./README-FR.md)  
[Итальянский язык](./README-IT.md)  
[вьетнамский](./README-NL.md)  
[русский](./README-RU.md)  
[китайский](./README-ZH.md)  
 
 
### Опции

| Флаг | Описание |
|------|-------------|
| `--to <code>` | Язык перевода (обязательно) |
| `--from <code>` | Исходный язык (по умолчанию: `en`) |
| `--output, -o <path>` | Выходной файл или каталог (по умолчанию: перезаписать на месте; для удаленных файлов без `--output` выводится на стандартный вывод) |
| `--dry-run` | Предварительный просмотр переводов без записи файлов |
| `--keep-temp` | Сохранять временный клон при переводе удаленного репозитория |
| `--verbose, -v` | Показать название модели и подробный прогресс |
| `--no-cache` | Отключить дисковый кэш; всегда переводить с нуля |
| `--clear-cache` | Очистите все кэшированные переводы из `~/.cache/codetranslate/` и выйдите |

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

Требуется Python 3.10+ и [PyTorch](https://pytorch.org/get-started/locally/). При первом запуске будет загружена модель перевода (~300 МБ), которая кэшируется в `~/.cache/huggingface/` для последующего использования.

## Краткое использование

### Перевести локальный файл или каталог

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

### Установка и запуск тестов
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

### Перевести репозиторий GitHub

Передайте любой URL-адрес репозитория GitHub — он будет автоматически клонирован:

```bash
# Preview translations (dry-run by default for remote repos)
codetranslate translate https://github.com/pymumu/smartdns --from zh --to en

# Write translated files to a directory
codetranslate translate https://github.com/pymumu/smartdns --from zh --to en --output ../smartdns-en

# Keep the cloned repo for inspection
codetranslate translate https://github.com/pymumu/smartdns --from zh --to en --keep-temp
```


### Список поддерживаемых языков

``` баш
кодовый перевод языков
```

### Опции

| Флаг | Описание |
|------|-------------|
| `--to <code>` | Язык перевода (обязательно) |
| `--from <code>` | Исходный язык (по умолчанию: `en`) |
| `--output, -o <path>` | Выходной файл или каталог (по умолчанию: перезаписать на месте; для удаленных файлов без `--output` выводится на стандартный | `--dry-run` | Предварительный просмотр переводов без записи файлов |
| `--keep-temp` | Сохранять временный клон при переводе удаленного репозитория |
| `--verbose, -v` | Показать название модели и подробный прогресс |
| `--no-cache` | Отключить дисковый кэш; всегда переводить с нуля |
| `--clear-cache` | Очистите все кэшированные переводы из `~/.cache/codetranslate/` и выйдите |


## Поддерживаемые языки

Использует бесплатные модели Helsinki-NLP/OPUS-MT, которые могут измениться в любое время. Не все языки включаются автоматически, их приходится скачивать при выполнении.

| Код | Язык |
|------|----------|
| `en` | английский |
| `es` | испанский |
| `fr` | французский |
| `it` | итальянский |
| `nl` | голландский |
| `ru` | Русский |
| `zh` | китайский |

Модель разрешается как «Helsinki-NLP/opus-mt-{source}-{target}» — если прямой пары не существует, проверьте доступные модели [Helsinki-NLP на HuggingFace](https://huggingface.co/Helsinki-NLP).
