from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples" / "traces"
FIXTURES = Path(__file__).resolve().parent / "traces"


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def repo_root() -> Path:
    return ROOT
