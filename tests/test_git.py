"""Tests for the git module."""

import pytest

from code_translate.git import is_github_url, is_github_file_url, normalize_url, clone_repo, parse_github_file_url


class TestIsGitHubUrl:
    def test_standard_https(self):
        assert is_github_url("https://github.com/pymumu/smartdns")

    def test_trailing_slash(self):
        assert is_github_url("https://github.com/pymumu/smartdns/")

    def test_with_git_extension(self):
        assert is_github_url("https://github.com/pymumu/smartdns.git")

    def test_http(self):
        assert is_github_url("http://github.com/pymumu/smartdns")

    def test_with_dots_in_name(self):
        assert is_github_url("https://github.com/org.name/repo.name")

    def test_rejects_non_github(self):
        assert not is_github_url("https://gitlab.com/user/repo")

    def test_rejects_local_path(self):
        assert not is_github_url("/usr/local/src/project")

    def test_rejects_random_url(self):
        assert not is_github_url("https://example.com/page")

    def test_rejects_empty(self):
        assert not is_github_url("")

    def test_rejects_partial_match(self):
        assert not is_github_url("https://github.com/")

    def test_whitespace_trimmed(self):
        assert is_github_url("  https://github.com/pymumu/smartdns  ")


class TestNormalizeUrl:
    def test_adds_git_suffix(self):
        assert normalize_url("https://github.com/pymumu/smartdns") == "https://github.com/pymumu/smartdns.git"

    def test_preserves_git_suffix(self):
        assert normalize_url("https://github.com/pymumu/smartdns.git") == "https://github.com/pymumu/smartdns.git"

    def test_trims_whitespace(self):
        assert normalize_url("  https://github.com/pymumu/smartdns  ") == "https://github.com/pymumu/smartdns.git"

    def test_handles_trailing_slash(self):
        assert normalize_url("https://github.com/pymumu/smartdns/") == "https://github.com/pymumu/smartdns/.git"


class TestCloneRepo:
    def test_rejects_non_github_url(self):
        with pytest.raises(ValueError, match="Not a valid GitHub"):
            clone_repo("https://gitlab.com/user/repo")

    def test_rejects_empty_url(self):
        with pytest.raises(ValueError):
            clone_repo("")


class TestIsGitHubFileUrl:
    def test_standard_file_url(self):
        assert is_github_file_url(
            "https://github.com/davideuler/architecture.of.internet-product/blob/master/README.md"
        )

    def test_nested_path(self):
        assert is_github_file_url(
            "https://github.com/org/repo/blob/main/src/utils/helper.py"
        )

    def test_rejects_repo_url(self):
        assert not is_github_file_url("https://github.com/pymumu/smartdns")

    def test_rejects_non_github(self):
        assert not is_github_file_url("https://gitlab.com/user/repo/blob/main/file.py")

    def test_rejects_empty(self):
        assert not is_github_file_url("")

    def test_rejects_missing_blob(self):
        assert not is_github_file_url("https://github.com/org/repo/main/file.py")

    def test_whitespace_trimmed(self):
        assert is_github_file_url(
            "  https://github.com/org/repo/blob/main/file.py  "
        )


class TestParseGitHubFileUrl:
    def test_parse_readme(self):
        info = parse_github_file_url(
            "https://github.com/davideuler/architecture.of.internet-product/blob/master/README.md"
        )
        assert info.owner == "davideuler"
        assert info.repo == "architecture.of.internet-product"
        assert info.branch == "master"
        assert info.filepath == "README.md"

    def test_parse_nested(self):
        info = parse_github_file_url(
            "https://github.com/org/repo/blob/main/src/utils/helper.py"
        )
        assert info.owner == "org"
        assert info.repo == "repo"
        assert info.branch == "main"
        assert info.filepath == "src/utils/helper.py"

    def test_parse_branch_with_special_chars(self):
        info = parse_github_file_url(
            "https://github.com/org/repo/blob/feature/add-login/docs/guide.md"
        )
        # First segment after blob/ is the branch; slashes in branch names
        # are not supported for single-file URL mode — use repo clone instead.
        assert info.branch == "feature"
        assert info.filepath == "add-login/docs/guide.md"

    def test_parse_dots_in_repo_name(self):
        info = parse_github_file_url(
            "https://github.com/my-org/my.project/blob/dev/README.md"
        )
        assert info.owner == "my-org"
        assert info.repo == "my.project"
        assert info.branch == "dev"

    def test_rejects_invalid(self):
        with pytest.raises(ValueError, match="Not a valid GitHub file URL"):
            parse_github_file_url("https://github.com/org/repo")

    def test_rejects_non_github(self):
        with pytest.raises(ValueError):
            parse_github_file_url("https://gitlab.com/org/repo/blob/main/file.py")
