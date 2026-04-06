"""Clone GitHub repositories and fetch individual files for translation."""

from __future__ import annotations

import re
import subprocess
import tempfile
import urllib.request
from pathlib import Path
from typing import NamedTuple

GITHUB_URL_RE = re.compile(r"^https?://github\.com/[\w.-]+/[\w.-]+/?(\.git)?$")
GITHUB_FILE_URL_RE = re.compile(
    r"^https?://github\.com/(?P<owner>[\w.-]+)/(?P<repo>[\w.-]+)/blob/(?P<rest>.+)$"
)


class GitHubFileInfo(NamedTuple):
    """Parsed components of a GitHub file URL."""

    owner: str
    repo: str
    branch: str
    filepath: str


def is_github_file_url(path: str) -> bool:
    """Check if the given string looks like a GitHub file URL (contains /blob/)."""
    return bool(GITHUB_FILE_URL_RE.match(path.strip()))


def parse_github_file_url(url: str) -> GitHubFileInfo:
    """Extract owner, repo, branch, and filepath from a GitHub file URL.

    The first path segment after 'blob/' is treated as the branch name.
    Everything after that is the file path within the repo.

    Raises ValueError if the URL doesn't match the expected pattern.
    """
    url = url.strip()
    match = GITHUB_FILE_URL_RE.match(url)
    if not match:
        raise ValueError(f"Not a valid GitHub file URL: {url}")

    owner = match.group("owner")
    repo = match.group("repo")
    rest = match.group("rest")

    parts = rest.split("/", 1)
    branch = parts[0]
    filepath = parts[1] if len(parts) > 1 else ""

    return GitHubFileInfo(owner=owner, repo=repo, branch=branch, filepath=filepath)


def fetch_github_file(info: GitHubFileInfo) -> tuple[str, bytes]:
    """Download a file from GitHub using the raw content URL.

    Args:
        info: Parsed GitHub file info.

    Returns:
        Tuple of (filename, raw content bytes).

    Raises:
        urllib.error.HTTPError: If the file doesn't exist or can't be fetched.
    """
    raw_url = f"https://raw.githubusercontent.com/{info.owner}/{info.repo}/{info.branch}/{info.filepath}"
    req = urllib.request.Request(raw_url, headers={"User-Agent": "codetranslate"})
    with urllib.request.urlopen(req) as resp:
        content = resp.read()
    filename = Path(info.filepath).name
    return filename, content


def is_github_url(path: str) -> bool:
    """Check if the given string looks like a GitHub repository URL."""
    return bool(GITHUB_URL_RE.match(path.strip()))


def normalize_url(url: str) -> str:
    """Normalize a GitHub URL: ensure it ends with .git for cloning."""
    url = url.strip()
    if not url.endswith(".git"):
        url = url + ".git"
    return url


def clone_repo(url: str, target_dir: Path | None = None) -> Path:
    """Shallow-clone a GitHub repository to a local directory.

    Args:
        url: GitHub repository URL.
        target_dir: Where to clone. If None, a temp directory is created.

    Returns:
        Path to the cloned repository root.

    Raises:
        subprocess.CalledProcessError: If git clone fails.
        ValueError: If the URL doesn't look like a GitHub repo.
    """
    if not is_github_url(url):
        raise ValueError(f"Not a valid GitHub repository URL: {url}")

    url = normalize_url(url)

    if target_dir is None:
        target_dir = Path(tempfile.mkdtemp(prefix="codetranslate-"))
    else:
        target_dir.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        ["git", "clone", "--depth", "1", url, str(target_dir)],
        check=True,
        capture_output=True,
    )

    return target_dir
