# codetranslate
“codetranslate”是一个 Python CLI 工具，可将代码库中的注释、文档字符串和 Markdown 文档从一种自然语言翻译为另一种自然语言。它通过 HuggingFace “transformers” 使用 Helsinki-NLP/OPUS-MT 模型，并完全在本地运行（不需要 API 密钥）。
将代码库中的注释、文档字符串和 Markdown 文档从一种自然语言翻译为另一种自然语言。通过 HuggingFace `transformers` 使用 [Helsinki-NLP/OPUS-MT](https://huggingface.co/Helsinki-NLP) 模型，完全在本地运行，无需 API 密钥。


## 免责声明

目前处于测试阶段。翻译由开源神经机器翻译模型（Helsinki-NLP/OPUS-MT）生成。因此，运行此工具会使用大量内存，并且不适合大型文本文档。某些语言需要 HuggingFace 的授权令牌。质量因语言对和上下文而异——技术术语、习语和细致入微的散文可能无法准确翻译。在生产中使用翻译后的输出之前，请务必先对其进行检查。

## 本文档的可用翻译

[英语](./README.md)  
[西班牙语](./README-ES.md)  
[法语](./README-FR.md)  
[意大利语](./README-IT.md)  
[荷兰语](./README-NL.md)  
[俄语](./README-RU.md)  
[中文](./README-ZH.md)  
 
 
## Development

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

需要 Python 3.10+ 和 [PyTorch](https://pytorch.org/get-started/locally/)。第一次运行将下载翻译模型（~300 MB），该模型缓存在“~/.cache/huggingface/”中以供后续使用。

## 快速入门使用

### 翻译本地文件或目录


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

### 安装和运行测试

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

### 翻译 GitHub 存储库

传递任何 GitHub 存储库 URL — 它将自动浅克隆：

```bash
# Preview translations (dry-run by default for remote repos)
codetranslate translate https://github.com/pymumu/smartdns --from zh --to en

# Write translated files to a directory
codetranslate translate https://github.com/pymumu/smartdns --from zh --to en --output ../smartdns-en

# Keep the cloned repo for inspection
codetranslate translate https://github.com/pymumu/smartdns --from zh --to en --keep-temp
```

### 列出支持的语言

```bash
codetranslate languages
```

### 选项

|旗帜|描述 |
|------|-------------|
| `--to <code>` |目标语言（必填）|
| `--from <code>`  |源语言（默认：`en`）|
| `--output, -o <path>` |输出文件或目录（默认：就地覆盖；对于没有“--output”的远程文件，打印到标准输出）|
| `--dry-run` |无需写入文件即可预览翻译 |
| `--keep-temp` |翻译远程存储库时保留临时克隆 |
| `--verbose, -v` |显示模型名称和详细进度 |
| `--no-cache`  |禁用磁盘缓存；总是从头开始重新翻译 |
| `--clear-cache`  |从 `~/.cache/codetranslate/` 清除所有缓存的翻译并退出 |

## 支持的语言

使用免费的 Helsinki-NLP/OPUS-MT 模型，该模型可能随时更改。并非所有语言都会自动包含，它们必须在执行时下载。

|代码|语言 |
|------|----------|
| `en` |英语 |
| `es` |西班牙语 |
| `fr` |法语 |
| `it` |意大利语 |
| `nl` |荷兰语 |
| `ru` |俄语 |
| `zh` |中文 |

该模型被解析为“Helsinki-NLP/opus-mt-{source}-{target}”——如果不存在直接对，请检查 [HuggingFace 上的 Helsinki-NLP](https://huggingface.co/Helsinki-NLP) 以获取可用模型。
