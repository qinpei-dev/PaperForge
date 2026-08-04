from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from time import perf_counter
from typing import Any

from .agent_orchestrator import AgentTraceBuilder
from .document_classifier import classify_document
from .docx_analyzer import analyze_docx
from .docx_formatter import apply_paper_format
from .language_reviewer import apply_language_suggestions, review_language_with_status
from .plagiarism_checker import check_repeat_risk
from .template_extractor import extract_template_profile


RISK_LEVELS = ("blocking", "high_risk", "warning", "info")
REVIEW_RISK_LEVELS = {"blocking", "high_risk"}


@dataclass
class AgentState:
    paper_path: Path
    output_dir: Path
    template_path: Path | None = None
    steps: list[dict[str, Any]] = field(default_factory=list)
    current_step: str = ""
    current_step_started_at: float | None = None

    def start(self, name: str, message: str) -> None:
        self.current_step = name
        self.current_step_started_at = perf_counter()
        self.steps.append({"name": name, "status": "running", "message": message, "duration_ms": 0, "fallback_used": False})

    def finish(self, message: str, *, fallback_used: bool = False) -> None:
        self.steps[-1] = {
            "name": self.current_step,
            "status": "done",
            "message": message,
            "duration_ms": self._elapsed_ms(),
            "fallback_used": fallback_used,
        }

    def fail(self, message: str, *, fallback_used: bool = False) -> None:
        if self.steps and self.steps[-1]["status"] == "running":
            self.steps[-1] = {
                "name": self.current_step,
                "status": "error",
                "message": message,
                "duration_ms": self._elapsed_ms(),
                "fallback_used": fallback_used,
            }
        else:
            self.steps.append(
                {
                    "name": self.current_step or "unknown_step",
                    "status": "error",
                    "message": message,
                    "duration_ms": self._elapsed_ms(),
                    "fallback_used": fallback_used,
                }
            )

    def _elapsed_ms(self) -> int:
        if self.current_step_started_at is None:
            return 0
        return max(0, round((perf_counter() - self.current_step_started_at) * 1000))


def run_paper_agent(
    paper_path: Path,
    output_dir: Path,
    template_path: Path | None = None,
    allow_non_paper: bool = False,
    mode: str = "ai",
    paper_display_name: str | None = None,
    template_display_name: str | None = None,
) -> dict[str, Any]:
    state = AgentState(paper_path=paper_path, template_path=template_path, output_dir=output_dir)
    normalized_mode = "local" if mode == "local" else "ai"
    paper_name = paper_display_name or paper_path.name
    template_name = template_display_name or (template_path.name if template_path else None)
    trace = AgentTraceBuilder(mode=normalized_mode, has_template=template_path is not None)
    classification: dict[str, Any] | None = None
    template_profile: dict[str, Any] | None = None
    language_review: dict[str, Any] | None = None
    after_analysis: dict[str, Any] | None = None
    modification_report: dict[str, Any] | None = None

    try:
        state.start("识别文档类型", "正在判断该文件是否为标准论文。")
        classification = classify_document(paper_path)
        trace.mark_task("classify_document", "done", f"{classification['label']}，置信度 {classification['confidence']}")
        trace.record_tool("document_classifier.classify_document", summary=f"{classification['label']}，置信度 {classification['confidence']}")
        if classification["requires_confirmation"] and not allow_non_paper:
            trace.add_fallback("non_paper_requires_confirmation")
            state.finish(classification["warning"], fallback_used=True)
            return {
                "status": "requires_confirmation",
                "requires_confirmation": True,
                "classification": classification,
                "steps": state.steps,
                "message": classification["warning"],
                "agent_trace": trace.build(
                    classification=classification,
                    requires_confirmation=True,
                    status="requires_confirmation",
                ),
            }
        state.finish(f"文档类型：{classification['label']}，置信度 {round(classification['confidence'] * 100)}%。")

        state.start("读取论文", "正在读取 Word 文档、正文段落和基础样式。")
        if not paper_path.exists():
            raise FileNotFoundError("论文文件不存在")
        state.finish(f"已读取 {paper_name}")

        state.start("分析本地格式", "正在进行结构、标题、字体、行距、页边距和参考文献基础评估。")
        before_repeat = check_repeat_risk(paper_path)
        before_analysis = analyze_docx(paper_path, template_path=template_path, repeat_score=before_repeat["score_for_quality"])
        trace.mark_task("analyze_before", "done", f"修改前评分 {before_analysis['report']['score']}")
        trace.record_tool("docx_analyzer.analyze_docx", summary=f"修改前评分 {before_analysis['report']['score']}")
        before_score = int(before_analysis["report"]["score"])
        state.finish(f"本地模式初评 {before_score}。")

        state.start("识别模板格式", "正在读取模板页边距、正文样式和标题格式。")
        template_profile = extract_template_profile(template_path) if template_path else None
        if template_profile and template_name:
            template_profile["filename"] = template_name
        trace.mark_task("extract_template", "done" if template_path else "skipped", "已读取上传模板" if template_path else "未上传模板，使用默认规则")
        if template_path:
            trace.record_tool("template_extractor.extract_template_profile", summary=f"模板：{template_name}")
        if template_profile and template_path:
            warnings = template_profile.get("warnings") or []
            warning_text = f"；提示：{'；'.join(warnings)}" if warnings else ""
            if warnings:
                trace.add_fallback("template_parse_warning")
            state.finish(f"已识别模板：{template_name}{warning_text}", fallback_used=bool(warnings))
        else:
            state.finish("未上传模板，按通用论文规范执行。", fallback_used=True)

        state.start("修复标题与正文格式", "正在统一标题层级、正文字体、段落缩进和页面基础格式。")
        formatted_path = build_output_path(output_dir, paper_path, "formatted")
        format_log = apply_paper_format(paper_path, formatted_path, template_path)
        trace.mark_task("format_document", "done", f"格式处理记录 {len(format_log)} 项")
        trace.record_tool("docx_formatter.apply_paper_format", summary=f"格式处理记录 {len(format_log)} 项")
        state.finish("标题、正文和页面基础格式已统一。")

        language_log: list[str] = []
        language_review = {
            "mode": "local",
            "error": None,
            "suggestions": [],
            "ai_scores": None,
            "ai_added_value": [],
        }
        final_path = formatted_path

        if normalized_mode == "ai":
            state.start("AI增强审校", "正在分析语言规范性、表达流畅度、论文逻辑性和学术表达质量。")
            language_path = build_output_path(output_dir, paper_path, "language")
            language_review = review_language_with_status(formatted_path)
            suggestions = language_review["suggestions"]
            language_log = apply_language_suggestions(formatted_path, language_path, suggestions)
            trace.mark_task("language_review", "done", f"{language_review['mode']} 模式，建议 {len(suggestions)} 条")
            trace.record_tool("language_reviewer.review_language_with_status", summary=f"{language_review['mode']} 模式，建议 {len(suggestions)} 条")
            if language_review["mode"] != "ai":
                trace.add_fallback("llm_unavailable_use_local_rules")
            final_path = language_path
            applied_language_count = len([item for item in language_log if "->" in item])
            if language_review["mode"] == "ai":
                warning = f"；提示：{language_review['error']}" if language_review.get("error") else ""
                state.finish(f"AI增强完成，应用 {applied_language_count} 条语言优化{warning}。")
            else:
                state.finish(f"AI不可用，已使用本地语言规则，应用 {applied_language_count} 条优化；提示：{language_review.get('error') or 'AI未返回可用结果'}。", fallback_used=True)
        else:
            state.start("AI增强审校", "本地规则模式已启用，本轮跳过 AI 语言审校。")
            trace.mark_task("language_review", "skipped", "local 模式跳过 AI 审校")
            trace.add_fallback("local_mode_skip_ai")
            state.finish("本地规则模式不计算 AI 语言、流畅度、逻辑和学术表达评分。", fallback_used=True)

        state.start("重复风险预检", "正在检测相似段落、重复句子和重复风险等级。")
        repeat_risk = check_repeat_risk(final_path)
        state.finish(f"重复风险等级：{repeat_risk['level']}，风险值 {repeat_risk['score']}/100。")

        state.start("最终复查", "正在计算本地评分、AI增强评分和最终评分。")
        after_analysis = analyze_docx(
            final_path,
            template_path=template_path,
            repeat_score=repeat_risk["score_for_quality"],
            ai_scores=language_review["ai_scores"] if normalized_mode == "ai" else None,
        )
        trace.mark_task("analyze_after", "done", f"最终评分 {after_analysis['report']['score']}")
        trace.record_tool("docx_analyzer.analyze_docx", summary=f"最终评分 {after_analysis['report']['score']}")
        after_score = int(after_analysis["report"]["score"])
        score_breakdown = after_analysis["report"]["score_breakdown"]
        state.finish(f"最终评分 {after_score}，AI使用状态：{'已启用' if score_breakdown['ai_used'] else '未启用'}。")

        state.start("生成最终报告", "正在整理修复记录、前后对比和人工复查建议。")
        modification_report = build_modification_report(
            before_analysis,
            after_analysis,
            format_log,
            language_log,
            repeat_risk,
            template_path,
            template_display_name=template_name,
        )
        trace.mark_task("generate_report", "done", f"人工复查项 {len(modification_report.get('manual_review_items') or [])} 项")
        trace.record_tool("report_generator/build_modification_report", summary=f"人工复查项 {len(modification_report.get('manual_review_items') or [])} 项")
        state.finish(f"报告已生成，最终文件：{final_path.name}")

        return {
            "status": "ok",
            "mode": normalized_mode,
            "requires_confirmation": False,
            "classification": classification,
            "steps": state.steps,
            "before_score": before_score,
            "after_score": after_score,
            "score_breakdown": score_breakdown,
            "repeat_risk": repeat_risk,
            "download_url": f"/download/{final_path.name}",
            "filename": final_path.name,
            "original_filename": paper_name,
            "original_template_filename": template_name,
            "before_analysis": before_analysis,
            "after_analysis": after_analysis,
            "modification_report": modification_report,
            "language_review": {"mode": language_review["mode"], "error": language_review["error"]},
            "language_suggestions": language_review["suggestions"],
            "agent_trace": trace.build(
                classification=classification,
                template_profile=template_profile,
                language_review=language_review,
                modification_report=modification_report,
                after_analysis=after_analysis,
                requires_confirmation=False,
                status="ok",
            ),
        }
    except Exception as exc:
        state.fail(str(exc))
        return {
            "status": "error",
            "failed_step": state.current_step,
            "steps": state.steps,
            "error": str(exc),
            "download_url": None,
            "agent_trace": trace.build(
                classification=classification,
                template_profile=template_profile,
                language_review=language_review,
                modification_report=modification_report,
                after_analysis=after_analysis,
                status="error",
            ),
        }


def build_output_path(output_dir: Path, source: Path, suffix: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return output_dir / f"{source.stem}_{suffix}_{timestamp}.docx"


def build_modification_report(
    before_analysis: dict[str, Any],
    after_analysis: dict[str, Any],
    format_log: list[str],
    language_log: list[str],
    repeat_risk: dict[str, Any],
    template_path: Path | None,
    template_display_name: str | None = None,
) -> dict[str, Any]:
    before_items = {item["key"]: item for item in before_analysis["report"]["breakdown"]}
    comparisons = []
    for after_item in after_analysis["report"]["breakdown"]:
        before_item = before_items.get(after_item["key"], after_item)
        comparisons.append(
            {
                "key": after_item["key"],
                "label": after_item["label"],
                "before": before_item["score"],
                "after": after_item["score"],
                "delta": after_item["score"] - before_item["score"],
                "status": after_item["status"],
            }
        )

    language_changes = len([item for item in language_log if "->" in item])
    auto_fix_count = len(format_log) + language_changes
    changed_dimensions = [item for item in comparisons if item["delta"] != 0]
    score_delta_by_dimension = {item["key"]: item["delta"] for item in comparisons}
    unresolved_issues = collect_unresolved(after_analysis)
    risk_items = collect_check_risk_items(after_analysis)
    manual_review_items = build_manual_review_items(risk_items)
    warning_items = build_warning_items(after_analysis, unresolved_issues, risk_items)
    info_items = build_info_items(risk_items)
    risk_summary = build_report_risk_summary(risk_items)
    score_explanation = (after_analysis["report"].get("score_breakdown") or {}).get(
        "score_explanation",
        "最终评分以格式规则评分为主，AI语言评分仅作参考，不会拉低最终评分。",
    )
    needs_manual_review_count = len(manual_review_items)
    score_delta = int(after_analysis["report"]["score"]) - int(before_analysis["report"]["score"])
    format_diff_summary = {
        "before_score": int(before_analysis["report"]["score"]),
        "after_score": int(after_analysis["report"]["score"]),
        "score_delta": score_delta,
        "auto_fix_count": auto_fix_count,
        "changed_dimension_count": len(changed_dimensions),
        "needs_manual_review_count": needs_manual_review_count,
        "format_change_count": len(format_log),
        "language_change_count": language_changes,
        "summary": build_format_diff_summary(score_delta, changed_dimensions, auto_fix_count, needs_manual_review_count),
    }
    return {
        "summary": f"Agent 完成 {auto_fix_count} 项自动处理，最终评分 {after_analysis['report']['score']}。",
        "fixed_issues": [
            "统一页面边距、正文样式、标题层级和段落间距。",
            "完成本地格式修复和重复风险预检。",
            "根据当前模式完成语言审校或跳过 AI 增强。",
        ],
        "before_after": comparisons,
        "format_diff_summary": format_diff_summary,
        "changed_dimensions": changed_dimensions,
        "score_delta_by_dimension": score_delta_by_dimension,
        "auto_fix_count": auto_fix_count,
        "needs_manual_review_count": needs_manual_review_count,
        "change_counts": {
            "format_changes": len(format_log),
            "language_changes": language_changes,
            "total": auto_fix_count,
        },
        "unresolved_issues": unresolved_issues,
        "manual_review_items": manual_review_items,
        "risk_summary": risk_summary,
        "warning_items": warning_items,
        "info_items": info_items,
        "score_explanation": score_explanation,
        "template_used": template_display_name or (template_path.name if template_path else None),
    }


def collect_unresolved(after_analysis: dict[str, Any]) -> list[str]:
    issues = []
    for item in after_analysis["report"]["breakdown"]:
        if item["score"] < 90:
            item_issues = item["issues"] or ["仍建议人工复核。"]
            issues.extend([f"{item['label']}：{issue}" for issue in item_issues])
    return issues or ["未发现高风险未修复项，但最终提交前仍建议人工复查。"]


def collect_check_risk_items(after_analysis: dict[str, Any]) -> list[dict[str, str]]:
    reference_items = after_analysis.get("reference_check", {}).get("risk_items", [])
    figure_table_items = after_analysis.get("figure_table_check", {}).get("risk_items", [])
    return [*reference_items, *figure_table_items]


def build_manual_review_items(risk_items: list[dict[str, str]]) -> list[str]:
    return unique_messages(item for item in risk_items if item.get("level") in REVIEW_RISK_LEVELS)


def build_warning_items(
    after_analysis: dict[str, Any],
    unresolved_issues: list[str],
    risk_items: list[dict[str, str]],
) -> list[str]:
    recommendations = after_analysis["report"].get("recommendations", [])
    review_risk_messages = [item.get("message", "") for item in risk_items if item.get("level") in REVIEW_RISK_LEVELS]
    score_warnings = [
        issue
        for issue in unresolved_issues
        if "未发现高风险未修复项" not in issue and not any(message and message in issue for message in review_risk_messages)
    ]
    risk_warnings = unique_messages(item for item in risk_items if item.get("level") == "warning")
    return list(dict.fromkeys([*score_warnings, *risk_warnings, *recommendations]))


def build_info_items(risk_items: list[dict[str, str]]) -> list[str]:
    return unique_messages(item for item in risk_items if item.get("level") == "info")


def build_report_risk_summary(risk_items: list[dict[str, str]]) -> dict[str, int]:
    return {level: sum(1 for item in risk_items if item.get("level") == level) for level in RISK_LEVELS}


def unique_messages(items) -> list[str]:
    return list(dict.fromkeys(item.get("message", "") for item in items if item.get("message")))


def build_format_diff_summary(
    score_delta: int,
    changed_dimensions: list[dict[str, Any]],
    auto_fix_count: int,
    needs_manual_review_count: int,
) -> str:
    if changed_dimensions:
        dimension_names = "、".join(item["label"] for item in changed_dimensions[:4])
        if len(changed_dimensions) > 4:
            dimension_names += "等"
    else:
        dimension_names = "各评分维度"

    if score_delta > 0:
        score_text = f"评分提升 {score_delta} 分"
    elif score_delta < 0:
        score_text = f"评分变化 {score_delta} 分，建议重点复核"
    else:
        score_text = "评分保持稳定"

    return f"{score_text}；{dimension_names}发生变化；完成 {auto_fix_count} 项自动处理，仍有 {needs_manual_review_count} 项建议人工复查。"
