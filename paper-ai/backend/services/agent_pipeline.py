from __future__ import annotations

from pathlib import Path
from time import perf_counter
from typing import Any, Callable

from .paper_agent import run_paper_agent
from .task_state import create_task_id, get_task_state_path, init_task_state, update_task_state
from .template_registry import ResolvedTemplate, resolve_template_request


FALLBACK_BY_STEP = {
    "non_paper_requires_confirmation": "识别文档类型",
    "no_template_uploaded": "识别模板格式",
    "template_parse_warning": "识别模板格式",
    "local_mode_skip_ai": "AI增强审校",
    "llm_unavailable_use_local_rules": "AI增强审校",
}


def run_agent_pipeline(
    paper_path: Path,
    output_dir: Path,
    template_path: Path | None = None,
    allow_non_paper: bool = False,
    mode: str = "ai",
    paper_display_name: str | None = None,
    template_display_name: str | None = None,
    template_id: str | None = None,
    template_version: str | None = None,
    resolved_template: ResolvedTemplate | None = None,
    progress_callback: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    selected_template = resolved_template or resolve_template_request(
        template_path=template_path,
        template_id=template_id,
        template_version=template_version,
    )
    effective_template_path = selected_template.template_path
    template_provenance = selected_template.provenance()
    task_id = create_task_id()
    task_state_path = get_task_state_path(output_dir, task_id)
    task_state, task_started_at = init_task_state(
        task_state_path,
        task_id=task_id,
        mode="local" if mode == "local" else "ai",
        paper_path=paper_path,
        template_path=effective_template_path,
        template=template_provenance,
    )
    started_at = perf_counter()
    try:
        result = run_paper_agent(
            paper_path=paper_path,
            template_path=effective_template_path,
            output_dir=output_dir,
            allow_non_paper=allow_non_paper,
            mode=mode,
            paper_display_name=paper_display_name,
            template_display_name=template_display_name or selected_template.definition.name,
            template_identity=template_provenance,
            progress_callback=progress_callback,
        )
    except Exception as exc:
        if progress_callback is not None:
            try:
                progress_callback("failed")
            except Exception:
                pass
        duration_ms = elapsed_ms(started_at)
        failed_result = {
            "status": "error",
            "error": str(exc),
            "download_url": None,
            "task_id": task_id,
            "task_state_path": str(task_state_path),
            "template": template_provenance,
            "resolved_template_id": template_provenance["id"],
            "resolved_template_version": template_provenance["version"],
            "agent_trace": add_template_trace([
                {
                    "step": "agent_pipeline",
                    "status": "error",
                    "duration_ms": duration_ms,
                    "fallback_used": False,
                    "message": str(exc),
                }
            ], template_provenance),
        }
        update_task_state(
            task_state_path,
            task_state,
            status="failed",
            started_at=task_started_at,
            result=failed_result,
            error=str(exc),
            output_dir=output_dir,
        )
        return failed_result

    normalized = normalize_pipeline_result(result, elapsed_ms(started_at))
    normalized.setdefault("template", template_provenance)
    normalized["resolved_template_id"] = template_provenance["id"]
    normalized["resolved_template_version"] = template_provenance["version"]
    normalized["agent_trace"] = add_template_trace(normalized.get("agent_trace"), template_provenance)
    normalized["task_id"] = task_id
    normalized["task_state_path"] = str(task_state_path)
    update_task_state(
        task_state_path,
        task_state,
        status="failed" if normalized.get("status") == "error" else "succeeded",
        started_at=task_started_at,
        result=normalized,
        error=normalized.get("error") if normalized.get("status") == "error" else None,
        output_dir=output_dir,
    )
    return normalized


def add_template_trace(trace: Any, template: dict[str, Any]) -> list[dict[str, Any]]:
    items = list(trace) if isinstance(trace, list) else []
    if any(isinstance(item, dict) and item.get("step") == "resolve_template" for item in items):
        return items
    return [
        {
            "step": "resolve_template",
            "status": "ok",
            "duration_ms": 0,
            "fallback_used": template.get("resolution") in {"default", "legacy_upload"},
            "message": f"Template: {template.get('name')} / v{template.get('version')}",
            "template_id": template.get("id"),
            "template_version": template.get("version"),
            "template_name": template.get("name"),
        },
        *items,
    ]


def normalize_pipeline_result(result: dict[str, Any], total_duration_ms: int) -> dict[str, Any]:
    normalized = dict(result)
    after_analysis = normalized.get("after_analysis") or {}

    if isinstance(after_analysis, dict):
        normalized.setdefault("reference_check", after_analysis.get("reference_check"))
        normalized.setdefault("figure_table_check", after_analysis.get("figure_table_check"))

    legacy_trace = normalized.get("agent_trace")
    if isinstance(legacy_trace, dict):
        normalized.setdefault("agent_trace_detail", legacy_trace)

    runtime_trace = normalized.get("runtime_trace")
    normalized["agent_trace"] = runtime_trace if isinstance(runtime_trace, list) and runtime_trace else build_agent_trace(normalized, total_duration_ms, legacy_trace)
    return normalized


def build_agent_trace(
    result: dict[str, Any],
    total_duration_ms: int,
    legacy_trace: Any,
) -> list[dict[str, Any]]:
    raw_steps = result.get("steps") or []
    fallback_reasons = legacy_trace.get("fallback_reason", []) if isinstance(legacy_trace, dict) else []
    fallback_steps = {FALLBACK_BY_STEP.get(reason, "") for reason in fallback_reasons}
    fallback_steps.discard("")

    trace_items: list[dict[str, Any]] = []
    for raw_step in raw_steps:
        if not isinstance(raw_step, dict):
            continue
        step_name = str(raw_step.get("step") or raw_step.get("name") or "unknown_step")
        trace_items.append(
            {
                "step": step_name,
                "status": normalize_status(raw_step.get("status")),
                "duration_ms": normalize_duration(raw_step.get("duration_ms")),
                "fallback_used": bool(raw_step.get("fallback_used")) or step_name in fallback_steps,
                "message": str(raw_step.get("message") or ""),
            }
        )

    if not trace_items:
        trace_items.append(
            {
                "step": "agent_pipeline",
                "status": normalize_status(result.get("status")),
                "duration_ms": total_duration_ms,
                "fallback_used": False,
                "message": str(result.get("message") or result.get("error") or "pipeline finished"),
            }
        )

    return trace_items


def normalize_status(status: Any) -> str:
    if status in {"done", "ok", "success"}:
        return "ok"
    if status in {"error", "failed", "fail"}:
        return "error"
    if status in {"requires_confirmation", "skipped", "running", "not_run"}:
        return str(status)
    return str(status or "unknown")


def normalize_duration(value: Any) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def elapsed_ms(started_at: float) -> int:
    return max(0, round((perf_counter() - started_at) * 1000))
