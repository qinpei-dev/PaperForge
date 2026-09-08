from __future__ import annotations

import hashlib
from typing import Any


def make_issue_id(domain: str, locator: dict[str, Any], issue_type: str, original: str, proposed: str) -> str:
    payload = "|".join([domain, str(locator), issue_type, original, proposed])
    return f"{domain[:3]}-{hashlib.sha1(payload.encode('utf-8')).hexdigest()[:12]}"


def aggregate_review_evidence(
    *,
    formatting_changes: list[dict[str, Any]] | None = None,
    content_review: dict[str, Any] | None = None,
) -> dict[str, Any]:
    evidence: list[dict[str, Any]] = []
    for change in formatting_changes or []:
        target = change.get("target") or {}
        locator = target.get("locator") or target.get("paragraph_index") or target
        original = change.get("before")
        proposed = change.get("expected", change.get("after"))
        item = _evidence_item("formatting", locator, change.get("rule_type", change.get("action", "formatting")), original, proposed, change.get("after"), change.get("verification_status"), change.get("status", "applied"), change.get("verification_evidence"), change.get("executor", "formatter"), change.get("reason", "格式规则要求"), change.get("confidence", 1.0), change.get("risk_level", "low"), change.get("action", "auto_fix"), change.get("requires_user_confirmation", False))
        evidence.append(item)

    review = content_review or {}
    for issue in review.get("issues", []):
        policy = issue.get("action_policy")
        if policy == "AUTO_FIX" or issue.get("status") == "accepted":
            continue
        locator = issue.get("locator") or {"kind": "paragraph", "paragraph_index": issue.get("paragraph_index")}
        status = "suggested" if policy == "SUGGEST_ONLY" else "hitl"
        evidence.append(_evidence_item("content", locator, issue.get("issue_type", "content"), issue.get("original_text"), issue.get("suggested_text"), None, issue.get("verification_status", "original_unchanged"), status, issue.get("verification_evidence"), issue.get("source", "local"), issue.get("reason"), issue.get("confidence"), issue.get("risk_level"), "suggestion" if policy == "SUGGEST_ONLY" else "hitl", policy == "HITL_REQUIRED"))
    for change in review.get("provenance", {}).get("auto_fixes", []):
        locator = change.get("locator") or {"kind": "paragraph", "paragraph_index": change.get("paragraph_index")}
        evidence.append(_evidence_item("content", locator, change.get("issue_type", "content"), change.get("before"), change.get("after"), change.get("after"), change.get("verification_status"), "applied", change.get("verification_evidence"), change.get("source", "local"), change.get("reason"), change.get("confidence"), change.get("risk_level", "low"), "auto_fix", False))
    for change in review.get("provenance", {}).get("accepted", []):
        locator = change.get("locator") or {"kind": "paragraph", "paragraph_index": change.get("paragraph_index")}
        evidence.append(_evidence_item("content", locator, change.get("issue_type", "content"), change.get("before"), change.get("after"), change.get("after"), change.get("verification_status"), "accepted", change.get("verification_evidence"), change.get("source", "user_confirmed"), change.get("reason"), change.get("confidence"), change.get("risk_level", "warning"), "accepted_by_user", False))

    formatting = [item for item in evidence if item["issue_domain"] == "formatting"]
    content = [item for item in evidence if item["issue_domain"] == "content"]
    pending = [item for item in content if item["status"] in {"suggested", "hitl"}]
    return {
        "change_evidence": evidence,
        "pending_actions": pending,
        "review_summary": {
            "formatting": _counts(formatting, include_accepted=False),
            "content": _counts(content, include_accepted=True),
            "overall": {
                "total_detected": len(evidence),
                "total_verified_changes": sum(item["verification_status"] == "verified" for item in evidence),
                "total_pending_user_actions": len([item for item in pending if item["status"] == "suggested"]),
                "total_hitl": len([item for item in pending if item["status"] == "hitl"]),
                "verification_failures": sum(item["verification_status"] == "failed" for item in evidence),
            },
        },
    }


def content_score_summary(review: dict[str, Any] | None) -> dict[str, Any]:
    review = review or {}
    issues = review.get("issues", [])
    detected = len(issues)
    auto = [x for x in review.get("provenance", {}).get("auto_fixes", []) if x.get("verification_status") == "verified"]
    accepted = [x for x in review.get("provenance", {}).get("accepted", []) if x.get("verification_status") == "verified"]
    suggestions = [x for x in issues if x.get("action_policy") == "SUGGEST_ONLY"]
    hitl = [x for x in issues if x.get("action_policy") == "HITL_REQUIRED"]
    failures = [x for x in review.get("provenance", {}).get("auto_fixes", []) if x.get("verification_status") == "failed"]
    unresolved = len(suggestions) + len(hitl) + len(failures)
    before = max(0, 100 - detected * 5)
    after = max(0, 100 - unresolved * 5)
    return {"before_content_score": before, "after_content_score": after, "delta": after - before, "verified_changes_count": len(auto) + len(accepted), "detected_issues": detected, "auto_fixed_issues": len(auto), "accepted_suggestions": len(accepted), "unresolved_issue_count": unresolved, "suggested_count": len(suggestions), "hitl_count": len(hitl), "score_delta_reasons": ["仅已重读验证的自动修改或用户采纳修改计入改善", "未采纳建议和未处理 HITL 保留为未解决问题", "验证失败不产生评分改善"]}


def _evidence_item(domain, locator, issue_type, original, proposed, actual_after, verification_status, status, evidence, source, reason, confidence, risk_level, action, requires_user_confirmation):
    return {"issue_id": make_issue_id(domain, locator if isinstance(locator, dict) else {"value": locator}, str(issue_type), str(original or ""), str(proposed or "")), "issue_domain": domain, "locator": locator, "issue_type": issue_type, "original": original, "proposed": proposed, "expected": proposed, "actual_after": actual_after, "reason": reason, "evidence": evidence or {}, "confidence": confidence, "risk_level": risk_level, "source": source, "action": action, "status": status, "verification_status": verification_status or "not_run", "requires_user_confirmation": requires_user_confirmation}


def _counts(items, include_accepted):
    return {"detected": len(items), "auto_fixed": len([x for x in items if x["action"] == "auto_fix"]), "verified": len([x for x in items if x["verification_status"] == "verified"]), "unresolved": len([x for x in items if x["status"] in {"suggested", "hitl"} or x["verification_status"] == "failed"]), "hitl": len([x for x in items if x["status"] == "hitl"]), **({"accepted": len([x for x in items if x["action"] == "accepted_by_user"])} if include_accepted else {})}
