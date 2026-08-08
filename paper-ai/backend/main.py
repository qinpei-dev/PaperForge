from __future__ import annotations

import os
import secrets
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any
from uuid import UUID, uuid4

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from services.document_classifier import classify_document
from services.agent_pipeline import run_agent_pipeline
from services.preview_service import build_docx_preview


BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
TEMPLATE_DIR = BASE_DIR / "templates"
OUTPUT_DIR = BASE_DIR / "outputs"
TASK_STATE_DIR = BASE_DIR / "task_states"

DEFAULT_MAX_UPLOAD_BYTES = 20 * 1024 * 1024
DEFAULT_RUNTIME_FILE_TTL_SECONDS = 60 * 60
UPLOAD_CHUNK_BYTES = 1024 * 1024

for directory in (UPLOAD_DIR, TEMPLATE_DIR, OUTPUT_DIR):
    directory.mkdir(exist_ok=True)

load_dotenv(BASE_DIR / ".env", override=True, encoding="utf-8-sig")

api_proxy_url = os.getenv("API_PROXY_URL") or os.getenv("DEEPSEEK_PROXY_URL")
if api_proxy_url:
    os.environ["HTTP_PROXY"] = api_proxy_url
    os.environ["HTTPS_PROXY"] = api_proxy_url

app = FastAPI(title="AI Paper Formatting Agent API")


@dataclass(frozen=True)
class StoredUpload:
    path: Path
    original_filename: str

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    cleanup_expired_runtime_files()
    return {"status": "ok"}


def require_backend_token(
    x_agent_token: Annotated[str | None, Header(alias="X-Agent-Token")] = None,
) -> None:
    expected = os.getenv("BACKEND_SHARED_SECRET", "").strip()
    running_on_render = os.getenv("RENDER", "").lower() == "true"
    if not expected:
        if running_on_render:
            raise HTTPException(status_code=503, detail="后端访问凭据未配置。")
        return
    if not x_agent_token or not secrets.compare_digest(x_agent_token, expected):
        raise HTTPException(status_code=401, detail="无权访问论文处理服务。")


protected_route = [Depends(require_backend_token)]


@app.post("/document/classify", dependencies=protected_route)
async def classify_uploaded_document(paper: UploadFile = File(...)) -> dict[str, object]:
    cleanup_expired_runtime_files()
    request_id = uuid4()
    try:
        upload = save_docx(paper, UPLOAD_DIR, request_id)
        result = classify_document(upload.path)
        result["filename"] = upload.original_filename
        return public_result(result)
    finally:
        remove_request_uploads(request_id)


@app.post("/agent/run", dependencies=protected_route)
async def run_agent(
    paper: UploadFile = File(...),
    template: UploadFile | None = File(None),
    allow_non_paper: bool = Form(False),
    mode: str = Form("ai"),
) -> dict[str, object]:
    cleanup_expired_runtime_files()
    request_id = uuid4()
    try:
        paper_upload = save_docx(paper, UPLOAD_DIR, request_id)
        template_upload = save_docx(template, UPLOAD_DIR, request_id) if template and template.filename else None
        result = run_agent_pipeline(
            paper_path=paper_upload.path,
            template_path=template_upload.path if template_upload else None,
            output_dir=OUTPUT_DIR,
            allow_non_paper=allow_non_paper,
            mode=mode,
            paper_display_name=paper_upload.original_filename,
            template_display_name=template_upload.original_filename if template_upload else None,
        )
        result.setdefault("original_filename", paper_upload.original_filename)
        result.setdefault(
            "original_template_filename",
            template_upload.original_filename if template_upload else None,
        )
        safe_result = public_result(result)
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=safe_result)
        return safe_result
    finally:
        remove_request_uploads(request_id)


@app.get("/download/{filename}", dependencies=protected_route)
def download_file(filename: str) -> FileResponse:
    cleanup_expired_runtime_files()
    target = OUTPUT_DIR / Path(filename).name
    if not target.exists():
        raise HTTPException(status_code=404, detail="没有找到生成后的 Word 文件。")
    return FileResponse(
        path=target,
        filename=target.name,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@app.get("/preview/{filename}", dependencies=protected_route)
def preview_file(filename: str) -> dict[str, str]:
    cleanup_expired_runtime_files()
    target = OUTPUT_DIR / Path(filename).name
    if not target.exists():
        raise HTTPException(status_code=404, detail="没有找到可预览的 Word 文件。")
    return build_docx_preview(target)


def save_docx(file: UploadFile, directory: Path, request_id: UUID) -> StoredUpload:
    original_filename = safe_upload_filename(file.filename)
    request_dir = directory / request_id.hex
    request_dir.mkdir(parents=True, exist_ok=True)

    target = request_dir / f"{uuid4().hex}.docx"
    written = 0
    try:
        with target.open("xb") as destination:
            while chunk := file.file.read(UPLOAD_CHUNK_BYTES):
                written += len(chunk)
                if written > max_upload_bytes():
                    raise HTTPException(
                        status_code=413,
                        detail=f"单个 DOCX 文件不能超过 {max_upload_bytes() // (1024 * 1024)} MB。",
                    )
                destination.write(chunk)
    except Exception:
        target.unlink(missing_ok=True)
        if request_dir.exists() and not any(request_dir.iterdir()):
            request_dir.rmdir()
        raise
    return StoredUpload(path=target, original_filename=original_filename)


def max_upload_bytes() -> int:
    return positive_int_env("MAX_UPLOAD_BYTES", DEFAULT_MAX_UPLOAD_BYTES)


def runtime_file_ttl_seconds() -> int:
    return positive_int_env("RUNTIME_FILE_TTL_SECONDS", DEFAULT_RUNTIME_FILE_TTL_SECONDS)


def positive_int_env(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError:
        return default
    return value if value > 0 else default


def remove_request_uploads(request_id: UUID) -> None:
    request_dir = UPLOAD_DIR / request_id.hex
    if request_dir.exists():
        shutil.rmtree(request_dir)


def cleanup_expired_runtime_files(now: float | None = None) -> None:
    cutoff = (time.time() if now is None else now) - runtime_file_ttl_seconds()
    for directory in (UPLOAD_DIR, OUTPUT_DIR, TASK_STATE_DIR):
        if not directory.exists():
            continue
        for path in directory.iterdir():
            if path.name == ".gitkeep":
                continue
            try:
                if path.stat().st_mtime >= cutoff:
                    continue
                if path.is_dir() and not path.is_symlink():
                    shutil.rmtree(path)
                else:
                    path.unlink(missing_ok=True)
            except FileNotFoundError:
                continue


def public_result(value: Any) -> Any:
    if os.getenv("RENDER", "").lower() != "true":
        return value
    if isinstance(value, dict):
        return {key: public_result(item) for key, item in value.items() if key != "task_state_path"}
    if isinstance(value, list):
        return [public_result(item) for item in value]
    if isinstance(value, str):
        return value.replace(str(BASE_DIR), "[runtime]").replace(BASE_DIR.as_posix(), "[runtime]")
    return value


def safe_upload_filename(filename: str | None) -> str:
    raw_filename = (filename or "").strip()
    if not raw_filename or "\x00" in raw_filename:
        raise HTTPException(status_code=400, detail="只支持 .docx 文件。")

    safe_name = Path(raw_filename.replace("\\", "/")).name
    if (
        not safe_name
        or any(ord(character) < 32 for character in safe_name)
        or Path(safe_name).suffix.lower() != ".docx"
    ):
        raise HTTPException(status_code=400, detail="只支持 .docx 文件。")
    return safe_name
