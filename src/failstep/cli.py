from __future__ import annotations

import sys
from enum import StrEnum
from pathlib import Path

import typer

from failstep import __version__
from failstep.errors import ParseError
from failstep.parser import load_run
from failstep.report import (
    format_error_json,
    format_error_terminal,
    format_inspect_json,
    format_inspect_markdown,
    format_inspect_terminal,
    format_phase1_diagnose,
)

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    pretty_exceptions_enable=False,
    pretty_exceptions_show_locals=False,
    help="Lint one finished AI agent run from a file.",
)


class OutputFormat(StrEnum):
    terminal = "terminal"
    json = "json"
    markdown = "markdown"


def _display_path(path: Path) -> str:
    try:
        relative = path.resolve().relative_to(Path.cwd().resolve())
        return relative.as_posix()
    except ValueError:
        return path.as_posix()


def _emit_error(error: ParseError, output_format: OutputFormat) -> None:
    if output_format is OutputFormat.json:
        sys.stdout.write(format_error_json(error, __version__))
    else:
        sys.stdout.write(format_error_terminal(error))
    raise typer.Exit(2)


def _load(path: Path, output_format: OutputFormat):
    try:
        return load_run(path)
    except ParseError as error:
        _emit_error(error, output_format)
    except OSError as exc:
        _emit_error(ParseError(str(exc), _display_path(path)), output_format)
    raise RuntimeError("unreachable")


@app.command()
def inspect(
    trace: Path = typer.Argument(..., help="Path to a native JSON or JSONL trace."),
    output_format: OutputFormat = typer.Option(
        OutputFormat.terminal,
        "--format",
        help="terminal, json, or markdown.",
    ),
) -> None:
    """Print the run. No verdict."""
    run = _load(trace, output_format)
    display = _display_path(trace)
    if output_format is OutputFormat.json:
        sys.stdout.write(format_inspect_json(run, display, __version__))
    elif output_format is OutputFormat.markdown:
        sys.stdout.write(format_inspect_markdown(run, display, __version__))
    else:
        sys.stdout.write(format_inspect_terminal(run, display, __version__))


@app.command()
def diagnose(
    trace: Path = typer.Argument(..., help="Path to a native JSON or JSONL trace."),
    output_format: OutputFormat = typer.Option(
        OutputFormat.terminal,
        "--format",
        help="terminal, json, or markdown.",
    ),
    fail_on: str | None = typer.Option(
        None,
        "--fail-on",
        help="Phase 2. Ignored until detectors ship.",
        hidden=True,
    ),
) -> None:
    """Print a root cause. Detectors ship in Phase 2."""
    del fail_on
    _load(trace, output_format)
    sys.stdout.write(
        format_phase1_diagnose(_display_path(trace), __version__, output_format.value)
    )


@app.command()
def version() -> None:
    """Print the tool version."""
    sys.stdout.write(f"failstep {__version__}\n")
