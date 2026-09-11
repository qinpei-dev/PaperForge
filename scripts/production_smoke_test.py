"""Minimal black-box production smoke test for a deployed PaperForge instance."""

from __future__ import annotations

import argparse
import json
import secrets
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def request(url: str, *, method: str = "GET", body: bytes | None = None, headers: dict[str, str] | None = None, timeout: int = 900) -> tuple[int, bytes]:
    request_obj = urllib.request.Request(url, data=body, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(request_obj, timeout=timeout) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {url} returned HTTP {exc.code}: {detail[:500]}") from exc


def json_request(base: str, path: str, *, method: str = "GET", payload: object | None = None, headers: dict[str, str] | None = None) -> dict[str, object]:
    request_headers = {"Accept": "application/json", **(headers or {})}
    body = None
    if payload is not None:
        request_headers["Content-Type"] = "application/json"
        body = json.dumps(payload).encode("utf-8")
    status, raw = request(base + path, method=method, body=body, headers=request_headers)
    if status < 200 or status >= 300:
        raise RuntimeError(f"{method} {path} returned HTTP {status}")
    value = json.loads(raw.decode("utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{path} did not return a JSON object")
    return value


def multipart(fields: dict[str, str], files: dict[str, tuple[str, bytes, str]]) -> tuple[bytes, str]:
    boundary = "----PaperForgeSmoke" + secrets.token_hex(8)
    chunks: list[bytes] = []
    for name, value in fields.items():
        chunks.extend([f"--{boundary}\r\n".encode(), f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(), value.encode(), b"\r\n"])
    for name, (filename, content, content_type) in files.items():
        chunks.extend([f"--{boundary}\r\n".encode(), f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'.encode(), f"Content-Type: {content_type}\r\n\r\n".encode(), content, b"\r\n"])
    chunks.append(f"--{boundary}--\r\n".encode())
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True, help="Public backend URL, for example https://api.example.com")
    parser.add_argument("--email", required=True, help="Existing smoke-test user email")
    parser.add_argument("--password", required=True, help="Smoke-test user password")
    parser.add_argument("--paper", required=True, type=Path, help="DOCX fixture path")
    parser.add_argument("--template", type=Path, help="Optional DOCX template fixture path")
    args = parser.parse_args()
    base = args.base_url.rstrip("/")
    if not args.paper.is_file() or args.paper.suffix.lower() != ".docx":
        raise RuntimeError("--paper must point to an existing DOCX file")
    if args.template and (not args.template.is_file() or args.template.suffix.lower() != ".docx"):
        raise RuntimeError("--template must point to an existing DOCX file")

    status, _ = request(base + "/health", timeout=10)
    assert status == 200
    ready = json_request(base, "/ready")
    assert ready.get("status") == "ready", ready
    login = json_request(base, "/auth/login", method="POST", payload={"email": args.email, "password": args.password})
    token = str(login.get("access_token") or "")
    if not token:
        raise RuntimeError("login did not return access_token")
    headers = {"Authorization": f"Bearer {token}"}
    paper = (args.paper.name, args.paper.read_bytes(), DOCX_MIME)
    files = {"paper": paper}
    if args.template:
        files["template"] = (args.template.name, args.template.read_bytes(), DOCX_MIME)
    body, content_type = multipart({"mode": "local", "allow_non_paper": "true"}, files)
    status, raw = request(base + "/document/classify", method="POST", body=body, headers={**headers, "Content-Type": content_type})
    if status != 200:
        raise RuntimeError(f"classify returned HTTP {status}")
    classify = json.loads(raw.decode("utf-8"))
    if not classify.get("document_type"):
        raise RuntimeError("classify did not return document_type")

    body, content_type = multipart({"mode": "local", "allow_non_paper": "true"}, files)
    status, raw = request(base + "/tasks", method="POST", body=body, headers={**headers, "Content-Type": content_type})
    if status != 201:
        raise RuntimeError(f"tasks returned HTTP {status}")
    created = json.loads(raw.decode("utf-8"))
    task_id = str(created.get("task_id") or "")
    if not task_id:
        raise RuntimeError("tasks did not return task_id")
    deadline = time.monotonic() + 900
    task: dict[str, object] = {}
    while time.monotonic() < deadline:
        task = json_request(base, f"/tasks/{task_id}", headers=headers)
        if task.get("status") in {"completed", "failed", "interrupted"}:
            break
        time.sleep(1)
    if task.get("status") != "completed":
        raise RuntimeError(f"task detail smoke assertion failed: {task.get('status')}")
    breakdown = task.get("score_breakdown") or {}
    if not isinstance(breakdown, dict) or breakdown.get("ai_score") is not None or breakdown.get("ai_used") is not False:
        raise RuntimeError(f"local smoke assertions failed: {breakdown}")
    event_status, event_raw = request(base + f"/tasks/{task_id}/events", headers={**headers, "Accept": "text/event-stream"}, timeout=30)
    if event_status != 200 or b"task_completed" not in event_raw:
        raise RuntimeError("task event smoke assertion failed")
    artifacts = task.get("artifacts") or []
    docx_artifact = next((item for item in artifacts if isinstance(item, dict) and item.get("file_type") == "docx"), None)
    if not docx_artifact or not docx_artifact.get("file_path"):
        raise RuntimeError("task artifact smoke assertion failed")
    filename = Path(str(docx_artifact["file_path"])).name
    preview_status, preview_raw = request(base + f"/preview/{filename}", headers={**headers, "Accept": "application/json"})
    if preview_status != 200 or not json.loads(preview_raw.decode("utf-8")).get("html"):
        raise RuntimeError("preview smoke assertion failed")
    download_status, download_raw = request(base + f"/download/{filename}", headers=headers)
    if download_status != 200 or not download_raw:
        raise RuntimeError("download smoke assertion failed")
    if not docx_artifact or not docx_artifact.get("id"):
        raise RuntimeError("task artifact smoke assertion failed")
    artifact_status, artifact_raw = request(base + f"/artifacts/{docx_artifact['id']}/download", headers=headers)
    if artifact_status != 200 or not artifact_raw:
        raise RuntimeError("artifact download smoke assertion failed")
    usage = json_request(base, "/usage", headers=headers)
    if "remaining" not in usage:
        raise RuntimeError("usage smoke assertion failed")
    print("PRODUCTION SMOKE PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, RuntimeError, OSError, json.JSONDecodeError) as exc:
        print(f"PRODUCTION SMOKE FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
