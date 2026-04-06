"""CLI entry point for codetranslate."""

from __future__ import annotations

import shutil
from pathlib import Path

import click

from . import __version__
from .languages import list_languages, resolve_model
from .translator import Translator
from .parsers import parse_file, ParseResult
from .writers import write_translated
from .git import is_github_url, is_github_file_url, clone_repo, parse_github_file_url, fetch_github_file

SUPPORTED_SUFFIXES = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".rs", ".go", ".java",
    ".c", ".cpp", ".h", ".hpp", ".cs", ".rb", ".sh", ".bash",
    ".yaml", ".yml", ".toml",
    ".md", ".txt",
}


def _derive_output_path(filepath: Path, target_lang: str) -> Path:
    """Derive a default output path by inserting ``-<target_lang>`` before the suffix.

    Examples::

        README.md           -> README-fr.md
        src/main.py         -> src/main-fr.py
        notes.txt           -> notes-de.txt
    """
    return filepath.with_name(f"{filepath.stem}-{target_lang}{filepath.suffix}")


@click.group()
@click.version_option(version=__version__, prog_name="codetranslate")
def main() -> None:
    """Translate comments, docstrings, and Markdown docs in codebases."""


@main.command()
@click.argument("path", type=str)
@click.option("--to", "target_lang", required=True, help="Target language code (e.g. fr, es, zh)")
@click.option("--from", "source_lang", default="en", help="Source language code (default: en)")
@click.option("--output", "-o", type=click.Path(path_type=Path), help="Output directory or file (default: auto-derive from input name)")
@click.option("--dry-run", is_flag=True, help="Preview translations without writing files")
@click.option("--keep-temp", is_flag=True, help="Keep cloned repo temp directory (only for URLs)")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed progress")
@click.option("--no-cache", is_flag=True, help="Disable disk cache for translations")
@click.option("--clear-cache", is_flag=True, help="Clear the translation disk cache and exit")
def translate(
    path: str,
    target_lang: str,
    source_lang: str,
    output: Path | None,
    dry_run: bool,
    keep_temp: bool,
    verbose: bool,
    no_cache: bool,
    clear_cache: bool,
) -> None:
    """Translate comments and docs in a file, directory, or GitHub repo URL."""
    from rich.console import Console

    console = Console()

    if clear_cache:
        count = Translator.clear_cache()
        console.print(f"[green]Cleared {count} cached translation(s).[/green]")
        return

    try:
        model_name = resolve_model(source_lang, target_lang)
    except ValueError as e:
        raise click.BadParameter(str(e), param_hint="--from/--to") from None

    if verbose:
        console.print(f"[dim]Model: {model_name}[/dim]")

    translator = Translator(model_name, no_cache=no_cache)

    # --- Handle remote GitHub URLs ---
    clone_dir: Path | None = None
    temp_file: Path | None = None
    work_path: Path | None = None

    if is_github_file_url(path):
        _handle_github_file(console, translator, path, source_lang, target_lang, output, dry_run, verbose)
        return

    if is_github_url(path):
        console.print(f"[dim]Cloning {path}...[/dim]")
        clone_dir = clone_repo(path)
        work_path = clone_dir
        if output is None:
            # Auto-derive output directory: <repo-name>-<lang>
            output = Path(f"{work_path.name}-{target_lang}")
            if verbose:
                console.print(f"[dim]Output directory: {output}[/dim]")
    else:
        work_path = Path(path)
        if not work_path.exists():
            raise click.BadParameter(f"Path does not exist: {work_path}", param_hint="path")

    try:
        _do_translate(console, translator, work_path, output, target_lang, dry_run, verbose)
    finally:
        # Clean up cloned repo unless --keep-temp
        if clone_dir is not None and not keep_temp:
            if verbose:
                console.print(f"[dim]Cleaning up {clone_dir}[/dim]")
            shutil.rmtree(clone_dir, ignore_errors=True)


def _handle_github_file(
    console,
    translator: Translator,
    url: str,
    source_lang: str,
    target_lang: str,
    output: Path | None,
    dry_run: bool,
    verbose: bool,
) -> None:
    """Handle translation of a single file from a GitHub URL."""
    import tempfile as tf

    info = parse_github_file_url(url)
    if verbose:
        console.print(f"[dim]Fetching {info.filepath} from {info.owner}/{info.repo} (branch: {info.branch})[/dim]")

    filename, content = fetch_github_file(info)
    console.print(f"[dim]Downloaded {filename} ({len(content)} bytes)[/dim]")

    # Write to a temp file so parse_file can read it
    tmp = Path(tf.mkdtemp(prefix="codetranslate-")) / filename
    tmp.write_bytes(content)

    try:
        parsed = parse_file(tmp)
        if not parsed.segments:
            console.print("[yellow]No translatable content found in this file.[/yellow]")
            return

        translated_segments = translator.translate_segments(parsed.segments)

        if dry_run:
            for original, translated in zip(parsed.segments, translated_segments):
                console.print(f"[cyan]{info.filepath}:[/cyan]")
                console.print(f"  [dim]{original.text[:120]}[/dim]")
                console.print(f"  [green]{translated.text[:120]}[/green]")
            console.print("[yellow]Dry run complete — no files were written.[/yellow]")
        else:
            # Derive default output path if --output not specified
            if output is None:
                output = _derive_output_path(Path(filename), target_lang)
            output.parent.mkdir(parents=True, exist_ok=True)
            write_translated(parsed, translated_segments, output)
            console.print(f"[green]Translated file written to {output}[/green]")
    finally:
        # Clean up temp file
        tmp.unlink(missing_ok=True)
        tmp.parent.rmdir()


def _do_translate(
    console,
    translator: Translator,
    work_path: Path,
    output: Path | None,
    target_lang: str,
    dry_run: bool,
    verbose: bool,
) -> None:
    """Core translation logic shared by local and remote paths."""

    # Collect files
    if work_path.is_file():
        files = [work_path]
    else:
        files = sorted(
            p
            for p in work_path.rglob("*")
            if p.is_file() and p.suffix in SUPPORTED_SUFFIXES
        )

    if not files:
        console.print("[yellow]No translatable files found.[/yellow]")
        return

    for filepath in files:
        rel = filepath.relative_to(work_path) if filepath.is_relative_to(work_path) else filepath
        if verbose:
            console.print(f"[dim]Processing {rel}...[/dim]")

        parsed = parse_file(filepath)
        if not parsed.segments:
            continue

        translated_segments = translator.translate_segments(parsed.segments)

        if dry_run:
            for original, translated in zip(parsed.segments, translated_segments):
                console.print(f"[cyan]{rel}:[/cyan]")
                console.print(f"  [dim]{original.text[:80]}[/dim]")
                console.print(f"  [green]{translated.text[:80]}[/green]")
        else:
            # Determine destination path
            if output is not None:
                # --output was explicitly provided
                if filepath.is_relative_to(work_path):
                    dest = output / filepath.relative_to(work_path)
                else:
                    dest = output / filepath.name
                dest.parent.mkdir(parents=True, exist_ok=True)
            elif work_path.is_file():
                # Single local file, no --output: derive from filename
                dest = _derive_output_path(filepath, target_lang)
            else:
                # Local directory, no --output: write alongside originals with -lang suffix
                if filepath.is_relative_to(work_path):
                    dest = work_path / _derive_output_path(
                        Path(filepath.name), target_lang
                    )
                    # Preserve subdirectory structure
                    parent_rel = filepath.parent.relative_to(work_path) if filepath.parent != work_path else None
                    if parent_rel and str(parent_rel) != ".":
                        dest = work_path / parent_rel / dest.name
                else:
                    dest = _derive_output_path(filepath, target_lang)

            write_translated(parsed, translated_segments, dest)

    if dry_run:
        console.print("[yellow]Dry run complete — no files were modified.[/yellow]")
    else:
        console.print(f"[green]Done. Translated {len(files)} file(s) to {target_lang}.[/green]")


@main.command("languages")
def languages_cmd() -> None:
    """List supported language codes and names."""
    from rich.console import Console
    from rich.table import Table

    console = Console()
    langs = list_languages()

    table = Table(title="Supported Languages")
    table.add_column("Code", style="cyan")
    table.add_column("Name")

    for code, name in sorted(langs.items(), key=lambda x: x[0]):
        table.add_row(code, name)

    console.print(table)
