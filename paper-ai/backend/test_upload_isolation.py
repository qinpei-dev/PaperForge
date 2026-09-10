from __future__ import annotations

import hashlib
import io
import re
import shutil
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from fastapi.testclient import TestClient

import main as api_main


DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
UUID_DOCX_PATTERN = re.compile(r"[0-9a-f]{32}\.docx")


def make_upload(filename: str, content: bytes) -> UploadFile:
    return UploadFile(filename=filename, file=io.BytesIO(content))


def valid_docx_bytes(content: bytes = b"") -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("word/document.xml", "<w:document/>")
        archive.writestr("customXml/item.xml", content)
    return buffer.getvalue()


def assert_ok(name: str, condition: bool, detail: object = "") -> None:
    if not condition:
        raise AssertionError(f"{name} FAIL {detail}")
    suffix = f" {detail}" if detail else ""
    print(f"{name} PASS{suffix}")


def file_hashes(directory: Path) -> dict[str, str]:
    return {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in directory.glob("*.docx")
        if path.is_file()
    }


def test_route_request_isolation(monkeypatch) -> None:
    captured: list[tuple[Path, Path | None]] = []
    original_pipeline = api_main.run_agent_pipeline
    existing_request_dirs = {path for path in api_main.UPLOAD_DIR.iterdir() if path.is_dir()}

    def fake_pipeline(*, paper_path: Path, template_path: Path | None, **_: object) -> dict[str, object]:
        captured.append((paper_path, template_path))
        return {
            "status": "ok",
            "filename": "result.docx",
            "download_url": "/download/result.docx",
        }

    api_main.run_agent_pipeline = fake_pipeline
    monkeypatch.setattr(api_main, "bootstrap_template_registry", lambda db: 0)
    try:
        client = TestClient(api_main.app)
        for _ in range(2):
            response = client.post(
                "/agent/run",
                data={"mode": "local"},
                files={
                    "paper": ("same-name.docx", valid_docx_bytes(b"paper"), DOCX_MIME),
                    "template": ("same-name.docx", valid_docx_bytes(b"template"), DOCX_MIME),
                },
            )
            payload = response.json()
            assert_ok("route_upload_status", response.status_code == 200, response.status_code)
            assert_ok("route_original_paper_name", payload.get("original_filename") == "same-name.docx", payload)
            assert_ok(
                "route_original_template_name",
                payload.get("original_template_filename") == "same-name.docx",
                payload,
            )

        first_paper, first_template = captured[0]
        second_paper, second_template = captured[1]
        assert_ok("sequential_request_directories_unique", first_paper.parent != second_paper.parent)
        assert_ok("paper_template_share_request_directory", first_paper.parent == first_template.parent)
        assert_ok("uploaded_template_outside_builtin_directory", api_main.TEMPLATE_DIR not in first_template.parents)
        assert_ok("internal_paper_name_is_uuid", bool(UUID_DOCX_PATTERN.fullmatch(first_paper.name)), first_paper.name)
        assert_ok("internal_template_name_is_uuid", bool(UUID_DOCX_PATTERN.fullmatch(first_template.name)), first_template.name)
        assert_ok("same_original_names_do_not_collide", first_paper != first_template)
    finally:
        api_main.run_agent_pipeline = original_pipeline
        for path in api_main.UPLOAD_DIR.iterdir():
            if path.is_dir() and path not in existing_request_dirs:
                shutil.rmtree(path)


def test_concurrent_same_name_uploads() -> None:
    request_id = uuid4()
    request_dir = api_main.UPLOAD_DIR / request_id.hex

    def store(index: int) -> api_main.StoredUpload:
        return api_main.save_docx(
                make_upload("concurrent.docx", valid_docx_bytes(f"content-{index}".encode())),
            api_main.UPLOAD_DIR,
            request_id,
        )

    try:
        with ThreadPoolExecutor(max_workers=8) as executor:
            stored = list(executor.map(store, range(8)))
        paths = [item.path for item in stored]
        assert_ok("concurrent_internal_names_unique", len(set(paths)) == 8, paths)
        assert_ok("concurrent_files_all_exist", all(path.exists() for path in paths))
        assert_ok(
            "concurrent_contents_preserved",
            {path.read_bytes() for path in paths} == {valid_docx_bytes(f"content-{index}".encode()) for index in range(8)},
        )
    finally:
        if request_dir.exists():
            shutil.rmtree(request_dir)


def test_extension_and_path_safety() -> None:
    request_id = uuid4()
    request_dir = api_main.UPLOAD_DIR / request_id.hex
    try:
        for filename in ("paper.pdf", "paper.docx.exe", "paper"):
            try:
                api_main.save_docx(make_upload(filename, b"invalid"), api_main.UPLOAD_DIR, request_id)
            except HTTPException as exc:
                assert_ok(f"invalid_extension_{filename}", exc.status_code == 400, exc.status_code)
            else:
                raise AssertionError(f"invalid_extension_{filename} FAIL")

        stored = api_main.save_docx(
            make_upload("../../..\\templates\\template.DOCX", valid_docx_bytes(b"safe")),
            api_main.UPLOAD_DIR,
            request_id,
        )
        assert_ok("path_filename_sanitized", stored.original_filename == "template.DOCX", stored.original_filename)
        assert_ok("path_upload_stays_in_request_directory", stored.path.parent == request_dir, stored.path)
        assert_ok("uppercase_docx_allowed", stored.path.suffix == ".docx", stored.path.name)
    finally:
        if request_dir.exists():
            shutil.rmtree(request_dir)


def main() -> None:
    builtin_before = file_hashes(api_main.TEMPLATE_DIR)
    test_route_request_isolation()
    test_concurrent_same_name_uploads()
    test_extension_and_path_safety()
    builtin_after = file_hashes(api_main.TEMPLATE_DIR)
    assert_ok("builtin_templates_unchanged", builtin_after == builtin_before, builtin_after)
    print("UPLOAD_ISOLATION PASS")


if __name__ == "__main__":
    main()
