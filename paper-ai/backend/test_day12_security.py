from __future__ import annotations

import io
import zipfile

import pytest
from fastapi import HTTPException, UploadFile

import auth
from main import MAX_UPLOAD_BYTES, safe_upload_filename, validate_docx_upload


def valid_docx(payload: bytes = b"") -> bytes:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("word/document.xml", "<w:document/>")
        archive.writestr("customXml/item.xml", payload)
    return stream.getvalue()


def upload(filename: str, payload: bytes, content_type: str | None = "application/vnd.openxmlformats-officedocument.wordprocessingml.document") -> UploadFile:
    headers = {"content-type": content_type} if content_type else None
    return UploadFile(filename=filename, file=io.BytesIO(payload), headers=headers)


def test_upload_rejects_non_docx_mime_and_invalid_zip() -> None:
    with pytest.raises(HTTPException) as mime_error:
        validate_docx_upload(upload("paper.docx", valid_docx(), "application/pdf"), maximum_size=MAX_UPLOAD_BYTES, label="论文")
    assert mime_error.value.status_code == 415
    with pytest.raises(HTTPException) as zip_error:
        validate_docx_upload(upload("paper.docx", b"not-a-zip"), maximum_size=MAX_UPLOAD_BYTES, label="论文")
    assert zip_error.value.status_code == 422


def test_upload_size_and_path_safety_are_enforced() -> None:
    with pytest.raises(HTTPException) as size_error:
        validate_docx_upload(upload("paper.docx", valid_docx(b"x" * 32)), maximum_size=10, label="论文")
    assert size_error.value.status_code == 413
    assert safe_upload_filename("../../tenant-b/essay.docx") == "essay.docx"


def test_production_jwt_secret_cannot_use_missing_or_placeholder_value(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError, match="JWT_SECRET_KEY"):
        auth._jwt_secret()
    monkeypatch.setenv("JWT_SECRET_KEY", "replace-with-a-long-random-secret")
    with pytest.raises(RuntimeError, match="non-placeholder"):
        auth._jwt_secret()
    monkeypatch.setenv("JWT_SECRET_KEY", "a" * 32)
    assert auth._jwt_secret() == "a" * 32
