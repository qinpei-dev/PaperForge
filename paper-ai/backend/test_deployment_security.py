from __future__ import annotations

import io
import os
import shutil
import time
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from fastapi.testclient import TestClient

import main as api_main


DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def assert_ok(name: str, condition: bool, detail: object = "") -> None:
    if not condition:
        raise AssertionError(f"{name} FAIL {detail}")
    suffix = f" {detail}" if detail else ""
    print(f"{name} PASS{suffix}")


def make_upload(content: bytes) -> UploadFile:
    return UploadFile(filename="paper.docx", file=io.BytesIO(content))


def test_render_authentication() -> None:
    original_render = os.environ.get("RENDER")
    original_secret = os.environ.get("BACKEND_SHARED_SECRET")
    client = TestClient(api_main.app)
    try:
        os.environ["RENDER"] = "true"
        os.environ.pop("BACKEND_SHARED_SECRET", None)
        response = client.post("/document/classify", files={"paper": ("paper.docx", b"x", DOCX_MIME)})
        assert_ok("render_missing_secret_fails_closed", response.status_code == 503, response.status_code)

        os.environ["BACKEND_SHARED_SECRET"] = "test-shared-secret"
        response = client.post("/document/classify", files={"paper": ("paper.docx", b"x", DOCX_MIME)})
        assert_ok("missing_header_rejected", response.status_code == 401, response.status_code)
        response = client.post(
            "/document/classify",
            headers={"X-Agent-Token": "wrong"},
            files={"paper": ("paper.docx", b"x", DOCX_MIME)},
        )
        assert_ok("wrong_header_rejected", response.status_code == 401, response.status_code)
    finally:
        restore_env("RENDER", original_render)
        restore_env("BACKEND_SHARED_SECRET", original_secret)


def test_upload_limit_and_cleanup() -> None:
    original_limit = os.environ.get("MAX_UPLOAD_BYTES")
    request_id = uuid4()
    request_dir = api_main.UPLOAD_DIR / request_id.hex
    try:
        os.environ["MAX_UPLOAD_BYTES"] = "4"
        try:
            api_main.save_docx(make_upload(b"12345"), api_main.UPLOAD_DIR, request_id)
        except HTTPException as exc:
            assert_ok("oversized_upload_rejected", exc.status_code == 413, exc.status_code)
        else:
            raise AssertionError("oversized_upload_rejected FAIL")
        assert_ok("partial_upload_removed", not request_dir.exists(), request_dir)
    finally:
        restore_env("MAX_UPLOAD_BYTES", original_limit)
        if request_dir.exists():
            shutil.rmtree(request_dir)


def test_expired_runtime_cleanup() -> None:
    original_ttl = os.environ.get("RUNTIME_FILE_TTL_SECONDS")
    old_output = api_main.OUTPUT_DIR / "expired-test.docx"
    fresh_output = api_main.OUTPUT_DIR / "fresh-test.docx"
    try:
        os.environ["RUNTIME_FILE_TTL_SECONDS"] = "60"
        old_output.write_bytes(b"old")
        fresh_output.write_bytes(b"fresh")
        now = time.time()
        os.utime(old_output, (now - 120, now - 120))
        api_main.cleanup_expired_runtime_files(now=now)
        assert_ok("expired_output_removed", not old_output.exists())
        assert_ok("fresh_output_preserved", fresh_output.exists())
    finally:
        restore_env("RUNTIME_FILE_TTL_SECONDS", original_ttl)
        old_output.unlink(missing_ok=True)
        fresh_output.unlink(missing_ok=True)


def test_public_result_removes_runtime_paths() -> None:
    original_render = os.environ.get("RENDER")
    try:
        os.environ["RENDER"] = "true"
        result = api_main.public_result(
            {
                "task_state_path": str(api_main.TASK_STATE_DIR / "secret.json"),
                "message": f"failed at {api_main.BASE_DIR / 'uploads' / 'private.docx'}",
                "nested": [{"status": "ok"}],
            }
        )
        assert_ok("task_state_path_removed", "task_state_path" not in result, result)
        assert_ok("base_directory_redacted", str(api_main.BASE_DIR) not in result["message"], result)
        assert_ok("nested_result_preserved", result["nested"] == [{"status": "ok"}], result)
    finally:
        restore_env("RENDER", original_render)


def restore_env(name: str, value: str | None) -> None:
    if value is None:
        os.environ.pop(name, None)
    else:
        os.environ[name] = value


def main() -> None:
    test_render_authentication()
    test_upload_limit_and_cleanup()
    test_expired_runtime_cleanup()
    test_public_result_removes_runtime_paths()
    print("DEPLOYMENT_SECURITY PASS")


if __name__ == "__main__":
    main()
