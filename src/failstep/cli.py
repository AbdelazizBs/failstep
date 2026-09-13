from __future__ import annotations

import sys
from enum import StrEnum
from pathlib import Path

import typer

from failstep import __version__
from failstep.diagnose import diagnose as diagnose_run
from failstep.errors import ParseError
from failstep.models import Report, Severity
from failstep.parser import load_run
from failstep.report import (
    format_diagnose_json,
    format_diagnose_markdown,
    format_diagnose_terminal,
    format_error_json,
    format_error_terminal,
    format_inspect_json,
    format_inspect_markdown,
    format_inspect_terminal,
    format_internal_json,
    format_internal_terminal,
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


class FailOn(StrEnum):
    error = "error"
    warning = "warning"


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


def _emit_internal(output_format: OutputFormat) -> None:
    if output_format is OutputFormat.json:
        sys.stdout.write(format_internal_json(__version__))
    else:
        sys.stdout.write(format_internal_terminal())
    raise typer.Exit(3)


def _load(path: Path, output_format: OutputFormat):
    try:
        return load_run(path)
    except ParseError as error:
        _emit_error(error, output_format)
    except OSError as exc:
        _emit_error(ParseError(str(exc), _display_path(path)), output_format)
    raise RuntimeError("unreachable")


def _write_diagnose(report: Report, output_format: OutputFormat) -> None:
    if output_format is OutputFormat.json:
        sys.stdout.write(format_diagnose_json(report, __version__))
    elif output_format is OutputFormat.markdown:
        sys.stdout.write(format_diagnose_markdown(report, __version__))
    else:
        sys.stdout.write(format_diagnose_terminal(report, __version__))


def _exit_for(report: Report, fail_on: FailOn) -> int:
    if not report.findings:
        return 0
    if fail_on is FailOn.warning:
        return 1
    if any(item.severity is Severity.error for item in report.findings):
        return 1
    return 0


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
    fail_on: FailOn = typer.Option(
        FailOn.error,
        "--fail-on",
        help="Exit 1 on this severity or higher.",
    ),
    no_llm: bool = typer.Option(
        False,
        "--no-llm",
        help="Skip LLM leftover (default path never calls a model).",
    ),
    no_redact: bool = typer.Option(
        False,
        "--no-redact",
        help="Warn; secrets are still redacted before leftover requests.",
    ),
) -> None:
    """Print a root cause from deterministic detectors."""
    if no_redact:
        sys.stderr.write(
            "Secrets are still redacted before any leftover request.\n"
        )
    run = _load(trace, output_format)
    try:
        report = diagnose_run(
            run, _display_path(trace), no_llm=no_llm
        )
    except Exception:
        _emit_internal(output_format)
    _write_diagnose(report, output_format)
    code = _exit_for(report, fail_on)
    if code:
        raise typer.Exit(code)


@app.command()
def version() -> None:
    """Print the tool version."""
    sys.stdout.write(f"failstep {__version__}\n")
