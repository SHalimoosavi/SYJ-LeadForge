"""Live smoke test for the SYJ LeadForge REST API.

Starts a real `uvicorn` server as a subprocess, hits it with real HTTP
requests end-to-end (import -> score -> list -> export -> error cases),
and asserts on the responses. Written in pure Python (no bash `&`
backgrounding, no `curl`) so it runs identically on Linux, macOS, and
Windows CI runners.

Usage:
    python scripts/api_smoke_test.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

HOST = "127.0.0.1"
PORT = "8199"
BASE_URL = f"http://{HOST}:{PORT}"
REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_CSV = REPO_ROOT / "sample_data" / "businesses_sample.csv"


def _wait_for_server(timeout: float = 20.0) -> None:
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(f"{BASE_URL}/health", timeout=1) as resp:
                if resp.status == 200:
                    return
        except (urllib.error.URLError, ConnectionError) as exc:
            last_error = exc
            time.sleep(0.3)
    raise RuntimeError(f"Server did not start in time: {last_error}")


def _get(path: str) -> tuple[int, object]:
    try:
        with urllib.request.urlopen(f"{BASE_URL}{path}", timeout=10) as resp:
            body = resp.read()
            content_type = resp.headers.get("content-type", "")
            data = json.loads(body) if "json" in content_type else body
            return resp.status, data
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read())


def _post(path: str, payload: dict | None = None) -> tuple[int, object]:
    data = json.dumps(payload).encode() if payload is not None else b""
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read())


def _post_multipart_csv(path: str, csv_path: Path) -> tuple[int, object]:
    boundary = uuid.uuid4().hex
    csv_bytes = csv_path.read_bytes()
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{csv_path.name}"\r\n'
        f"Content-Type: text/csv\r\n\r\n"
    ).encode() + csv_bytes + f"\r\n--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read())


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp_home:
        env = os.environ.copy()
        env["LEADFORGE_HOME"] = tmp_home
        env["LEADFORGE_DELAY"] = "0"

        proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", HOST, "--port", PORT],
            cwd=REPO_ROOT,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        try:
            _wait_for_server()
            print("Server is up.")

            status, body = _get("/health")
            assert status == 200 and body["status"] == "ok", f"health check failed: {status} {body}"
            print("  /health OK")

            status, body = _post_multipart_csv("/businesses/import", SAMPLE_CSV)
            assert status == 200 and body["imported"] == 6, f"import failed: {status} {body}"
            print(f"  /businesses/import OK ({body['imported']} imported)")

            status, body = _get("/businesses")
            assert status == 200 and len(body) == 6, f"list businesses failed: {status}"
            print("  /businesses OK")

            status, body = _post("/scores/run")
            assert status == 200 and body["scored"] == 6, f"scores/run failed: {status} {body}"
            print(f"  /scores/run OK ({body['scored']} scored)")

            status, body = _get("/leads")
            assert status == 200 and len(body) == 6
            scores = [lead["score"]["opportunity_score"] for lead in body if lead["score"]]
            assert scores == sorted(scores, reverse=True), "leads not sorted by score descending"
            print("  /leads OK (sorted correctly)")

            status, body = _get("/stats")
            assert status == 200 and body["total_businesses"] == 6, f"stats failed: {status} {body}"
            print(f"  /stats OK (average_score={body['average_score']})")

            status, body = _get("/leads/export/csv")
            assert status == 200 and b"opportunity_score" in body, "csv export failed"
            print("  /leads/export/csv OK")

            status, _ = _post("/businesses/1/audit")
            assert status == 400, f"expected 400 for no-website audit, got {status}"
            print("  /businesses/1/audit correctly rejects no-website business (400)")

            status, _ = _get("/businesses/99999")
            assert status == 404, f"expected 404 for missing business, got {status}"
            print("  /businesses/99999 correctly 404s")

            print("\nAll live API smoke tests passed.")
            return 0
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
            if proc.stdout:
                output = proc.stdout.read()
                if output:
                    print("\n--- server log ---")
                    print(output)


if __name__ == "__main__":
    raise SystemExit(main())
