from __future__ import annotations

import os
import shutil
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID, uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from services.document_classifier import classify_document
from services.agent_pipeline import run_agent_pipeline
from services.preview_service import build_docx_preview
from services.content_review import apply_content_suggestion
from services.review_evidence import aggregate_review_evidence, content_score_summary


BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
TEMPLATE_DIR = BASE_DIR / "templates"
OUTPUT_DIR = BASE_DIR / "outputs"

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
    return {"status": "ok"}


@app.post("/document/classify")
async def classify_uploaded_document(paper: UploadFile = File(...)) -> dict[str, object]:
    upload = save_docx(paper, UPLOAD_DIR, uuid4())
    result = classify_document(upload.path)
    result["filename"] = upload.original_filename
    return result


@app.post("/agent/run")
async def run_agent(
    paper: UploadFile = File(...),
    template: UploadFile | None = File(None),
    allow_non_paper: bool = Form(False),
    mode: str = Form("ai"),
) -> dict[str, object]:
    request_id = uuid4()
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
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result)
    return result


@app.get("/download/{filename}")
def download_file(filename: str) -> FileResponse:
    target = OUTPUT_DIR / Path(filename).name
    if not target.exists():
        raise HTTPException(status_code=404, detail="没有找到生成后的 Word 文件。")
    return FileResponse(
        path=target,
        filename=target.name,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@app.post("/agent/apply-suggestion")
async def apply_suggestion(
    filename: str = Form(...),
    issue_id: str = Form(...),
    paragraph_index: int = Form(...),
    original: str = Form(...),
    suggested: str = Form(...),
    issue_type: str = Form("content"),
    reason: str = Form("用户确认采纳该建议"),
    confidence: float = Form(0.85),
) -> dict[str, object]:
    source = OUTPUT_DIR / Path(filename).name
    if not source.exists():
        raise HTTPException(status_code=404, detail="没有找到可确认修改的 DOCX。")
    output = OUTPUT_DIR / f"{source.stem}_confirmed_{datetime.now().strftime('%Y%m%d%H%M%S%f')}.docx"
    result = apply_content_suggestion(source, output, {"issue_id": issue_id, "paragraph_index": paragraph_index, "original_text": original, "suggested_text": suggested, "issue_type": issue_type, "reason": reason, "confidence": confidence})
    if result.get("status") == "conflict":
        raise HTTPException(status_code=409, detail=result)
    if result.get("status") != "ok":
        raise HTTPException(status_code=422, detail=result)
    accepted_review = {"issues": [{"issue_id": issue_id, "paragraph_index": paragraph_index, "issue_type": issue_type, "original_text": original, "suggested_text": suggested, "reason": reason, "confidence": confidence, "action_policy": "SUGGEST_ONLY", "source": "user_confirmed", "status": "accepted"}], "provenance": {"auto_fixes": [], "suggestions": [], "accepted": [result["change"]], "hitl": []}}
    evidence = aggregate_review_evidence(content_review=accepted_review)
    result["review_summary"] = evidence["review_summary"]
    result["change_evidence"] = evidence["change_evidence"]
    result["pending_actions"] = evidence["pending_actions"]
    result["content_score"] = content_score_summary(accepted_review)
    return result


@app.get("/preview/{filename}")
def preview_file(filename: str) -> dict[str, str]:
    target = OUTPUT_DIR / Path(filename).name
    if not target.exists():
        raise HTTPException(status_code=404, detail="没有找到可预览的 Word 文件。")
    return build_docx_preview(target)


def save_docx(file: UploadFile, directory: Path, request_id: UUID) -> StoredUpload:
    original_filename = safe_upload_filename(file.filename)
    request_dir = directory / request_id.hex
    request_dir.mkdir(parents=True, exist_ok=True)

    target = request_dir / f"{uuid4().hex}.docx"
    with target.open("xb") as destination:
        shutil.copyfileobj(file.file, destination)
    return StoredUpload(path=target, original_filename=original_filename)


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
