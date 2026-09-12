from __future__ import annotations

import os
import json
import logging
import hashlib
import re
import secrets
import zipfile
from datetime import datetime, timezone
from time import sleep
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID, uuid4

from dotenv import load_dotenv
from fastapi import Body, Depends, FastAPI, File, Form, Header, HTTPException, Query, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse

from services.document_classifier import classify_document
from services.agent_pipeline import run_agent_pipeline
from services.preview_service import build_docx_preview
from services.storage import LocalStorage
from services.content_review import apply_content_suggestion
from services.review_evidence import aggregate_review_evidence, content_score_summary
from auth import auth_is_required, create_access_token, get_current_user, get_optional_current_user, hash_password, is_platform_admin, preview_auto_login_enabled, preview_user_email, require_platform_admin, validate_email, verify_password
from db.models import Artifact, Feedback, Project, Quota, Task, TaskEvent, Template, Tenant, TenantAuditEvent, TenantInvitation, TenantMembership, TenantOwnershipTransfer, Usage, User, Workspace
from db.session import SessionLocal, get_db, init_db
from schemas.auth import AuthResponse, LoginRequest, RegisterRequest, UserResponse
from schemas.feedback import FeedbackRequest
from services.task_worker import task_worker
from services.durable_tasks import advance_running_task, claim_pending_task, finish_running_task, record_task_event, reconcile_orphaned_tasks
from services.observability import bind_context, clear_context, configure_structured_logging, log_event
from services.rate_limit import enforce_rate_limit
from services.rate_limit import api_rate_limit_per_minute
from services.concurrency import TaskConcurrencyExceededError, check_task_concurrency
from services.template_registry import (
    TEMPLATE_STATUSES,
    ResolvedTemplate,
    TemplateNotFoundError,
    TemplateRegistryError,
    resolve_template_request,
    template_registry,
)
from services.template_persistence import bootstrap_template_registry, refresh_template_registry, template_storage
from services.template_repository import TemplateRepository
from services.template_intelligence import analyze_template
from services.tenant_context import TenantContext, bootstrap_personal_tenants, ensure_personal_tenant, get_current_tenant, resolve_tenant_context
from services.rbac import AUDIT_READ, MEMBER_MANAGE, MEMBER_READ, ROLE_ADMIN, ROLE_MEMBER, ROLE_OWNER, ROLE_PERMISSIONS, TASK_CREATE, TASK_MANAGE, TASK_READ, TEMPLATE_READ, TEMPLATE_WRITE, add_member, change_role, remove_member, require_tenant_permission
from services.tenant_invitations import INVITATION_PENDING, accept_invitation, create_invitation, expire_pending_invitations
from services.tenant_audit import record_audit_event
from services.ownership_transfers import ACCEPTED as TRANSFER_ACCEPTED, CANCELLED as TRANSFER_CANCELLED, PENDING as TRANSFER_PENDING, accept_transfer, create_transfer, expire_pending_transfers
from services.quota import QuotaExceededError, check_quota, current_usage_period, get_or_create_quota, get_usage_snapshot, record_usage, usage_response
from sqlalchemy import func, inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker


BASE_DIR = Path(__file__).resolve().parent
STORAGE = LocalStorage(BASE_DIR)
UPLOAD_DIR = STORAGE.path_for("uploads")
TEMPLATE_DIR = BASE_DIR / "templates"
OUTPUT_DIR = STORAGE.path_for("outputs")
MANAGED_TEMPLATE_STORAGE = template_storage()
MAX_TEMPLATE_UPLOAD_BYTES = int(os.getenv("MAX_TEMPLATE_UPLOAD_BYTES", str(20 * 1024 * 1024)))
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(100 * 1024 * 1024)))
MAX_DOCX_UNCOMPRESSED_BYTES = int(os.getenv("MAX_DOCX_UNCOMPRESSED_BYTES", str(300 * 1024 * 1024)))
MAX_DOCX_ARCHIVE_ENTRIES = int(os.getenv("MAX_DOCX_ARCHIVE_ENTRIES", "5000"))
MAX_DOCX_COMPRESSION_RATIO = float(os.getenv("MAX_DOCX_COMPRESSION_RATIO", "200"))
MAX_UPLOAD_FILENAME_LENGTH = int(os.getenv("MAX_UPLOAD_FILENAME_LENGTH", "320"))
MAX_REQUEST_BODY_BYTES = int(os.getenv("MAX_REQUEST_BODY_BYTES", str(240 * 1024 * 1024)))
APP_VERSION = os.getenv("APP_VERSION", "v3.7.3")
LOGGER = logging.getLogger(__name__)
configure_structured_logging()

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


def error_code_for_status(status_code: int) -> str:
    if status_code in {401, 403}: return "AUTH_ERROR"
    if status_code in {400, 409, 413, 415, 422, 429}: return "VALIDATION_ERROR"
    return "INTERNAL_ERROR"


def error_response(request: Request, *, status_code: int, message: object, headers: dict[str, str] | None = None) -> JSONResponse:
    code = error_code_for_status(status_code)
    if request.url.path.startswith("/tasks") and status_code >= 500: code = "TASK_ERROR"
    if request.url.path.startswith(("/templates", "/artifacts", "/download", "/preview")) and status_code >= 500: code = "STORAGE_ERROR"
    return JSONResponse(status_code=status_code, headers=headers, content={"error": {"code": code, "message": message}, "request_id": getattr(request.state, "request_id", None)})


@app.middleware("http")
async def request_diagnostics(request: Request, call_next):
    started = datetime.now().timestamp(); request_id = uuid4().hex
    request.state.request_id = request_id; bind_context(request_id=request_id)
    try:
        content_length = request.headers.get("content-length")
        if request.method in {"POST", "PUT", "PATCH"} and content_length:
            try:
                request_size = int(content_length)
            except ValueError:
                request_size = MAX_REQUEST_BODY_BYTES + 1
            if request_size > MAX_REQUEST_BODY_BYTES:
                raise HTTPException(status_code=413, detail="请求体超过生产资源保护上限。")
        if request.url.path not in {"/health", "/ready"}:
            enforce_rate_limit(request, bucket="api", limit=api_rate_limit_per_minute())
        response = await call_next(request)
    except HTTPException as exc:
        response = error_response(request, status_code=exc.status_code, message=exc.detail, headers=exc.headers)
    except Exception:
        duration = round((datetime.now().timestamp() - started) * 1000)
        log_event(LOGGER, logging.ERROR, "http_request_failed", duration_ms=duration, method=request.method, path=request.url.path, status_code=500, error_code="INTERNAL_ERROR")
        response = error_response(request, status_code=500, message="服务器内部错误。")
    duration = round((datetime.now().timestamp() - started) * 1000)
    response.headers["X-Request-ID"] = request_id
    log_event(LOGGER, logging.INFO if response.status_code < 500 else logging.ERROR, "http_request_completed", duration_ms=duration, method=request.method, path=request.url.path, status_code=response.status_code)
    clear_context()
    return response


@app.exception_handler(HTTPException)
async def classified_http_error(request: Request, exc: HTTPException) -> JSONResponse:
    return error_response(request, status_code=exc.status_code, message=exc.detail, headers=exc.headers)


@app.exception_handler(RequestValidationError)
async def classified_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    return error_response(request, status_code=422, message="请求参数无效。")


@dataclass(frozen=True)
class StoredUpload:
    path: Path
    original_filename: str

def runtime_environment() -> str:
    return os.getenv("APP_ENV", os.getenv("ENVIRONMENT", "local")).strip().lower()


def configured_cors_origins() -> list[str]:
    configured = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "").split(",") if origin.strip()]
    if runtime_environment() in {"production", "prod"}:
        return configured
    return ["http://localhost:3000", "http://127.0.0.1:3000", *configured]


app.add_middleware(
    CORSMiddleware,
    allow_origins=configured_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Accept", "Authorization", "Content-Type", "Last-Event-ID", "X-Tenant-ID"],
)


@app.on_event("startup")
def startup_database() -> None:
    environment = runtime_environment()
    if environment in {"production", "prod"}:
        # Validate here so deployment fails before serving a request.
        from auth import _jwt_secret
        _jwt_secret()
        if not auth_is_required():
            raise RuntimeError("AUTH_REQUIRED=true is required in production.")
        if not configured_cors_origins():
            raise RuntimeError("CORS_ORIGINS must contain the public HTTPS origin in production.")
    auto_create_db = os.getenv("AUTO_CREATE_DB", "true").strip().lower() == "true"
    if environment in {"production", "prod"} and auto_create_db:
        raise RuntimeError("AUTO_CREATE_DB=false is required in production; run Alembic before startup.")
    if auto_create_db:
        init_db()
    db = SessionLocal()
    try:
        db.execute(select(1))
        bootstrap_personal_tenants(db)
        bootstrap_template_registry(db)
        # Alembic is authoritative in production.  The guard keeps historical
        # migration compatibility tests (and an intentionally old local DB)
        # from loading ORM columns that do not exist until Day11 is applied.
        task_columns = {column["name"] for column in inspect(db.get_bind()).get_columns("tasks")}
        if {"progress", "worker_run_id", "recovery_metadata"}.issubset(task_columns):
            interrupted = reconcile_orphaned_tasks(db, worker_identity=f"backend-startup-{uuid4().hex[:12]}")
            if interrupted:
                LOGGER.warning("Reconciled %s orphaned running task(s) after backend startup", interrupted)
    finally:
        db.close()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
def ready(db: Session = Depends(get_db)) -> JSONResponse:
    """Readiness is deliberately limited to database reachability."""
    try:
        db.execute(select(1))
    except Exception:
        return JSONResponse(status_code=503, content={"status": "not_ready", "checks": {"database": "unavailable"}})
    return JSONResponse(content={"status": "ready", "checks": {"database": "ok"}})


@app.get("/templates")
def list_templates(
    school: str | None = Query(None),
    document_type: str | None = Query(None),
    status: str | None = Query("active"),
    user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
    requested_tenant_id: str | None = Header(None, alias="X-Tenant-ID"),
) -> dict[str, object]:
    if status is not None and status not in TEMPLATE_STATUSES:
        raise HTTPException(status_code=422, detail="status 必须是 active、deprecated 或 disabled。")
    bootstrap_template_registry(db)
    context = resolve_tenant_context(db, user, requested_tenant_id) if user is not None else None
    if context is not None:
        require_permission(context, TEMPLATE_READ)
    tenant_id = context.tenant_id if context is not None else None
    repository = TemplateRepository(db)
    templates = repository.list_visible(tenant_id, school=school, document_type=document_type, status=status)
    default_template = template_registry.resolve(tenant_id=tenant_id)
    return {
        "default_template_id": template_registry.default_template_id,
        "default_template_version": default_template.definition.version,
        "templates": [template_public_dict(item) for item in templates],
    }


@app.post("/templates", status_code=201)
def create_managed_template(
    request: Request,
    file: UploadFile = File(...),
    name: str = Form(...),
    version: str = Form(...),
    school: str = Form("通用"),
    document_type: str = Form("academic_paper"),
    template_id: str | None = Form(None),
    context: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    enforce_rate_limit(request, bucket="template-upload", limit=20)
    require_permission(context, TEMPLATE_WRITE)
    original_filename, file_size, checksum = validate_managed_template_upload(file)
    clean_name = require_template_text(name, "name", 300)
    clean_version = require_template_text(version, "version", 100)
    clean_school = require_template_text(school, "school", 200)
    clean_document_type = require_template_text(document_type, "document_type", 100)
    clean_template_id = normalize_template_id(template_id or clean_name)
    repository = TemplateRepository(db)
    if repository.exists(clean_template_id, clean_version, scope="tenant", tenant_id=context.tenant_id):
        raise HTTPException(status_code=409, detail="当前 tenant 中该 template_id 与 version 已存在，不能覆盖已有模板。")
    resource_id = str(uuid4())
    locator: str | None = None
    try:
        file.file.seek(0)
        locator = MANAGED_TEMPLATE_STORAGE.save(context.tenant_id, resource_id, clean_version, file.file)
        local_path = MANAGED_TEMPLATE_STORAGE.resolve_local_path(locator)
        intelligence = analyze_template(local_path).to_dict()
        repository.create(
            resource_id=resource_id, template_id=clean_template_id, version=clean_version, name=clean_name,
            school=clean_school, document_type=clean_document_type, status="active", source="tenant_upload",
            scope="tenant", tenant_id=context.tenant_id, template_path=None, storage_locator=locator,
            original_filename=original_filename, file_size=file_size, content_type=file.content_type or "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            checksum=checksum, uploaded_by=context.current_user.id,
            metadata={"intelligence_summary": {"rule_count": len(intelligence.get("rules", [])), "protected_region_count": len(intelligence.get("protected_regions", []))}},
        )
        db.commit()
    except HTTPException:
        db.rollback()
        if locator:
            MANAGED_TEMPLATE_STORAGE.delete(locator)
        raise
    except Exception as exc:
        db.rollback()
        if locator:
            MANAGED_TEMPLATE_STORAGE.delete(locator)
        LOGGER.exception("Managed template creation failed")
        raise HTTPException(status_code=422, detail="模板无法被解析为有效 DOCX，资源未创建。") from exc
    refresh_template_registry(db)
    created = repository.get_resource(resource_id)
    return template_public_dict(created) if created else {"id": resource_id}


@app.get("/templates/{resource_id}")
def get_template_detail(resource_id: str, context: TenantContext = Depends(get_current_tenant), db: Session = Depends(get_db)) -> dict[str, object]:
    require_permission(context, TEMPLATE_READ)
    item = TemplateRepository(db).get_visible_resource(context.tenant_id, resource_id)
    if item is None:
        raise HTTPException(status_code=404, detail="没有找到模板。")
    return template_public_dict(item)


@app.patch("/templates/{resource_id}")
def update_managed_template(resource_id: str, payload: dict[str, object] = Body(...), context: TenantContext = Depends(get_current_tenant), db: Session = Depends(get_db)) -> dict[str, object]:
    repository = TemplateRepository(db)
    item = repository.get_visible_resource(context.tenant_id, resource_id)
    if item is None or item.scope != "tenant" or item.tenant_id != context.tenant_id:
        raise HTTPException(status_code=404, detail="没有找到可修改的模板。")
    require_permission(context, TEMPLATE_WRITE)
    allowed = {"name": 300, "school": 200, "document_type": 100, "status": 50}
    unexpected = set(payload) - set(allowed)
    if unexpected:
        raise HTTPException(status_code=422, detail="只允许修改 name、school、document_type、status。")
    for field, maximum in allowed.items():
        if field not in payload:
            continue
        value = require_template_text(payload[field], field, maximum)
        if field == "status" and value not in TEMPLATE_STATUSES:
            raise HTTPException(status_code=422, detail="status 必须是 active、deprecated 或 disabled。")
        setattr(item, field, value)
    db.commit()
    refresh_template_registry(db)
    return template_public_dict(item)


@app.get("/templates/{resource_id}/file")
def download_template_file(resource_id: str, context: TenantContext = Depends(get_current_tenant), db: Session = Depends(get_db)) -> FileResponse:
    require_permission(context, TEMPLATE_READ)
    item = TemplateRepository(db).get_visible_resource(context.tenant_id, resource_id)
    if item is None or not item.storage_locator or not MANAGED_TEMPLATE_STORAGE.exists(item.storage_locator):
        raise HTTPException(status_code=404, detail="没有找到模板文件。")
    return FileResponse(MANAGED_TEMPLATE_STORAGE.resolve_local_path(item.storage_locator), filename=safe_upload_filename(item.original_filename or f"{item.template_id}.docx"), media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")


@app.delete("/templates/{resource_id}", status_code=204)
def delete_managed_template(resource_id: str, context: TenantContext = Depends(get_current_tenant), db: Session = Depends(get_db)) -> Response:
    repository = TemplateRepository(db)
    item = repository.get_visible_resource(context.tenant_id, resource_id)
    if item is None or item.scope != "tenant" or item.tenant_id != context.tenant_id:
        raise HTTPException(status_code=404, detail="没有找到可删除的模板。")
    require_permission(context, TEMPLATE_WRITE)
    if template_has_task_provenance(db, item):
        raise HTTPException(status_code=409, detail="该模板已被历史任务使用，只能将 status 更新为 disabled。")
    locator = item.storage_locator
    repository.delete(item)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=409, detail="模板删除失败，文件未删除。")
    if locator:
        try:
            MANAGED_TEMPLATE_STORAGE.delete(locator)
        except Exception:
            LOGGER.exception("Template row deleted but storage cleanup failed: %s", resource_id)
    refresh_template_registry(db)
    return Response(status_code=204)


def template_public_dict(item: Template) -> dict[str, object]:
    return {"id": item.id, "template_id": item.template_id, "version": item.version, "name": item.name, "school": item.school, "document_type": item.document_type, "status": item.status, "source": item.source, "scope": item.scope, "tenant_id": item.tenant_id, "original_filename": item.original_filename, "file_size": item.file_size, "content_type": item.content_type, "checksum": item.checksum, "created_at": item.created_at, "updated_at": item.updated_at, "metadata": item.template_metadata or {}}


def require_template_text(value: object, field: str, maximum: int) -> str:
    if not isinstance(value, str) or not (clean := value.strip()) or len(clean) > maximum or any(ord(character) < 32 for character in clean):
        raise HTTPException(status_code=422, detail=f"{field} 格式不正确。")
    return clean


def normalize_template_id(value: str) -> str:
    base = value.strip().lower()
    base = re.sub(r"[^a-z0-9]+", "-", base).strip("-")
    if not base or len(base) > 200 or ".." in base:
        raise HTTPException(status_code=422, detail="template_id 只允许小写字母、数字和连字符，长度不超过 200。")
    return base


def validate_managed_template_upload(file: UploadFile) -> tuple[str, int, str]:
    return validate_docx_upload(file, maximum_size=MAX_TEMPLATE_UPLOAD_BYTES, label="模板")


def template_has_task_provenance(db: Session, item: Template) -> bool:
    for trace in db.scalars(select(Task.agent_trace).where(Task.tenant_id == item.tenant_id)).all():
        serialized = json.dumps(trace, ensure_ascii=False, default=str)
        if item.template_id in serialized and item.version in serialized:
            return True
    return False


@app.post("/auth/register", response_model=AuthResponse, status_code=201)
def register_user(payload: RegisterRequest, request: Request, db: Session = Depends(get_db)) -> AuthResponse:
    email = validate_email(payload.email)
    enforce_rate_limit(request, bucket=f"auth-register:{email}", limit=10)
    if db.scalar(select(User).where(User.email == email)) is not None:
        raise HTTPException(status_code=409, detail="该邮箱已经注册。")
    user = User(email=email, password_hash=hash_password(payload.password))
    workspace_name = f"{email.split('@', 1)[0]}的 PaperForge Space"
    user.workspaces.append(Workspace(name=workspace_name))
    db.add(user)
    db.flush()
    personal_membership = ensure_personal_tenant(db, user)
    get_or_create_quota(db, personal_membership.tenant_id)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="该邮箱已经注册。")
    db.refresh(user)
    workspace = user.workspaces[0]
    return AuthResponse(access_token=create_access_token(user.id, user.token_version), user=UserResponse(id=user.id, email=user.email, is_admin=is_platform_admin(user)), workspace_id=workspace.id, workspace_name=workspace.name)


@app.post("/auth/login", response_model=AuthResponse)
def login_user(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> AuthResponse:
    email = validate_email(payload.email)
    enforce_rate_limit(request, bucket=f"auth-login:{email}", limit=10)
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="邮箱或密码错误。", headers={"WWW-Authenticate": "Bearer"})
    ensure_personal_tenant(db, user)
    workspace = db.scalar(select(Workspace).where(Workspace.owner_id == user.id).order_by(Workspace.created_at).limit(1))
    if workspace is None:
        workspace = Workspace(owner_id=user.id, name=f"{email.split('@', 1)[0]}的 PaperForge Space")
        db.add(workspace)
        db.flush()
    db.commit()
    db.refresh(workspace)
    return AuthResponse(access_token=create_access_token(user.id, user.token_version), user=UserResponse(id=user.id, email=user.email, is_admin=is_platform_admin(user)), workspace_id=workspace.id, workspace_name=workspace.name)


@app.post("/auth/preview-login", response_model=AuthResponse)
def preview_login(request: Request, db: Session = Depends(get_db)) -> AuthResponse:
    """Create/load the reserved local Preview user without exposing a password."""
    if not preview_auto_login_enabled():
        raise HTTPException(status_code=404, detail="Preview 自动登录未启用。")
    enforce_rate_limit(request, bucket="auth-preview-login", limit=60)
    email = preview_user_email()
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(email=email, password_hash=hash_password(secrets.token_urlsafe(32)))
        user.workspaces.append(Workspace(name="PaperForge Preview Space"))
        db.add(user)
        db.flush()
    membership = ensure_personal_tenant(db, user)
    get_or_create_quota(db, membership.tenant_id)
    workspace = db.scalar(select(Workspace).where(Workspace.owner_id == user.id).order_by(Workspace.created_at).limit(1))
    if workspace is None:
        workspace = Workspace(owner_id=user.id, name="PaperForge Preview Space")
        db.add(workspace)
        db.flush()
    db.commit()
    db.refresh(user)
    db.refresh(workspace)
    return AuthResponse(access_token=create_access_token(user.id, user.token_version), user=UserResponse(id=user.id, email=user.email, is_admin=is_platform_admin(user)), workspace_id=workspace.id, workspace_name=workspace.name)


@app.get("/auth/me", response_model=UserResponse)
def current_user(user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse(id=user.id, email=user.email, is_admin=is_platform_admin(user))


@app.post("/auth/revoke-sessions")
def revoke_sessions(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, bool]:
    """Invalidate every existing bearer token for the authenticated user."""
    user.token_version += 1
    db.commit()
    return {"revoked": True}


def require_permission(context: TenantContext, permission: str) -> None:
    require_tenant_permission(context.membership, permission)


def membership_public_dict(membership: TenantMembership) -> dict[str, object]:
    return {
        "tenant_id": membership.tenant_id,
        "user_id": membership.user_id,
        "email": membership.user.email,
        "role": membership.role,
        "joined_at": membership.created_at,
        "permissions": sorted(ROLE_PERMISSIONS[membership.role]),
    }


def invitation_public_dict(invitation: TenantInvitation) -> dict[str, object]:
    return {
        "id": invitation.id,
        "tenant_id": invitation.tenant_id,
        "email": invitation.email,
        "role": invitation.role,
        "status": invitation.status,
        "expires_at": invitation.expires_at,
        "created_at": invitation.created_at,
        "accepted_at": invitation.accepted_at,
    }

def transfer_public_dict(transfer: TenantOwnershipTransfer) -> dict[str, object]:
    return {"id": transfer.id, "tenant_id": transfer.tenant_id, "from_user_id": transfer.from_user_id, "to_user_id": transfer.to_user_id, "status": transfer.status, "expires_at": transfer.expires_at, "created_at": transfer.created_at, "accepted_at": transfer.accepted_at, "cancelled_at": transfer.cancelled_at}


def require_owner_governance(context: TenantContext) -> None:
    require_permission(context, MEMBER_MANAGE)


@app.get("/tenants/membership/me")
def current_membership(context: TenantContext = Depends(get_current_tenant)) -> dict[str, object]:
    return membership_public_dict(context.membership)


@app.get("/tenants/{tenant_id}/membership/me")
def tenant_membership_me(tenant_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, object]:
    return membership_public_dict(resolve_tenant_context(db, user, tenant_id).membership)


@app.get("/tenants/{tenant_id}/members")
def list_tenant_members(tenant_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict[str, object]]:
    context = resolve_tenant_context(db, user, tenant_id)
    require_permission(context, MEMBER_READ)
    memberships = db.scalars(select(TenantMembership).where(TenantMembership.tenant_id == tenant_id, TenantMembership.status == "active").order_by(TenantMembership.created_at)).all()
    return [membership_public_dict(item) for item in memberships]


@app.post("/tenants/{tenant_id}/members", status_code=201)
def add_tenant_member(tenant_id: str, payload: dict[str, object] = Body(...), user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, object]:
    context = resolve_tenant_context(db, user, tenant_id)
    require_owner_governance(context)
    email = validate_email(str(payload.get("email") or ""))
    role = str(payload.get("role") or ROLE_MEMBER)
    if role not in {ROLE_ADMIN, ROLE_MEMBER}:
        raise HTTPException(status_code=422, detail="成员角色只能是 admin 或 member。")
    target = db.scalar(select(User).where(User.email == email))
    if target is None:
        raise HTTPException(status_code=404, detail="没有找到可添加的用户。")
    try:
        membership = add_member(db, tenant_id=tenant_id, user_id=target.id, role=role)
        record_audit_event(db, tenant_id=tenant_id, actor_user_id=user.id, event_type="membership.added", target_type="membership", target_id=target.id, metadata={"role": role})
        db.commit()
        db.refresh(membership)
        return membership_public_dict(membership)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="该用户已是此 Workspace 成员。") from exc


@app.patch("/tenants/{tenant_id}/members/{user_id}")
def update_tenant_member(tenant_id: str, user_id: str, payload: dict[str, object] = Body(...), user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, object]:
    context = resolve_tenant_context(db, user, tenant_id)
    require_owner_governance(context)
    role = str(payload.get("role") or "")
    if role not in {ROLE_ADMIN, ROLE_MEMBER}:
        raise HTTPException(status_code=422, detail="成员角色只能是 admin 或 member。")
    membership = db.scalar(select(TenantMembership).where(TenantMembership.tenant_id == tenant_id, TenantMembership.user_id == user_id))
    if membership is None:
        raise HTTPException(status_code=404, detail="没有找到成员。")
    try:
        previous_role = membership.role
        change_role(db, membership, role, actor=context.membership)
        record_audit_event(db, tenant_id=tenant_id, actor_user_id=user.id, event_type="membership.role_changed", target_type="membership", target_id=user_id, metadata={"from_role": previous_role, "to_role": role})
        db.commit()
        db.refresh(membership)
        return membership_public_dict(membership)
    except (ValueError, PermissionError) as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Owner 不能通过普通成员接口变更角色。") from exc


@app.delete("/tenants/{tenant_id}/members/{user_id}", status_code=204)
def delete_tenant_member(tenant_id: str, user_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Response:
    context = resolve_tenant_context(db, user, tenant_id)
    require_owner_governance(context)
    membership = db.scalar(select(TenantMembership).where(TenantMembership.tenant_id == tenant_id, TenantMembership.user_id == user_id))
    if membership is None:
        raise HTTPException(status_code=404, detail="没有找到成员。")
    try:
        remove_member(db, membership, actor=context.membership)
        record_audit_event(db, tenant_id=tenant_id, actor_user_id=user.id, event_type="membership.removed", target_type="membership", target_id=user_id)
        db.commit()
    except (ValueError, PermissionError) as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Owner 不能通过普通成员接口删除。") from exc
    return Response(status_code=204)


@app.post("/tenants/{tenant_id}/invitations", status_code=201)
def create_tenant_invitation(tenant_id: str, payload: dict[str, object] = Body(...), user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, object]:
    context = resolve_tenant_context(db, user, tenant_id)
    require_owner_governance(context)
    email = validate_email(str(payload.get("email") or ""))
    role = str(payload.get("role") or ROLE_MEMBER)
    if role not in {ROLE_ADMIN, ROLE_MEMBER}:
        raise HTTPException(status_code=422, detail="邀请角色只能是 admin 或 member。")
    try:
        invitation, token = create_invitation(db, tenant_id=tenant_id, email=email, role=role, created_by=user.id)
        record_audit_event(db, tenant_id=tenant_id, actor_user_id=user.id, event_type="invitation.created", target_type="invitation", target_id=invitation.id, metadata={"email": email, "role": role})
        db.commit()
        db.refresh(invitation)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    result = invitation_public_dict(invitation)
    result["token"] = token
    result["invitation_url"] = f"/tenant-invitations/{token}/accept"
    return result


@app.get("/tenants/{tenant_id}/invitations")
def list_tenant_invitations(tenant_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict[str, object]]:
    context = resolve_tenant_context(db, user, tenant_id)
    require_owner_governance(context)
    expire_pending_invitations(db, tenant_id)
    db.commit()
    invitations = db.scalars(select(TenantInvitation).where(TenantInvitation.tenant_id == tenant_id).order_by(TenantInvitation.created_at.desc())).all()
    return [invitation_public_dict(item) for item in invitations]


@app.delete("/tenants/{tenant_id}/invitations/{invitation_id}", status_code=204)
def revoke_tenant_invitation(tenant_id: str, invitation_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Response:
    context = resolve_tenant_context(db, user, tenant_id)
    require_owner_governance(context)
    invitation = db.scalar(select(TenantInvitation).where(TenantInvitation.id == invitation_id, TenantInvitation.tenant_id == tenant_id))
    if invitation is None:
        raise HTTPException(status_code=404, detail="没有找到邀请。")
    if invitation.status != INVITATION_PENDING:
        raise HTTPException(status_code=409, detail="该邀请已不可撤销。")
    invitation.status = "revoked"
    record_audit_event(db, tenant_id=tenant_id, actor_user_id=user.id, event_type="invitation.revoked", target_type="invitation", target_id=invitation.id)
    db.commit()
    return Response(status_code=204)


@app.post("/tenant-invitations/{token}/accept")
def accept_tenant_invitation(token: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, object]:
    try:
        invitation = accept_invitation(db, token=token, user=user)
        record_audit_event(db, tenant_id=invitation.tenant_id, actor_user_id=user.id, event_type="invitation.accepted", target_type="membership", target_id=user.id)
        db.commit()
        return {"status": "accepted", "membership": membership_public_dict(db.scalar(select(TenantMembership).where(TenantMembership.tenant_id == invitation.tenant_id, TenantMembership.user_id == user.id)))}
    except PermissionError as exc:
        db.rollback()
        raise HTTPException(status_code=403, detail="邀请邮箱与当前登录用户不匹配。") from exc
    except ValueError as exc:
        db.commit() if "expired" in str(exc) else db.rollback()
        raise HTTPException(status_code=409, detail="邀请无效、已使用、已撤销或已过期。") from exc


@app.patch("/tenants/{tenant_id}")
def update_tenant_settings(tenant_id: str, payload: dict[str, object] = Body(...), user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, object]:
    context = resolve_tenant_context(db, user, tenant_id); require_owner_governance(context)
    name = payload.get("display_name", payload.get("name"))
    if not isinstance(name, str) or not (clean := name.strip()) or len(clean) > 300: raise HTTPException(status_code=422, detail="Workspace 名称不能为空且不能超过 300 字符。")
    context.tenant.name = clean
    record_audit_event(db, tenant_id=tenant_id, actor_user_id=user.id, event_type="tenant.settings_updated", target_type="tenant", target_id=tenant_id, metadata={"display_name": clean})
    db.commit(); db.refresh(context.tenant)
    return {"id": context.tenant.id, "tenant_id": context.tenant.id, "name": context.tenant.name, "updated_at": context.tenant.updated_at}


@app.post("/tenants/{tenant_id}/ownership-transfer", status_code=201)
def begin_ownership_transfer(tenant_id: str, payload: dict[str, object] = Body(...), user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, object]:
    context = resolve_tenant_context(db, user, tenant_id); require_owner_governance(context)
    to_user_id = str(payload.get("to_user_id") or "")
    try:
        transfer, token = create_transfer(db, tenant_id=tenant_id, actor=context.membership, to_user_id=to_user_id); db.commit(); db.refresh(transfer)
    except ValueError as exc:
        db.rollback(); raise HTTPException(status_code=409, detail=str(exc)) from exc
    result = transfer_public_dict(transfer); result["token"] = token; result["accept_url"] = f"/ownership-transfer?token={token}"; return result


@app.get("/tenants/{tenant_id}/ownership-transfer")
def get_pending_ownership_transfer(tenant_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, object] | None:
    context = resolve_tenant_context(db, user, tenant_id); require_owner_governance(context); expire_pending_transfers(db, tenant_id); db.commit()
    transfer = db.scalar(select(TenantOwnershipTransfer).where(TenantOwnershipTransfer.tenant_id == tenant_id, TenantOwnershipTransfer.status == TRANSFER_PENDING))
    return transfer_public_dict(transfer) if transfer else None


@app.delete("/tenants/{tenant_id}/ownership-transfer/{transfer_id}", status_code=204)
def cancel_ownership_transfer(tenant_id: str, transfer_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Response:
    context = resolve_tenant_context(db, user, tenant_id); require_owner_governance(context)
    transfer = db.scalar(select(TenantOwnershipTransfer).where(TenantOwnershipTransfer.id == transfer_id, TenantOwnershipTransfer.tenant_id == tenant_id).with_for_update())
    if transfer is None: raise HTTPException(status_code=404, detail="没有找到 ownership transfer。")
    if transfer.status != TRANSFER_PENDING or transfer.from_user_id != user.id: raise HTTPException(status_code=409, detail="该 transfer 已不可取消。")
    transfer.status = TRANSFER_CANCELLED; transfer.cancelled_at = datetime.utcnow(); record_audit_event(db, tenant_id=tenant_id, actor_user_id=user.id, event_type="ownership_transfer.cancelled", target_type="ownership_transfer", target_id=transfer.id); db.commit(); return Response(status_code=204)


@app.post("/tenant-ownership-transfers/{token}/accept")
def accept_ownership_transfer(token: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, object]:
    try:
        transfer = accept_transfer(db, token=token, user=user); db.commit()
        return {"status": TRANSFER_ACCEPTED, "tenant_id": transfer.tenant_id}
    except PermissionError as exc:
        db.rollback(); raise HTTPException(status_code=403, detail="当前用户不是该 ownership transfer 的目标成员。") from exc
    except ValueError as exc:
        db.rollback(); raise HTTPException(status_code=409, detail="ownership transfer 无效、已结束或参与者状态已变化。") from exc


@app.get("/tenants/{tenant_id}/audit-events")
def list_audit_events(tenant_id: str, limit: int = Query(30, ge=1, le=100), offset: int = Query(0, ge=0), event_type: str | None = Query(None), user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, object]:
    context = resolve_tenant_context(db, user, tenant_id); require_permission(context, AUDIT_READ)
    statement = select(TenantAuditEvent).where(TenantAuditEvent.tenant_id == tenant_id).order_by(TenantAuditEvent.created_at.desc()).offset(offset).limit(limit)
    if event_type: statement = statement.where(TenantAuditEvent.event_type == event_type)
    events = db.scalars(statement).all()
    return {"events": [{"id": item.id, "actor_user_id": item.actor_user_id, "event_type": item.event_type, "target_type": item.target_type, "target_id": item.target_id, "metadata": item.metadata_json, "created_at": item.created_at} for item in events], "offset": offset, "limit": limit}


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
    ensure_personal_tenant(db, user)
    memberships = db.scalars(select(TenantMembership).where(TenantMembership.user_id == user.id, TenantMembership.status == "active").order_by(TenantMembership.created_at)).all()
    return [{"id": item.tenant_id, "tenant_id": item.tenant_id, "name": item.tenant.name, "role": item.role, "created_at": item.tenant.created_at} for item in memberships if item.tenant.status == "active"]


@app.get("/tasks")
def list_tasks(context: TenantContext = Depends(get_current_tenant), db: Session = Depends(get_db)) -> list[dict[str, object]]:
    require_permission(context, TASK_READ)
    statement = select(Task).where(Task.tenant_id == context.tenant_id).order_by(Task.created_at.desc())
    tasks = db.scalars(statement).all()
    return [{"id": item.id, "project_id": item.project_id, "tenant_id": item.tenant_id, "user_id": item.user_id, "status": item.status, "workflow_stage": item.workflow_stage, "progress": item.progress, "score": item.score, "created_at": item.created_at, "title": item.paper_name or item.project.title, "status_explanation": task_status_explanation(item.status)} for item in tasks]


@app.get("/tasks/{task_id}")
def get_task(task_id: str, context: TenantContext = Depends(get_current_tenant), db: Session = Depends(get_db)) -> dict[str, object]:
    require_permission(context, TASK_READ)
    statement = select(Task).where(Task.id == task_id, Task.tenant_id == context.tenant_id)
    task = db.scalar(statement)
    if task is None:
        raise HTTPException(status_code=404, detail="没有找到该任务。")
    result_metadata = task.result_metadata if isinstance(task.result_metadata, dict) else {}
    return {"id": task.id, "task_id": task.id, "project_id": task.project_id, "tenant_id": task.tenant_id, "user_id": task.user_id, "status": task.status, "workflow_stage": task.workflow_stage, "progress": task.progress, "current_stage": task.current_stage, "started_at": task.started_at, "finished_at": task.finished_at, "updated_at": task.updated_at, "error_code": task.error_code, "error_message": task.error_message, "attempt_count": task.attempt_count, "paper_name": task.paper_name or task.project.title, "uploaded_file": task.uploaded_file, "template": template_from_trace(task.agent_trace), "trace": task.agent_trace, "agent_trace": task.agent_trace, "workflow_steps": build_workflow_steps(task.agent_trace, task.workflow_stage, task.status), "score_history": {"before": task.before_score, "after": task.score}, "score": task.score, "created_at": task.created_at, "status_explanation": task_status_explanation(task.status), "retry_available": task.status in {"failed", "interrupted"} and stored_input_file(task.uploaded_file) is not None, "score_breakdown": result_metadata.get("score_breakdown"), "verification": result_metadata.get("verification"), "verification_summary": result_metadata.get("verification_summary"), "artifacts": [{"id": item.id, "file_path": item.file_path, "file_type": item.file_type, "download_url": f"/artifacts/{item.id}/download", "preview_url": f"/preview/{Path(item.file_path).name}" if item.file_type == "docx" else None} for item in task.artifacts]}


@app.post("/tasks/{task_id}/retry")
def retry_task(task_id: str, context: TenantContext = Depends(get_current_tenant), db: Session = Depends(get_db)) -> dict[str, object]:
    """Requeue a failed/interrupted task using its original uploaded input."""
    require_permission(context, TASK_CREATE)
    task = db.scalar(select(Task).where(Task.id == task_id, Task.tenant_id == context.tenant_id))
    if task is None:
        raise HTTPException(status_code=404, detail="没有找到该任务。")
    if task.user_id != context.current_user.id:
        require_permission(context, TASK_MANAGE)
    if task.status not in {"failed", "interrupted"}:
        raise HTTPException(status_code=409, detail="只有失败或中断任务可以重试。")
    paper_path = stored_input_file(task.uploaded_file)
    if paper_path is None:
        raise HTTPException(status_code=409, detail="原始上传文件已不可用，无法重试。")
    try:
        check_task_concurrency(db, context.tenant_id, context.current_user.id)
    except TaskConcurrencyExceededError as exc:
        db.rollback()
        raise HTTPException(status_code=429, detail={"code": "TASK_CONCURRENCY_LIMIT", "message": "当前活跃任务数已达到并发上限，请稍后重试。", "scope": exc.scope, "concurrency": exc.snapshot.as_dict()}) from exc

    metadata = task.input_metadata if isinstance(task.input_metadata, dict) else {}
    template_meta = metadata.get("template") if isinstance(metadata.get("template"), dict) else {}
    template_path = stored_input_file(metadata.get("template_upload_path"))
    template_upload = StoredUpload(template_path, template_path.name) if template_path else None
    selected_template = resolve_template_or_422(db, template_upload, None if template_path else str(template_meta.get("id") or "") or None, None if template_path else str(template_meta.get("version") or "") or None, context.tenant_id)
    previous_status = task.status
    task.status = "pending"
    task.workflow_stage = None
    task.current_stage = None
    task.progress = 0
    task.started_at = None
    task.finished_at = None
    task.worker_run_id = None
    task.error_code = None
    task.error_message = None
    task.recovery_metadata = {"reason": "user_retry", "retried_at": datetime.now(timezone.utc).isoformat(), "previous_status": previous_status}
    task.state_version += 1
    db.commit()
    db.refresh(task)
    publish_task_event(task.id, "task_retry_requested", db=db, status="pending", progress=0, message="用户已请求重新执行任务。")
    task_worker.submit(run_task_in_worker, task.id, StoredUpload(paper_path, task.paper_name or paper_path.name), template_upload, bool(metadata.get("allow_non_paper", False)), str(metadata.get("mode") or "ai"), selected_template, sessionmaker(bind=db.get_bind(), autoflush=False, expire_on_commit=False))
    return {"task_id": task.id, "status": "pending", "retry_started": True}


@app.get("/tasks/{task_id}/events")
def task_events(
    task_id: str,
    after: int = Query(0, ge=0),
    last_event_id: str | None = Header(None, alias="Last-Event-ID"),
    context: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    require_permission(context, TASK_READ)
    statement = select(Task).where(Task.id == task_id, Task.tenant_id == context.tenant_id)
    task = db.scalar(statement)
    if task is None:
        raise HTTPException(status_code=404, detail="没有找到该任务。")

    try:
        cursor = max(after, int(last_event_id or 0))
    except ValueError:
        raise HTTPException(status_code=422, detail="Last-Event-ID 必须是事件序号。")
    session_factory = sessionmaker(bind=db.get_bind(), autoflush=False, expire_on_commit=False)

    def stream():
        current = cursor
        while True:
            stream_db = session_factory()
            try:
                events = stream_db.scalars(select(TaskEvent).where(TaskEvent.task_id == task_id, TaskEvent.tenant_id == context.tenant_id, TaskEvent.sequence > current).order_by(TaskEvent.sequence).limit(100)).all()
                current_task = stream_db.scalar(select(Task).where(Task.id == task_id, Task.tenant_id == context.tenant_id))
                for event in events:
                    current = event.sequence
                    payload = {"status": event.metadata_json.get("status"), "workflow_stage": event.stage, "progress": event.progress, "message": event.message, "timestamp": event.created_at.isoformat(), "event_type": event.event_type, "event_id": event.id}
                    yield f"id: {event.sequence}\n"
                    yield "event: workflow_update\n"
                    yield f"data: {json.dumps(payload, ensure_ascii=False, default=str)}\n\n"
                if current_task is None or (current_task.status in {"completed", "failed", "cancelled", "interrupted"} and not events):
                    return
            finally:
                stream_db.close()
            yield ": keep-alive\n\n"
            sleep(1)

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


@app.post("/tasks", status_code=201)
async def create_task(
    request: Request,
    paper: UploadFile = File(...),
    template: UploadFile | None = File(None),
    template_id: str | None = Form(None),
    template_version: str | None = Form(None),
    allow_non_paper: bool = Form(False),
    mode: str = Form("ai"),
    context: TenantContext = Depends(get_current_tenant),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    """Create a task and hand execution to the lightweight in-process worker."""
    require_permission(context, TASK_CREATE)
    enforce_rate_limit(request, bucket=f"task-create:{context.current_user.id}", limit=20)
    if mode not in {"local", "ai"}:
        raise HTTPException(status_code=422, detail="mode 必须是 local 或 ai。")
    try:
        check_task_concurrency(db, context.tenant_id, context.current_user.id)
    except TaskConcurrencyExceededError as exc:
        db.rollback()
        raise HTTPException(
            status_code=429,
            detail={
                "code": "TASK_CONCURRENCY_LIMIT",
                "message": "当前用户或 tenant 的活跃任务数已达到并发上限，请等待已有任务完成。",
                "scope": exc.scope,
                "concurrency": exc.snapshot.as_dict(),
            },
        ) from exc
    request_id = uuid4()
    paper_upload: StoredUpload | None = None
    template_upload: StoredUpload | None = None
    try:
        paper_upload = save_docx(paper, UPLOAD_DIR, request_id)
        template_upload = save_docx(template, UPLOAD_DIR, request_id) if template and template.filename else None
        selected_template = resolve_template_or_422(db, template_upload, template_id, template_version, context.tenant_id)
        project = get_or_create_default_project(db, context.current_user)
        task = Task(project_id=project.id, tenant_id=context.tenant_id, user_id=context.current_user.id, status="pending", progress=0, paper_name=paper_upload.original_filename, uploaded_file=str(paper_upload.path), agent_trace=[template_trace_item(selected_template)], input_metadata={"mode": mode, "allow_non_paper": allow_non_paper, "template": selected_template.provenance(), "template_upload_path": str(template_upload.path) if template_upload else None, "original_paper_name": paper_upload.original_filename})
        db.add(task)
        db.commit()
        db.refresh(task)
    except Exception:
        db.rollback()
        for upload in (paper_upload, template_upload):
            if upload is not None:
                upload.path.unlink(missing_ok=True)
        raise
    bind_context(tenant_id=task.tenant_id, user_id=task.user_id, task_id=task.id)
    log_event(LOGGER, logging.INFO, "task_created")
    publish_task_event(task.id, "task_created", db=db, status="pending", progress=0, message="任务已创建，等待 Agent 启动。", template=selected_template.provenance())
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
async def classify_uploaded_document(request: Request, paper: UploadFile = File(...), user: User | None = Depends(require_user_if_enabled)) -> dict[str, object]:
    enforce_rate_limit(request, bucket="document-classify", limit=30)
    upload = save_docx(paper, UPLOAD_DIR, uuid4())
    try:
        result = classify_document(upload.path)
        result["filename"] = upload.original_filename
        return result
    finally:
        upload.path.unlink(missing_ok=True)
        try:
            upload.path.parent.rmdir()
        except OSError:
            pass


@app.get("/usage")
def get_usage(context: TenantContext = Depends(get_current_tenant), db: Session = Depends(get_db)) -> dict[str, object]:
    """Return the current tenant's monthly Agent-run quota and usage."""
    snapshot = get_usage_snapshot(db, context.tenant_id)
    db.commit()
    return usage_response(snapshot)


@app.post("/feedback", status_code=201)
def create_feedback(payload: FeedbackRequest, request: Request, context: TenantContext = Depends(get_current_tenant), db: Session = Depends(get_db)) -> dict[str, object]:
    """Store tenant-scoped user feedback without accepting forged identity fields."""
    description = payload.description.strip()
    if not description:
        raise HTTPException(status_code=422, detail="问题描述不能为空。")
    task = None
    if payload.task_id:
        task = db.scalar(select(Task).where(Task.id == payload.task_id, Task.tenant_id == context.tenant_id))
        if task is None:
            raise HTTPException(status_code=404, detail="没有找到当前工作区中的任务。")
    metadata: dict[str, object] = {}
    if payload.category == "slow" and task is not None:
        now = datetime.now(timezone.utc)
        started = task.started_at
        finished = task.finished_at
        end = finished or now
        if started is not None:
            if started.tzinfo is None:
                started = started.replace(tzinfo=timezone.utc)
            if end.tzinfo is None:
                end = end.replace(tzinfo=timezone.utc)
            metadata["task_status"] = task.status
            metadata["elapsed_seconds"] = max(0, round((end - started).total_seconds(), 3))
            metadata["timing_source"] = "task.started_at/finished_at"
    item = Feedback(
        user_id=context.current_user.id,
        tenant_id=context.tenant_id,
        category=payload.category,
        description=description,
        contact=payload.contact.strip() if payload.contact and payload.contact.strip() else None,
        route=payload.route.strip() if payload.route and payload.route.strip() else None,
        task_id=task.id if task else None,
        request_id=getattr(request.state, "request_id", None),
        app_version=APP_VERSION,
        metadata_json=metadata or None,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"id": item.id, "status": "submitted", "message": "反馈已提交，感谢你的帮助。"}


@app.get("/admin/stats")
def admin_stats(_admin: User = Depends(require_platform_admin), db: Session = Depends(get_db)) -> dict[str, object]:
    """Return aggregate operational metrics for explicitly configured admins."""
    period = current_usage_period()
    tenant_total = int(db.scalar(select(func.count()).select_from(Tenant)) or 0)
    active_tenant_total = int(
        db.scalar(select(func.count()).select_from(Tenant).where(Tenant.status == "active")) or 0
    )
    user_total = int(db.scalar(select(func.count()).select_from(User)) or 0)
    task_total = int(db.scalar(select(func.count()).select_from(Task)) or 0)
    task_status_summary = {
        str(status): int(count)
        for status, count in db.execute(
            select(Task.status, func.count()).group_by(Task.status).order_by(Task.status)
        ).all()
    }
    current_usage = int(
        db.scalar(
            select(func.coalesce(func.sum(Usage.quantity), 0)).where(
                Usage.metric == "agent_run",
                Usage.period_start >= period.start,
                Usage.period_start < period.end,
            )
        )
        or 0
    )
    all_time_usage = int(
        db.scalar(
            select(func.coalesce(func.sum(Usage.quantity), 0)).where(Usage.metric == "agent_run")
        )
        or 0
    )
    quota_limit = int(db.scalar(select(func.coalesce(func.sum(Quota.monthly_limit), 0))) or 0)
    return {
        "generated_at": datetime.now(timezone.utc),
        "tenants": {"total": tenant_total, "active": active_tenant_total},
        "users": {"total": user_total},
        "tasks": {"total": task_total, "status_summary": task_status_summary},
        "usage": {
            "metric": "agent_run",
            "period_start": period.start,
            "period_end": period.end,
            "used": current_usage,
            "all_time_used": all_time_usage,
            "monthly_quota_total": quota_limit,
            "monthly_quota_remaining": max(0, quota_limit - current_usage),
        },
    }


@app.post("/agent/run")
async def run_agent(
    request: Request,
    paper: UploadFile = File(...),
    template: UploadFile | None = File(None),
    template_id: str | None = Form(None),
    template_version: str | None = Form(None),
    allow_non_paper: bool = Form(False),
    mode: str = Form("ai"),
    user: User | None = Depends(require_user_if_enabled),
    db: Session = Depends(get_db),
    requested_tenant_id: str | None = Header(None, alias="X-Tenant-ID"),
) -> dict[str, object]:
    enforce_rate_limit(request, bucket=f"agent-run:{user.id if user else 'anonymous'}", limit=10)
    if mode not in {"local", "ai"}:
        raise HTTPException(status_code=422, detail="mode 必须是 local 或 ai。")
    context = resolve_tenant_context(db, user, requested_tenant_id) if user is not None else None
    if context is not None:
        require_permission(context, TASK_CREATE)
        try:
            quota_snapshot = check_quota(db, context.tenant_id)
            check_task_concurrency(db, context.tenant_id, context.current_user.id)
        except QuotaExceededError as exc:
            db.rollback()
            raise HTTPException(
                status_code=429,
                detail={
                    "code": "QUOTA_EXCEEDED",
                    "message": "当前 tenant 的本月 Agent 运行额度已用尽。",
                    "usage": usage_response(exc.snapshot),
                },
            ) from exc
        except TaskConcurrencyExceededError as exc:
            db.rollback()
            raise HTTPException(
                status_code=429,
                detail={
                    "code": "TASK_CONCURRENCY_LIMIT",
                    "message": "当前用户或 tenant 的活跃任务数已达到并发上限，请等待已有任务完成。",
                    "scope": exc.scope,
                    "concurrency": exc.snapshot.as_dict(),
                },
            ) from exc
    request_id = uuid4()
    paper_upload: StoredUpload | None = None
    template_upload: StoredUpload | None = None
    try:
        paper_upload = save_docx(paper, UPLOAD_DIR, request_id)
        template_upload = save_docx(template, UPLOAD_DIR, request_id) if template and template.filename else None
        selected_template = resolve_template_or_422(db, template_upload, template_id, template_version, context.tenant_id if context else None)
    except Exception:
        db.rollback()
        for upload in (paper_upload, template_upload):
            if upload is not None:
                upload.path.unlink(missing_ok=True)
        raise
    task = None
    if context is not None:
        project = get_or_create_default_project(db, context.current_user)
        task = Task(project_id=project.id, tenant_id=context.tenant_id, user_id=context.current_user.id, status="pending", progress=0, paper_name=paper_upload.original_filename, uploaded_file=str(paper_upload.path), input_metadata={"mode": mode, "allow_non_paper": allow_non_paper, "template": selected_template.provenance(), "template_upload_path": str(template_upload.path) if template_upload else None, "original_paper_name": paper_upload.original_filename})
        db.add(task)
        db.flush()
        record_usage(db, tenant_id=context.tenant_id, user_id=context.current_user.id, task_id=task.id, period=quota_snapshot.period)
        db.commit()
        db.refresh(task)
        bind_context(tenant_id=task.tenant_id, user_id=task.user_id, task_id=task.id)
        log_event(LOGGER, logging.INFO, "task_created")
        publish_task_event(task.id, "task_created", db=db, status="pending", progress=0, message="任务已创建，正在同步执行。", template=selected_template.provenance())
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
            tenant_id=context.tenant_id if context else None,
            user_id=context.current_user.id if context else None,
        )
    result.setdefault("original_filename", paper_upload.original_filename)
    result.setdefault(
        "original_template_filename",
        template_upload.original_filename if template_upload else None,
    )
    if result["status"] == "error":
        LOGGER.error("Agent request failed for task %s", task.id if task is not None else "legacy")
        raise HTTPException(status_code=500, detail="任务处理失败，请稍后重试。")
    if task is not None:
        result["task_id"] = task.id
    return result


def publish_task_event(task_id: str, event_type: str, *, db: Session, **payload: object) -> None:
    """Append an event before committing state; PostgreSQL is the SSE authority."""
    try:
        task = db.get(Task, task_id)
        if task is None:
            return
        record_task_event(db, task, event_type, **payload)
        db.commit()
    except Exception:
        db.rollback()
        LOGGER.exception("Unable to publish task event %s for %s", event_type, task_id)


def resolve_template_or_422(
    db: Session,
    template_upload: StoredUpload | None,
    template_id: str | None,
    template_version: str | None,
    tenant_id: str | None,
) -> ResolvedTemplate:
    try:
        bootstrap_template_registry(db)
        return resolve_template_request(
            template_path=template_upload.path if template_upload else None,
            template_id=template_id.strip() if template_id and template_id.strip() else None,
            template_version=template_version.strip() if template_version and template_version.strip() else None,
            tenant_id=tenant_id,
        )
    except TemplateNotFoundError as exc:
        raise HTTPException(status_code=404, detail="没有找到可用模板。") from exc
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
    run_id = claim_pending_task(db, task.id)
    if run_id is None:
        return {"status": "error", "error": "任务已被其他 worker 领取或已结束。"}
    db.refresh(task)
    bind_context(tenant_id=task.tenant_id, user_id=task.user_id, task_id=task.id)
    log_event(LOGGER, logging.INFO, "task_claimed")
    log_event(LOGGER, logging.INFO, "task_started")
    publish_task_event(task.id, "task_started", db=db, status="running", workflow_stage="analyzing", progress=0, message="Agent 已启动。", worker_run_id=run_id)

    def on_progress(stage: str) -> None:
        if stage not in {"analyzing", "planning", "executing", "verifying"}:
            return
        progress = workflow_progress(stage, "running")
        if not advance_running_task(db, task, run_id, stage=stage, progress=progress):
            return
        log_event(LOGGER, logging.INFO, "task_stage_changed")
        messages = {"analyzing": "文档解析完成", "planning": "模板分析与格式规划完成", "executing": "正在执行修改", "verifying": "正在进行质量验证"}
        publish_task_event(task.id, "workflow_stage_changed", db=db, status="running", workflow_stage=stage, progress=progress, message=messages.get(stage, stage))
        publish_task_event(task.id, "progress_updated", db=db, status="running", workflow_stage=stage, progress=progress, message=f"当前进度 {progress}%")

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
            tenant_id=task.tenant_id,
            user_id=task.user_id,
        )
    except Exception as exc:
        log_event(LOGGER, logging.ERROR, "task_failed", error_code="TASK_ERROR")
        LOGGER.exception("Persisted task orchestration failed")
        task.agent_trace = [{"step": "task_orchestrator", "status": "error", "message": str(exc)}]
        db.commit()
        finish_running_task(db, task, run_id, status="failed", stage="failed", progress=task.progress, error_code="agent_exception", error_message=str(exc))
        publish_task_event(task.id, "task_failed", db=db, status="failed", workflow_stage="failed", progress=task.progress, message="任务处理失败，请稍后重试。")
        return {"status": "error", "error": str(exc), "agent_trace": task.agent_trace}

    result_trace = result.get("agent_trace")
    if not isinstance(result_trace, list):
        result_trace = []
    task.agent_trace = [template_trace_item(selected_template), *result_trace]
    task.before_score = result.get("before_score") if isinstance(result.get("before_score"), (int, float)) else None
    task.score = result.get("after_score") if isinstance(result.get("after_score"), (int, float)) else None
    result_status = str(result.get("status") or "error")
    if result_status == "error":
        log_event(LOGGER, logging.ERROR, "task_failed", error_code="TASK_ERROR")
    # Persist metadata while the row is still owned by this exact execution.
    if task.status != "running" or task.worker_run_id != run_id:
        return {"status": "error", "error": "任务执行租约已失效。"}
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
    verification = result.get("verification") if isinstance(result.get("verification"), dict) else None
    verification_summary = verification_summary_from_result(result)
    if artifact_count:
        publish_task_event(task.id, "artifact_created", db=db, status="running", workflow_stage="verifying", progress=80, message="处理产物已生成。", artifact_count=artifact_count)
    if result_status == "ok":
        finish_running_task(db, task, run_id, status="completed", stage="completed", progress=100, result_metadata={"filename": result.get("filename"), "artifact_count": artifact_count, "score_breakdown": result.get("score_breakdown"), "verification": verification, "verification_summary": verification_summary})
        publish_task_event(task.id, "task_completed", db=db, status="completed", workflow_stage="completed", progress=100, message="任务已完成。")
        log_event(LOGGER, logging.INFO, "task_completed")
    elif result_status == "requires_confirmation":
        # Existing synchronous compatibility behavior exposes confirmation as pending.
        task.status = "pending"; task.workflow_stage = "analyzing"; task.current_stage = "analyzing"; task.worker_run_id = None; task.updated_at = datetime.now().astimezone(); task.state_version += 1
        db.commit()
        publish_task_event(task.id, "task_confirmation_required", db=db, status="pending", workflow_stage="analyzing", progress=task.progress, message="任务需要用户确认后继续。")
    else:
        finish_running_task(db, task, run_id, status="failed", stage="failed", progress=task.progress, error_code="agent_error", error_message=str(result.get("error") or "Agent failed"))
        publish_task_event(task.id, "task_failed", db=db, status="failed", workflow_stage="failed", progress=task.progress, message="任务处理失败，请稍后重试。")
        log_event(LOGGER, logging.ERROR, "task_failed", error_code="TASK_ERROR")
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
        bind_context(task_id=task_id)
        log_event(LOGGER, logging.ERROR, "task_failed", error_code="TASK_ERROR")
        LOGGER.exception("Task worker failed")
        task = db.get(Task, task_id)
        if task is not None:
            task.agent_trace = [{"step": "task_worker", "status": "error", "message": str(exc)}]
            db.commit()
            if task.status == "running" and task.worker_run_id:
                finish_running_task(db, task, task.worker_run_id, status="failed", stage="failed", progress=task.progress, error_code="worker_exception", error_message=str(exc))
                publish_task_event(task.id, "task_failed", db=db, status="failed", workflow_stage="failed", progress=task.progress, message="任务处理失败，请稍后重试。")
    finally:
        db.close()


def workflow_progress(workflow_stage: str | None, status: str) -> int:
    if status == "failed" or workflow_stage == "failed":
        return 0
    return {"analyzing": 20, "planning": 40, "executing": 60, "verifying": 80, "completed": 100}.get(workflow_stage or "", 0)


def task_status_explanation(status: str | None) -> str | None:
    return {
        "failed": "任务执行失败，原始上传文件仍保留，可以点击重试。",
        "interrupted": "后端重启中断了任务，系统不会伪造断点续跑，可以点击重试。",
        "completed": "任务已完成，结果已经过验证并可预览或下载。",
    }.get(status)


def stored_input_file(value: object) -> Path | None:
    """Resolve a retryable input only inside the managed uploads directory."""
    if not isinstance(value, str) or not value.strip():
        return None
    candidate = Path(value).resolve()
    upload_root = UPLOAD_DIR.resolve()
    if upload_root not in candidate.parents or not candidate.is_file():
        return None
    return candidate


def verification_summary_from_result(result: dict[str, object]) -> dict[str, object] | None:
    verification = result.get("verification")
    if not isinstance(verification, dict):
        return None
    summary = verification.get("verification_summary")
    if isinstance(summary, dict):
        return summary
    provenance = result.get("provenance")
    if isinstance(provenance, dict):
        nested = provenance.get("summary")
        if isinstance(nested, dict) and isinstance(nested.get("verification"), dict):
            return nested["verification"]
    return None


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
def download_artifact(artifact_id: str, context: TenantContext = Depends(get_current_tenant), db: Session = Depends(get_db)) -> FileResponse:
    require_permission(context, TASK_READ)
    artifact = db.scalar(select(Artifact).join(Artifact.task).where(Artifact.id == artifact_id, Task.tenant_id == context.tenant_id))
    if artifact is None:
        raise HTTPException(status_code=404, detail="没有找到属于当前用户的产物。")
    target = Path(artifact.file_path)
    if not target.exists():
        raise HTTPException(status_code=404, detail="产物文件不存在。")
    media_type = "application/json" if artifact.file_type == "report" else "application/octet-stream"
    return FileResponse(path=target, filename=target.name, media_type=media_type)


@app.get("/download/{filename}")
def download_file(filename: str, user: User | None = Depends(require_user_if_enabled), db: Session = Depends(get_db), requested_tenant_id: str | None = Header(None, alias="X-Tenant-ID")) -> FileResponse:
    context = resolve_tenant_context(db, user, requested_tenant_id) if user is not None else None
    if context is None:
        if auth_is_required():
            raise HTTPException(status_code=404, detail="没有找到生成后的 Word 文件。")
        target = OUTPUT_DIR / Path(filename).name
    else:
        require_permission(context, TASK_READ)
        artifact = ensure_artifact_access(filename, context, db)
        if artifact is None:
            raise HTTPException(status_code=404, detail="没有找到生成后的 Word 文件。")
        target = Path(artifact.file_path)
    if not target.is_file():
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
    user: User | None = Depends(require_user_if_enabled),
    db: Session = Depends(get_db),
    requested_tenant_id: str | None = Header(None, alias="X-Tenant-ID"),
) -> dict[str, object]:
    context = resolve_tenant_context(db, user, requested_tenant_id) if user is not None else None
    if context is None:
        if auth_is_required():
            raise HTTPException(status_code=404, detail="没有找到可确认修改的 DOCX。")
        source_artifact = None
        source = OUTPUT_DIR / Path(filename).name
    else:
        require_permission(context, TASK_MANAGE)
        source_artifact = ensure_artifact_access(filename, context, db)
        if source_artifact is None:
            raise HTTPException(status_code=404, detail="没有找到可确认修改的 DOCX。")
        source = Path(source_artifact.file_path)
    if not source.is_file():
        raise HTTPException(status_code=404, detail="没有找到可确认修改的 DOCX。")
    output = OUTPUT_DIR / f"{source.stem}_confirmed_{datetime.now().strftime('%Y%m%d%H%M%S%f')}.docx"
    result = apply_content_suggestion(source, output, {"issue_id": issue_id, "paragraph_index": paragraph_index, "original_text": original, "suggested_text": suggested, "issue_type": issue_type, "reason": reason, "confidence": confidence})
    if result.get("status") == "conflict":
        raise HTTPException(status_code=409, detail=result)
    if result.get("status") != "ok":
        raise HTTPException(status_code=422, detail=result)
    if source_artifact is not None:
        source_artifact.task.artifacts.append(Artifact(file_path=str(output), file_type="docx"))
        db.commit()
    accepted_review = {"issues": [{"issue_id": issue_id, "paragraph_index": paragraph_index, "issue_type": issue_type, "original_text": original, "suggested_text": suggested, "reason": reason, "confidence": confidence, "action_policy": "SUGGEST_ONLY", "source": "user_confirmed", "status": "accepted"}], "provenance": {"auto_fixes": [], "suggestions": [], "accepted": [result["change"]], "hitl": []}}
    evidence = aggregate_review_evidence(content_review=accepted_review)
    result["review_summary"] = evidence["review_summary"]
    result["change_evidence"] = evidence["change_evidence"]
    result["pending_actions"] = evidence["pending_actions"]
    result["content_score"] = content_score_summary(accepted_review)
    return result


@app.get("/preview/{filename}")
def preview_file(filename: str, user: User | None = Depends(require_user_if_enabled), db: Session = Depends(get_db), requested_tenant_id: str | None = Header(None, alias="X-Tenant-ID")) -> dict[str, str]:
    context = resolve_tenant_context(db, user, requested_tenant_id) if user is not None else None
    if context is None:
        if auth_is_required():
            raise HTTPException(status_code=404, detail="没有找到可预览的 Word 文件。")
        target = OUTPUT_DIR / Path(filename).name
    else:
        require_permission(context, TASK_READ)
        artifact = ensure_artifact_access(filename, context, db)
        if artifact is None:
            raise HTTPException(status_code=404, detail="没有找到可预览的 Word 文件。")
        target = Path(artifact.file_path)
    if not target.is_file():
        raise HTTPException(status_code=404, detail="没有找到可预览的 Word 文件。")
    return build_docx_preview(target)


def ensure_artifact_access(filename: str, context: TenantContext | None, db: Session) -> Artifact | None:
    if context is None:
        return None
    return db.scalar(
        select(Artifact)
        .join(Artifact.task)
        .where(Artifact.file_path == str(OUTPUT_DIR / Path(filename).name), Task.tenant_id == context.tenant_id)
    )


def save_docx(file: UploadFile, directory: Path, request_id: UUID) -> StoredUpload:
    original_filename, _, _ = validate_docx_upload(file, maximum_size=MAX_UPLOAD_BYTES, label="论文")
    request_dir = directory / request_id.hex
    request_dir.mkdir(parents=True, exist_ok=True)

    target = request_dir / f"{uuid4().hex}.docx"
    try:
        with target.open("xb") as destination:
            copied = 0
            while chunk := file.file.read(1024 * 1024):
                copied += len(chunk)
                if copied > MAX_UPLOAD_BYTES:
                    raise HTTPException(status_code=413, detail=f"论文文件不能超过 {MAX_UPLOAD_BYTES} 字节。")
                destination.write(chunk)
    except Exception:
        target.unlink(missing_ok=True)
        raise
    return StoredUpload(path=target, original_filename=original_filename)


def validate_docx_upload(file: UploadFile, *, maximum_size: int, label: str) -> tuple[str, int, str]:
    """Validate both DOCX container shape and bounded archive expansion."""
    filename = safe_upload_filename(file.filename)
    allowed_content_types = {None, "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/octet-stream"}
    if file.content_type not in allowed_content_types:
        raise HTTPException(status_code=415, detail=f"{label}文件类型必须是 DOCX。")
    file.file.seek(0, os.SEEK_END)
    size = file.file.tell()
    file.file.seek(0)
    if size <= 0:
        raise HTTPException(status_code=422, detail=f"{label}文件不能为空。")
    if size > maximum_size:
        raise HTTPException(status_code=413, detail=f"{label}文件不能超过 {maximum_size} 字节。")
    hasher = hashlib.sha256()
    while chunk := file.file.read(1024 * 1024):
        hasher.update(chunk)
    digest = hasher.hexdigest()
    file.file.seek(0)
    try:
        with zipfile.ZipFile(file.file) as archive:
            members = archive.infolist()
            names = [member.filename.replace("\\", "/") for member in members]
            total_uncompressed = sum(member.file_size for member in members)
            total_compressed = sum(max(0, member.compress_size) for member in members)
            unsafe_member = any(
                name.startswith("/") or ".." in Path(name).parts or (member.external_attr >> 16) & 0o170000 == 0o120000
                for name, member in zip(names, members, strict=True)
            )
            ratio = total_uncompressed / max(1, total_compressed)
            if (
                len(members) > MAX_DOCX_ARCHIVE_ENTRIES
                or len(set(names)) != len(names)
                or unsafe_member
                or total_uncompressed > MAX_DOCX_UNCOMPRESSED_BYTES
                or ratio > MAX_DOCX_COMPRESSION_RATIO
            ):
                raise ValueError("archive expansion exceeds limit")
            if "[Content_Types].xml" not in archive.namelist() or "word/document.xml" not in archive.namelist():
                raise ValueError("missing DOCX parts")
    except (zipfile.BadZipFile, ValueError) as exc:
        raise HTTPException(status_code=422, detail=f"{label}不是可读取的 DOCX 文件。") from exc
    finally:
        file.file.seek(0)
    return filename, size, digest


def safe_upload_filename(filename: str | None) -> str:
    raw_filename = (filename or "").strip()
    if not raw_filename or "\x00" in raw_filename:
        raise HTTPException(status_code=400, detail="只支持 .docx 文件。")

    safe_name = Path(raw_filename.replace("\\", "/")).name
    if (
        not safe_name
        or len(safe_name) > MAX_UPLOAD_FILENAME_LENGTH
        or any(ord(character) < 32 for character in safe_name)
        or Path(safe_name).suffix.lower() != ".docx"
    ):
        raise HTTPException(status_code=400, detail="只支持 .docx 文件。")
    return safe_name
