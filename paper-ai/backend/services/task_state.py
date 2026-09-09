from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any
from uuid import uuid4


TASK_STATE_DIR_NAME = "task_states"
TASK_STATE_STATUSES = {"queued", "running", "succeeded", "failed"}


def create_task_id() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"{timestamp}-{uuid4().hex[:12]}"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def get_task_state_path(output_dir: Path, task_id: str) -> Path:
    task_state_dir = output_dir.resolve().parent / TASK_STATE_DIR_NAME
    task_state_dir.mkdir(parents=True, exist_ok=True)
    return task_state_dir / f"{Path(task_id).name}.json"


def write_task_state(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    temp_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    os.replace(temp_path, path)


def init_task_state(
    path: Path,
    *,
    task_id: str,
    mode: str,
    paper_path: Path,
    template_path: Path | None,
) -> tuple[dict[str, Any], float]:
    now = utc_now_iso()
    state = {
        "task_id": task_id,
        "status": "running",
        "mode": mode,
        "created_at": now,
        "updated_at": now,
        "started_at": now,
        "finished_at": None,
        "duration_ms": 0,
        "input_files": {
            "paper_path": str(paper_path),
            "template_path": str(template_path) if template_path else None,
        },
        "output_files": {
            "formatted_docx": None,
            "report_json": None,
            "agent_trace_json": None,
        },
        "classification": None,
        "document_analysis": None,
        "before_score": None,
        "after_score": None,
        "ai_used": None,
        "ai_score": None,
        "fallback_used": False,
        # P0.3 runtime summary fields.  They intentionally coexist with the
        # original task-state schema so older task files remain readable.
        "runtime_state": None,
        "current_phase": None,
        "current_step": None,
        "decision": None,
        "replan_count": 0,
        "human_review_required": False,
        "execution_summary": None,
        "conflict_summary": None,
        "verification_summary": None,
        "hitl_targets": [],
        "error": None,
        "agent_trace_steps_count": 0,
    }
    write_task_state(path, state)
    return state, perf_counter()


def update_task_state(
    path: Path,
    state: dict[str, Any],
    *,
    status: str,
    started_at: float,
    result: dict[str, Any] | None = None,
    error: str | None = None,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    if status not in TASK_STATE_STATUSES:
        raise ValueError(f"invalid task state status: {status}")

    now = utc_now_iso()
    updated = dict(state)
    updated["status"] = status
    updated["updated_at"] = now
    updated["duration_ms"] = max(0, round((perf_counter() - started_at) * 1000))

    if status in {"succeeded", "failed"}:
        updated["finished_at"] = now

    if result:
        apply_result_fields(updated, result, output_dir=output_dir)

    if error:
        updated["error"] = error

    write_task_state(path, updated)
    return updated


def apply_result_fields(state: dict[str, Any], result: dict[str, Any], *, output_dir: Path | None) -> None:
    state["classification"] = result.get("classification")
    if "document_analysis" in result:
        state["document_analysis"] = result.get("document_analysis")
    state["before_score"] = result.get("before_score")
    state["after_score"] = result.get("after_score")

    score_breakdown = result.get("score_breakdown") or {}
    if isinstance(score_breakdown, dict):
        state["ai_used"] = score_breakdown.get("ai_used")
        state["ai_score"] = score_breakdown.get("ai_score")

    trace = result.get("agent_trace")
    if isinstance(trace, list):
        state["agent_trace_steps_count"] = len(trace)
        state["fallback_used"] = any(bool(item.get("fallback_used")) for item in trace if isinstance(item, dict))

    workflow = result.get("workflow")
    if isinstance(workflow, dict):
        runtime_state = workflow.get("current_state")
        state["runtime_state"] = runtime_state
        state["current_phase"] = runtime_state
        state["replan_count"] = workflow.get("replan_count", 0)

    runtime_trace = result.get("runtime_trace")
    if isinstance(runtime_trace, list) and runtime_trace:
        last_event = runtime_trace[-1]
        if isinstance(last_event, dict):
            state["current_step"] = last_event.get("step") or last_event.get("action")

    decision = result.get("decision")
    if isinstance(decision, dict):
        state["decision"] = decision.get("action")
    state["human_review_required"] = bool(result.get("human_review")) or state.get("decision") == "HUMAN_REVIEW"
    execution = result.get("execution") or {}
    if isinstance(execution, dict):
        state["execution_summary"] = {key: execution.get(key) for key in ("executed_step_ids", "unsupported_step_ids", "conflict_step_ids") if key in execution}
        state["conflict_summary"] = execution.get("conflict_summary")
    verification = result.get("verification") or {}
    if isinstance(verification, dict):
        state["verification_summary"] = verification.get("verification_summary")
    review = result.get("human_review")
    if isinstance(review, dict):
        state["hitl_targets"] = review.get("affected_targets") or review.get("items") or []

    filename = result.get("filename")
    if filename and output_dir:
        state["output_files"] = {
            **state.get("output_files", {}),
            "formatted_docx": str(output_dir / Path(str(filename)).name),
        }
