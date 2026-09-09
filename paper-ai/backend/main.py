from __future__ import annotations

import os
import json
import shutil
import logging
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID, uuid4

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse

from services.document_classifier import classify_document
from services.agent_pipeline import run_agent_pipeline
from services.preview_service import build_docx_preview
from services.storage import LocalStorage
from services.content_review import apply_content_suggestion
from services.review_evidence import aggregate_review_evidence, content_score_summary
from auth import auth_is_required, create_access_token, get_current_user, get_optional_current_user, hash_password, validate_email, verify_password
from db.models import Artifact, Project, Task, User, Workspace
from db.session import SessionLocal, get_db, init_db
from schemas.auth import AuthResponse, LoginRequest, RegisterRequest, UserResponse
from services.task_worker import task_worker
from services.task_events import has_events, publish_event, subscribe_event
from services.template_registry import (
    TEMPLATE_STATUSES,
    ResolvedTemplate,
    TemplateRegistryError,
    resolve_template_request,
    template_registry,
)
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker


BASE_DIR = Path(__file__).resolve().parent
STORAGE = LocalStorage(BASE_DIR)
UPLOAD_DIR = STORAGE.path_for("uploads")
TEMPLATE_DIR = BASE_DIR / "templates"
OUTPUT_DIR = STORAGE.path_for("outputs")
LOGGER = logging.getLogger(__name__)

for directory in (UPLOAD_DIR, TEMPLATE_DIR, OUTPUT_DIR):
    directory.mkdir(exist_ok=True)

load_dotenv(BASE_DIR / ".env", override=True, encoding="utf-8-sig")

api_proxy_url = os.getenv("API_PROXY_URL") or os.getenv("DEEPSEEK_PROXY_URL")
if api_proxy_url:
    os.environ["HTTP_PROXY"] = api_proxy_url
    os.environ["HTTPS_PROXY"] = api_proxy_url

app = FastAPI(
    title="PaperForge API",
    description="Verified Academic Document Agent API",
)


@dataclass(frozen=True)
class StoredUpload:
    path: Path
    original_filename: str

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        *[
            origin.strip()
            for origin in os.getenv("CORS_ORIGINS", "").split(",")
            if origin.strip()
        ],
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_database() -> None:
    environment = os.getenv("APP_ENV", os.getenv("ENVIRONMENT", "local")).strip().lower()
    if environment in {"production", "prod"} and not os.getenv("JWT_SECRET_KEY", "").strip():
        raise RuntimeError("JWT_SECRET_KEY must be configured in production.")
    if os.getenv("AUTO_CREATE_DB", "true").strip().lower() == "true":
        init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/templates")
def list_templates(
    school: str | None = Query(None),
    document_type: str | None = Query(None),
    status: str | None = Query("active"),
) -> dict[str, object]:
    if status is not None and status not in TEMPLATE_STATUSES:
        raise HTTPException(status_code=422, detail="status 必须是 active、deprecated 或 disabled。")
    templates = template_registry.list(school=school, document_type=document_type, status=status)
    default_template = template_registry.resolve()
    return {
        "default_template_id": template_registry.default_template_id,
        "default_template_version": default_template.definition.version,
        "templates": [item.public_dict() for item in templates],
    }


@app.post("/auth/register", response_model=AuthResponse, status_code=201)
def register_user(payload: RegisterRequest, db: Session = Depends(get_db)) -> AuthResponse:
    email = validate_email(payload.email)
    if db.scalar(select(User).where(User.email == email)) is not None:
        raise HTTPException(status_code=409, detail="该邮箱已经注册。")
    user = User(email=email, password_hash=hash_password(payload.password))
    workspace_name = f"{email.split('@', 1)[0]}的 PaperForge Space"
    user.workspaces.append(Workspace(name=workspace_name))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="该邮箱已经注册。")
    db.refresh(user)
    workspace = user.workspaces[0]
    return AuthResponse(access_token=create_access_token(user.id), user=UserResponse(id=user.id, email=user.email), workspace_id=workspace.id, workspace_name=workspace.name)


@app.post("/auth/login", response_model=AuthResponse)
def login_user(payload: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    email = validate_email(payload.email)
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="邮箱或密码错误。", headers={"WWW-Authenticate": "Bearer"})
    workspace = db.scalar(select(Workspace).where(Workspace.owner_id == user.id).order_by(Workspace.created_at).limit(1))
    if workspace is None:
        workspace = Workspace(owner_id=user.id, name=f"{email.split('@', 1)[0]}的 PaperForge Space")
        db.add(workspace)
        db.commit()
        db.refresh(workspace)
    return AuthResponse(access_token=create_access_token(user.id), user=UserResponse(id=user.id, email=user.email), workspace_id=workspace.id, workspace_name=workspace.name)


@app.get("/auth/me", response_model=UserResponse)
def current_user(user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse(id=user.id, email=user.email)


def require_user_if_enabled(user: User | None = Depends(get_optional_current_user)) -> User | None:
    if auth_is_required() and user is None:
        raise HTTPException(status_code=401, detail="需要登录后访问。", headers={"WWW-Authenticate": "Bearer"})
    return user


def get_or_create_default_project(db: Session, user: User) -> Project:
    workspace = db.scalar(select(Workspace).where(Workspace.owner_id == user.id).order_by(Workspace.created_at).limit(1))
    if workspace is None:
        workspace = Workspace(owner_id=user.id, name=f"{user.email.split('@', 1)[0]}的 PaperForge Space")
        db.add(workspace)
        db.flush()
    project = db.scalar(select(Project).where(Project.workspace_id == workspace.id).order_by(Project.created_at).limit(1))
    if project is None:
        project = Project(workspace_id=workspace.id, title="PaperForge Documents", status="active")
        db.add(project)
        db.flush()
    return project


@app.get("/workspaces")
def list_workspaces(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict[str, object]]:
    workspaces = db.scalars(select(Workspace).where(Workspace.owner_id == user.id).order_by(Workspace.created_at)).all()
    return [{"id": item.id, "name": item.name, "created_at": item.created_at} for item in workspaces]


@app.get("/tasks")
def list_tasks(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict[str, object]]:
    statement = (
        select(Task)
        .join(Task.project)
        .join(Project.workspace)
        .where(Workspace.owner_id == user.id)
        .order_by(Task.created_at.desc())
    )
    tasks = db.scalars(statement).all()
    return [{"id": item.id, "project_id": item.project_id, "status": item.status, "workflow_stage": item.workflow_stage, "progress": workflow_progress(item.workflow_stage, item.status), "score": item.score, "created_at": item.created_at, "title": item.paper_name or item.project.title} for item in tasks]


@app.get("/tasks/{task_id}")
def get_task(task_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, object]:
    statement = select(Task).join(Task.project).join(Project.workspace).where(Task.id == task_id, Workspace.owner_id == user.id)
    task = db.scalar(statement)
    if task is None:
        raise HTTPException(status_code=404, detail="没有找到该任务。")
    return {"id": task.id, "task_id": task.id, "project_id": task.project_id, "status": task.status, "workflow_stage": task.workflow_stage, "progress": workflow_progress(task.workflow_stage, task.status), "paper_name": task.paper_name or task.project.title, "uploaded_file": task.uploaded_file, "template": template_from_trace(task.agent_trace), "trace": task.agent_trace, "agent_trace": task.agent_trace, "workflow_steps": build_workflow_steps(task.agent_trace, task.workflow_stage, task.status), "score_history": {"before": task.before_score, "after": task.score}, "score": task.score, "created_at": task.created_at, "artifacts": [{"id": item.id, "file_path": item.file_path, "file_type": item.file_type, "download_url": f"/artifacts/{item.id}/download"} for item in task.artifacts]}


@app.get("/tasks/{task_id}/events")
def task_events(
    task_id: str,
    after: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    statement = select(Task).join(Task.project).join(Project.workspace).where(Task.id == task_id, Workspace.owner_id == user.id)
    task = db.scalar(statement)
    if task is None:
        raise HTTPException(status_code=404, detail="没有找到该任务。")

    def stream():
        if task.status in {"completed", "failed"} and not has_events(task_id):
            event_type = "task_completed" if task.status == "completed" else "task_failed"
            payload = {"status": task.status, "workflow_stage": task.workflow_stage, "progress": workflow_progress(task.workflow_stage, task.status), "message": "任务已完成。" if task.status == "completed" else "任务处理失败，请稍后重试。", "timestamp": datetime.now().astimezone().isoformat(), "event_type": event_type}
            yield "event: workflow_update\n"
            yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
            return
        for event in subscribe_event(task_id, after_sequence=after):
            if event is None:
                yield ": keep-alive\n\n"
                continue
            yield f"id: {event.sequence}\n"
            yield "event: workflow_update\n"
            yield f"data: {json.dumps(event.payload, ensure_ascii=False, default=str)}\n\n"

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


@app.post("/tasks", status_code=201)
async def create_task(
    paper: UploadFile = File(...),
    template: UploadFile | None = File(None),
    template_id: str | None = Form(None),
    template_version: str | None = Form(None),
    allow_non_paper: bool = Form(False),
    mode: str = Form("ai"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """Create a task and hand execution to the lightweight in-process worker."""
    if mode not in {"local", "ai"}:
        raise HTTPException(status_code=422, detail="mode 必须是 local 或 ai。")
    request_id = uuid4()
    paper_upload = save_docx(paper, UPLOAD_DIR, request_id)
    template_upload = save_docx(template, UPLOAD_DIR, request_id) if template and template.filename else None
    selected_template = resolve_template_or_422(template_upload, template_id, template_version)
    project = get_or_create_default_project(db, user)
    task = Task(project_id=project.id, status="pending", paper_name=paper_upload.original_filename, uploaded_file=str(paper_upload.path), agent_trace=[template_trace_item(selected_template)])
    db.add(task)
    db.commit()
    db.refresh(task)
    publish_task_event(task.id, "task_created", status="pending", progress=0, message="任务已创建，等待 Agent 启动。", template=selected_template.provenance())
    task_worker.submit(
        run_task_in_worker,
        task.id,
        paper_upload,
        template_upload,
        allow_non_paper,
        mode,
        selected_template,
        sessionmaker(bind=db.get_bind(), autoflush=False, expire_on_commit=False),
    )
    return {"task_id": task.id, "status": "pending", "result_status": "pending"}


@app.post("/document/classify")
async def classify_uploaded_document(paper: UploadFile = File(...), user: User | None = Depends(require_user_if_enabled)) -> dict[str, object]:
    upload = save_docx(paper, UPLOAD_DIR, uuid4())
    result = classify_document(upload.path)
    result["filename"] = upload.original_filename
    return result


@app.post("/agent/run")
async def run_agent(
    paper: UploadFile = File(...),
    template: UploadFile | None = File(None),
    template_id: str | None = Form(None),
    template_version: str | None = Form(None),
    allow_non_paper: bool = Form(False),
    mode: str = Form("ai"),
    user: User | None = Depends(require_user_if_enabled),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    request_id = uuid4()
    paper_upload = save_docx(paper, UPLOAD_DIR, request_id)
    template_upload = save_docx(template, UPLOAD_DIR, request_id) if template and template.filename else None
    selected_template = resolve_template_or_422(template_upload, template_id, template_version)
    task = None
    if user is not None:
        project = get_or_create_default_project(db, user)
        task = Task(project_id=project.id, status="pending", paper_name=paper_upload.original_filename, uploaded_file=str(paper_upload.path))
        db.add(task)
        db.commit()
        db.refresh(task)
    if task is not None:
        result = execute_persisted_task(task, db, paper_upload, template_upload, allow_non_paper, mode, selected_template)
    else:
        result = run_agent_pipeline(
            paper_path=paper_upload.path,
            template_path=template_upload.path if template_upload else None,
            output_dir=OUTPUT_DIR,
            allow_non_paper=allow_non_paper,
            mode=mode,
            paper_display_name=paper_upload.original_filename,
            template_display_name=template_upload.original_filename if template_upload and selected_template.resolution == "legacy_upload" else None,
            resolved_template=selected_template,
        )
    result.setdefault("original_filename", paper_upload.original_filename)
    result.setdefault(
        "original_template_filename",
        template_upload.original_filename if template_upload else None,
    )
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result)
    if task is not None:
        result["task_id"] = task.id
    return result


def publish_task_event(task_id: str, event_type: str, **payload: object) -> None:
    """Event delivery is observational and must not interrupt task execution."""
    try:
        publish_event(task_id, event_type, **payload)
    except Exception:
        LOGGER.exception("Unable to publish task event %s for %s", event_type, task_id)


def resolve_template_or_422(
    template_upload: StoredUpload | None,
    template_id: str | None,
    template_version: str | None,
) -> ResolvedTemplate:
    try:
        return resolve_template_request(
            template_path=template_upload.path if template_upload else None,
            template_id=template_id.strip() if template_id and template_id.strip() else None,
            template_version=template_version.strip() if template_version and template_version.strip() else None,
        )
    except TemplateRegistryError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def template_trace_item(selected_template: ResolvedTemplate) -> dict[str, object]:
    identity = selected_template.provenance()
    return {
        "step": "resolve_template",
        "status": "ok",
        "duration_ms": 0,
        "fallback_used": identity.get("resolution") in {"default", "legacy_upload"},
        "message": f"Template: {identity['name']} / v{identity['version']}",
        "template_id": identity["id"],
        "template_version": identity["version"],
        "template_name": identity["name"],
    }


def execute_persisted_task(
    task: Task,
    db: Session,
    paper_upload: StoredUpload,
    template_upload: StoredUpload | None,
    allow_non_paper: bool,
    mode: str,
    selected_template: ResolvedTemplate,
) -> dict[str, object]:
    """Run the existing Agent and persist only orchestration metadata and artifacts."""
    task.status = "running"
    db.commit()
    publish_task_event(task.id, "task_started", status="running", progress=0, message="Agent 已启动。")

    def on_progress(stage: str) -> None:
        if stage not in {"analyzing", "planning", "executing", "verifying"}:
            return
        task.workflow_stage = stage
        task.status = "running"
        db.commit()
        messages = {"analyzing": "文档解析完成", "planning": "模板分析与格式规划完成", "executing": "正在执行修改", "verifying": "正在进行质量验证"}
        progress = workflow_progress(stage, task.status)
        publish_task_event(task.id, "workflow_stage_changed", status=task.status, workflow_stage=stage, progress=progress, message=messages.get(stage, stage))
        publish_task_event(task.id, "progress_updated", status=task.status, workflow_stage=stage, progress=progress, message=f"当前进度 {progress}%")

    try:
        result = run_agent_pipeline(
            paper_path=paper_upload.path,
            template_path=template_upload.path if template_upload else None,
            output_dir=OUTPUT_DIR,
            allow_non_paper=allow_non_paper,
            mode=mode,
            paper_display_name=paper_upload.original_filename,
            template_display_name=template_upload.original_filename if template_upload and selected_template.resolution == "legacy_upload" else None,
            resolved_template=selected_template,
            progress_callback=on_progress,
        )
    except Exception as exc:
        LOGGER.exception("Persisted task %s failed during orchestration", task.id)
        task.status = "failed"
        task.workflow_stage = "failed"
        task.agent_trace = [{"step": "task_orchestrator", "status": "error", "message": str(exc)}]
        db.commit()
        publish_task_event(task.id, "task_failed", status="failed", workflow_stage="failed", progress=0, message="任务处理失败，请稍后重试。")
        return {"status": "error", "error": str(exc), "agent_trace": task.agent_trace}

    result_trace = result.get("agent_trace")
    if not isinstance(result_trace, list):
        result_trace = []
    task.agent_trace = result_trace
    task.before_score = result.get("before_score") if isinstance(result.get("before_score"), (int, float)) else None
    task.score = result.get("after_score") if isinstance(result.get("after_score"), (int, float)) else None
    result_status = str(result.get("status") or "error")
    if result_status == "error":
        LOGGER.error("Persisted task %s failed: %s", task.id, result.get("error") or "unknown error")
    task.status = "running" if result_status == "ok" else ("pending" if result_status == "requires_confirmation" else "failed")
    task.workflow_stage = "verifying" if result_status == "ok" else ("analyzing" if result_status == "requires_confirmation" else "failed")
    artifact_count = 0
    filename = result.get("filename")
    if isinstance(filename, str):
        task.artifacts.append(Artifact(file_path=str(OUTPUT_DIR / Path(filename).name), file_type="docx"))
        artifact_count += 1
    report = result.get("modification_report")
    if isinstance(report, dict):
        report_path = OUTPUT_DIR / f"{task.id}_report.json"
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        task.artifacts.append(Artifact(file_path=str(report_path), file_type="report"))
        artifact_count += 1
    db.commit()
    db.refresh(task)
    if artifact_count:
        publish_task_event(task.id, "artifact_created", status=task.status, workflow_stage=task.workflow_stage, progress=workflow_progress(task.workflow_stage, task.status), message="处理产物已生成。", artifact_count=artifact_count)
    if result_status == "ok":
        task.status = "completed"
        task.workflow_stage = "completed"
        db.commit()
        publish_task_event(task.id, "task_completed", status="completed", workflow_stage="completed", progress=100, message="任务已完成。")
    elif task.status == "failed":
        publish_task_event(task.id, "task_failed", status="failed", workflow_stage="failed", progress=0, message="任务处理失败，请稍后重试。")
    return result


def run_task_in_worker(
    task_id: str,
    paper_upload: StoredUpload,
    template_upload: StoredUpload | None,
    allow_non_paper: bool,
    mode: str,
    selected_template: ResolvedTemplate,
    session_factory: sessionmaker[Session] = SessionLocal,
) -> None:
    """Run one queued task with a session owned by the worker thread."""
    db = session_factory()
    try:
        task = db.get(Task, task_id)
        if task is None:
            return
        execute_persisted_task(
            task=task,
            db=db,
            paper_upload=paper_upload,
            template_upload=template_upload,
            allow_non_paper=allow_non_paper,
            mode=mode,
            selected_template=selected_template,
        )
    except Exception as exc:
        LOGGER.exception("Task worker failed for task %s", task_id)
        task = db.get(Task, task_id)
        if task is not None:
            task.status = "failed"
            task.workflow_stage = "failed"
            task.agent_trace = [{"step": "task_worker", "status": "error", "message": str(exc)}]
            db.commit()
            publish_task_event(task.id, "task_failed", status="failed", workflow_stage="failed", progress=0, message="任务处理失败，请稍后重试。")
    finally:
        db.close()


def workflow_progress(workflow_stage: str | None, status: str) -> int:
    if status == "failed" or workflow_stage == "failed":
        return 0
    return {"analyzing": 20, "planning": 40, "executing": 60, "verifying": 80, "completed": 100}.get(workflow_stage or "", 0)


def template_from_trace(trace: object) -> dict[str, object] | None:
    if not isinstance(trace, list):
        return None
    for item in trace:
        if isinstance(item, dict) and item.get("step") == "resolve_template":
            return {
                "id": item.get("template_id"),
                "version": item.get("template_version"),
                "name": item.get("template_name") or str(item.get("message") or "").removeprefix("Template: ").rsplit(" / v", 1)[0],
            }
    return None


def build_workflow_steps(trace: object, workflow_stage: str | None = None, task_status: str | None = None) -> list[dict[str, str]]:
    """Project the existing Agent Trace onto the five user-facing workflow stages."""
    stages = [("analyzing", "文档解析"), ("planning", "模板识别与格式规划"), ("executing", "自动修改"), ("verifying", "质量验证"), ("completed", "处理完成")]
    events = trace if isinstance(trace, list) else []
    states = {str(item.get("state", "")).lower() for item in events if isinstance(item, dict)}
    actions = {str(item.get("action", "")).lower() for item in events if isinstance(item, dict)}
    has_error = any(str(item.get("status", "")).lower() in {"error", "failed"} for item in events if isinstance(item, dict))
    completed = {"analyzing", "planning", "executing", "verifying"}
    if states & {"completed", "failed"}:
        completed.update({"analyzing", "planning", "executing", "verifying"})
    result = []
    for key, label in stages:
        active = key in states or (key == "planning" and "accept_execution_plan" in actions)
        status = "completed" if key in completed and (active or states) else ("completed" if key == "completed" and "completed" in states else "pending")
        if key == "completed" and has_error:
            status = "failed"
        elif key == "completed" and "completed" not in states:
            status = "pending"
        result.append({"key": key, "label": label, "status": status})
    if workflow_stage in {"analyzing", "planning", "executing", "verifying", "completed", "failed"}:
        order = ["analyzing", "planning", "executing", "verifying", "completed"]
        current_index = order.index(workflow_stage) if workflow_stage in order else -1
        for item in result:
            if item["key"] in order and order.index(item["key"]) < current_index:
                item["status"] = "completed"
            elif item["key"] == workflow_stage:
                item["status"] = "failed" if workflow_stage == "failed" else ("completed" if workflow_stage == "completed" else "running")
            elif workflow_stage == "failed" and item["key"] == "completed":
                item["status"] = "failed"
            elif workflow_stage != "failed" and item["key"] in order and order.index(item["key"]) > current_index:
                item["status"] = "pending"
    return result


@app.get("/artifacts/{artifact_id}/download")
def download_artifact(artifact_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> FileResponse:
    artifact = db.scalar(select(Artifact).join(Artifact.task).join(Task.project).join(Project.workspace).where(Artifact.id == artifact_id, Workspace.owner_id == user.id))
    if artifact is None:
        raise HTTPException(status_code=404, detail="没有找到属于当前用户的产物。")
    target = Path(artifact.file_path)
    if not target.exists():
        raise HTTPException(status_code=404, detail="产物文件不存在。")
    media_type = "application/json" if artifact.file_type == "report" else "application/octet-stream"
    return FileResponse(path=target, filename=target.name, media_type=media_type)


@app.get("/download/{filename}")
def download_file(filename: str, user: User | None = Depends(require_user_if_enabled), db: Session = Depends(get_db)) -> FileResponse:
    target = OUTPUT_DIR / Path(filename).name
    if not target.exists():
        raise HTTPException(status_code=404, detail="没有找到生成后的 Word 文件。")
    ensure_artifact_access(filename, user, db)
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
    user: User | None = Depends(require_user_if_enabled),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    source = OUTPUT_DIR / Path(filename).name
    if not source.exists():
        raise HTTPException(status_code=404, detail="没有找到可确认修改的 DOCX。")
    ensure_artifact_access(filename, user, db)
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
def preview_file(filename: str, user: User | None = Depends(require_user_if_enabled), db: Session = Depends(get_db)) -> dict[str, str]:
    target = OUTPUT_DIR / Path(filename).name
    if not target.exists():
        raise HTTPException(status_code=404, detail="没有找到可预览的 Word 文件。")
    ensure_artifact_access(filename, user, db)
    return build_docx_preview(target)


def ensure_artifact_access(filename: str, user: User | None, db: Session) -> None:
    if user is None:
        return
    artifact = db.scalar(
        select(Artifact)
        .join(Artifact.task)
        .join(Task.project)
        .join(Project.workspace)
        .where(Artifact.file_path == str(OUTPUT_DIR / Path(filename).name), Workspace.owner_id == user.id)
    )
    if artifact is None:
        raise HTTPException(status_code=404, detail="没有找到属于当前用户的文件。")


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
