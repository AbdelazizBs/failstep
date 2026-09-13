from __future__ import annotations

import tomllib
from pathlib import Path

from typer.testing import CliRunner

from failstep import __version__
from failstep.cli import app

ROOT = Path(__file__).resolve().parents[1]
BANNED = ("linkedin", "youtube.com", "twitter.com", "x.com/")
GONE_DOCS = (
    ROOT / "docs" / "COMPETITORS.md",
    ROOT / "docs" / "POSITIONING.md",
)
BANNED_DOCS_PHRASES = (
    "lookalike",
    "name squat",
    "kitchen sink",
    "agent-debug",
    "agentdebugx",
    "agentlint",
    "whyfail",
    "agentinspect",
    "langfuse",
)


def test_help_lists_commands(runner: CliRunner) -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for name in ("inspect", "diagnose", "compare", "fix", "version"):
        assert name in result.stdout


def test_version_matches_pyproject() -> None:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert data["project"]["version"] == __version__


def test_changelog_names_this_version() -> None:
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert f"## {__version__}" in text


def test_ci_matrix() -> None:
    text = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "3.11" in text
    assert "3.12" in text
    assert "3.13" in text
    assert "ubuntu-latest" in text
    assert "windows-latest" in text
    assert "python -m pytest" in text
    assert "python -m ruff check ." in text


def test_docs_stay_product_only() -> None:
    paths = [
        ROOT / "README.md",
        ROOT / "CONTRIBUTING.md",
        ROOT / "CHANGELOG.md",
        *sorted((ROOT / "docs").glob("*.md")),
        *sorted((ROOT / ".github").rglob("*.md")),
        *sorted((ROOT / ".github").rglob("*.yml")),
    ]
    hits: list[str] = []
    for path in paths:
        blob = path.read_text(encoding="utf-8").lower()
        for word in (*BANNED, *BANNED_DOCS_PHRASES):
            if word in blob:
                hits.append(f"{path.relative_to(ROOT)}:{word}")
    assert hits == []


def test_comparison_docs_are_gone() -> None:
    present = [path.name for path in GONE_DOCS if path.exists()]
    assert present == []


def test_gitignore_keeps_local_data_private() -> None:
    text = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for needle in (
        ".pypi-venv/",
        ".release-venv/",
        ".*-venv/",
        "local/",
        "media/",
        "private/",
        ".env",
    ):
        assert needle in text


def test_sdist_lists_public_paths_only() -> None:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    only = data["tool"]["hatch"]["build"]["targets"]["sdist"]["only-include"]
    assert "src/failstep" in only
    assert "docs" in only
    for banned in (".pypi-venv", "local", "media", "private"):
        assert banned not in only
