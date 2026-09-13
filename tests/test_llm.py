from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from typer.testing import CliRunner

from failstep.cli import app
from failstep.diagnose import diagnose
from failstep.llm import leftover_finding, load_llm_config, summarize
from failstep.models import Source
from failstep.parser import load_run
from failstep.redact import contains_secret

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "traces"
EXAMPLES = ROOT / "examples" / "traces"


class _Recorder(BaseHTTPRequestHandler):
    bodies: list[bytes] = []
    payload = {
        "id": "FS004",
        "confidence": 0.95,
        "title": "leftover",
        "recommendation": "Check the final answer against get_order.",
        "step_indexes": [3],
        "evidence": [
            {"key": "output", "value": "I cannot find the order."}
        ],
    }

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length)
        self.bodies.append(body)
        raw = json.dumps(self.payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, format: str, *args: object) -> None:
        del format, args


def _serve() -> tuple[ThreadingHTTPServer, str]:
    _Recorder.bodies = []
    server = ThreadingHTTPServer(("127.0.0.1", 0), _Recorder)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address[:2]
    return server, f"http://{host}:{port}"


def test_leftover_silent_without_url() -> None:
    run = load_run(FIXTURES / "leftover-secret.json")
    report = diagnose(run, "tests/traces/leftover-secret.json")
    assert report.root_cause is None
    assert leftover_finding(run, None) is None


def test_leftover_posts_redacted_summary() -> None:
    server, url = _serve()
    try:
        run = load_run(FIXTURES / "leftover-secret.json")
        finding = leftover_finding(run, load_llm_config(url=url))
        assert finding is not None
        assert finding.id == "FS000"
        assert finding.source is Source.llm
        assert finding.severity.value == "warning"
        assert finding.step_indexes == [3]
        assert finding.evidence[0].value == "I cannot find the order."
        assert len(_Recorder.bodies) == 1
        body = _Recorder.bodies[0].decode("utf-8")
        assert "sk-" not in body
        assert "Bearer" not in body
        assert "secret-token" not in body
        assert "sk-test-example" not in body
        assert "[redacted]" in body
        assert contains_secret(body) is False
        sent = json.loads(body)
        assert sent["task"] == "leftover"
        assert "steps" in sent["summary"]
        assert sent["summary"]["step_count"] == 3
    finally:
        server.shutdown()
        server.server_close()


def test_error_finding_skips_llm() -> None:
    server, url = _serve()
    try:
        run = load_run(EXAMPLES / "retry-loop.json")
        report = diagnose(
            run, "examples/traces/retry-loop.json", llm_url=url
        )
        assert report.root_cause is not None
        assert report.root_cause.id == "FS004"
        assert all(item.source.value != "llm" for item in report.findings)
        assert _Recorder.bodies == []
    finally:
        server.shutdown()
        server.server_close()


def test_no_llm_flag_skips_request() -> None:
    server, url = _serve()
    try:
        run = load_run(FIXTURES / "leftover-secret.json")
        report = diagnose(
            run,
            "tests/traces/leftover-secret.json",
            no_llm=True,
            llm_url=url,
        )
        assert report.root_cause is None
        assert _Recorder.bodies == []
    finally:
        server.shutdown()
        server.server_close()


def test_invented_step_is_dropped() -> None:
    server, url = _serve()
    _Recorder.payload = {
        "title": "leftover",
        "recommendation": "Invent a step.",
        "step_indexes": [99],
        "evidence": [{"key": "output", "value": "not in the file"}],
    }
    try:
        run = load_run(FIXTURES / "leftover-secret.json")
        assert leftover_finding(run, load_llm_config(url=url)) is None
    finally:
        _Recorder.payload = {
            "id": "FS004",
            "confidence": 0.95,
            "title": "leftover",
            "recommendation": "Check the final answer against get_order.",
            "step_indexes": [3],
            "evidence": [
                {"key": "output", "value": "I cannot find the order."}
            ],
        }
        server.shutdown()
        server.server_close()


def test_cli_leftover_and_no_llm(runner: CliRunner, monkeypatch) -> None:
    monkeypatch.chdir(ROOT)
    server, url = _serve()
    monkeypatch.setenv("FAILSTEP_LLM_URL", url)
    try:
        hit = runner.invoke(
            app, ["diagnose", "tests/traces/leftover-secret.json"]
        )
        assert hit.exit_code == 0
        assert "FS000" in hit.stdout
        assert "leftover" in hit.stdout
        assert "confidence" not in hit.stdout
        assert "sk-test-example" not in hit.stdout
        js = runner.invoke(
            app,
            [
                "diagnose",
                "tests/traces/leftover-secret.json",
                "--format",
                "json",
            ],
        )
        payload = json.loads(js.stdout)
        assert payload["root_cause"]["id"] == "FS000"
        assert payload["root_cause"]["source"] == "llm"
        assert "confidence" not in js.stdout
        skipped = runner.invoke(
            app,
            ["diagnose", "tests/traces/leftover-secret.json", "--no-llm"],
        )
        assert skipped.exit_code == 0
        assert "FS000" not in skipped.stdout
        warn = runner.invoke(
            app,
            [
                "diagnose",
                "tests/traces/leftover-secret.json",
                "--fail-on",
                "warning",
            ],
        )
        assert warn.exit_code == 1
        blocked = runner.invoke(
            app, ["diagnose", "examples/traces/retry-loop.json"]
        )
        assert blocked.exit_code == 1
        assert "FS004" in blocked.stdout
        assert "FS000" not in blocked.stdout
    finally:
        server.shutdown()
        server.server_close()


def test_no_redact_still_redacts_and_warns(
    runner: CliRunner, monkeypatch
) -> None:
    monkeypatch.chdir(ROOT)
    server, url = _serve()
    monkeypatch.setenv("FAILSTEP_LLM_URL", url)
    try:
        result = runner.invoke(
            app,
            ["diagnose", "tests/traces/leftover-secret.json", "--no-redact"],
        )
        assert result.exit_code == 0
        assert "still redacted" in result.stderr
        body = _Recorder.bodies[-1].decode("utf-8")
        assert "sk-" not in body
        assert "Bearer" not in body
    finally:
        server.shutdown()
        server.server_close()


def test_summarize_does_not_keep_secrets() -> None:
    run = load_run(FIXTURES / "leftover-secret.json")
    blob = json.dumps(summarize(run))
    assert "sk-" not in blob
    assert "Bearer" not in blob
    assert "sk-test-example" not in blob
