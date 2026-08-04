from __future__ import annotations

from pathlib import Path
from time import perf_counter
from typing import Any

from .paper_agent import run_paper_agent
from .task_state import create_task_id, get_task_state_path, init_task_state, update_task_state


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
) -> dict[str, Any]:
    task_id = create_task_id()
    task_state_path = get_task_state_path(output_dir, task_id)
    task_state, task_started_at = init_task_state(
        task_state_path,
        task_id=task_id,
        mode="local" if mode == "local" else "ai",
        paper_path=paper_path,
        template_path=template_path,
    )
    started_at = perf_counter()
    try:
        result = run_paper_agent(
            paper_path=paper_path,
            template_path=template_path,
            output_dir=output_dir,
            allow_non_paper=allow_non_paper,
            mode=mode,
            paper_display_name=paper_display_name,
            template_display_name=template_display_name,
        )
    except Exception as exc:
        duration_ms = elapsed_ms(started_at)
        failed_result = {
            "status": "error",
            "error": str(exc),
            "download_url": None,
            "task_id": task_id,
            "task_state_path": str(task_state_path),
            "agent_trace": [
                {
                    "step": "agent_pipeline",
                    "status": "error",
                    "duration_ms": duration_ms,
                    "fallback_used": False,
                    "message": str(exc),
                }
            ],
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


def normalize_pipeline_result(result: dict[str, Any], total_duration_ms: int) -> dict[str, Any]:
    normalized = dict(result)
    after_analysis = normalized.get("after_analysis") or {}

    if isinstance(after_analysis, dict):
        normalized.setdefault("reference_check", after_analysis.get("reference_check"))
        normalized.setdefault("figure_table_check", after_analysis.get("figure_table_check"))

    legacy_trace = normalized.get("agent_trace")
    if isinstance(legacy_trace, dict):
        normalized.setdefault("agent_trace_detail", legacy_trace)

    normalized["agent_trace"] = build_agent_trace(normalized, total_duration_ms, legacy_trace)
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
