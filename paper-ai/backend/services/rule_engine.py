from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any

from .template_extractor import DEFAULT_TEMPLATE_PROFILE


class RuleSource(StrEnum):
    TEMPLATE = "TEMPLATE"
    DEFAULT = "DEFAULT"
    USER_GUIDELINE = "USER_GUIDELINE"
    INFERRED = "INFERRED"


@dataclass(frozen=True)
class Rule:
    id: str
    target: str
    property: str
    expected: Any
    source: RuleSource
    evidence: str
    confidence: float
    risk_level: str
    auto_fixable: bool

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["source"] = self.source.value
        return data


def normalize_rules(template_profile: dict[str, Any] | None, *, template_uploaded: bool = False) -> list[Rule]:
    """Normalize existing template extraction output without altering extraction.

    A template profile may contain fallback defaults. Warnings determine whether
    a field may honestly claim TEMPLATE provenance; otherwise it is emitted as
    a DEFAULT rule with explicit fallback evidence.
    """
    profile = template_profile or DEFAULT_TEMPLATE_PROFILE
    warnings = [str(item) for item in profile.get("warnings") or []]
    rules: list[Rule] = []
    for side, expected in (profile.get("margins") or {}).items():
        rules.append(make_rule("page", f"margin_{side}_cm", expected, profile, warnings, "margins", template_uploaded, "low", True))
    for property_name, expected in (profile.get("normal") or {}).items():
        rules.append(make_rule("body", property_name, expected, profile, warnings, "normal", template_uploaded, "low", True))
    for property_name, expected in (profile.get("body") or {}).items():
        rules.append(make_rule("body", property_name, expected, profile, warnings, "body", template_uploaded, "low", True))
    for style_name, style_profile in (profile.get("heading") or {}).items():
        for property_name, expected in style_profile.items():
            # Formatting a reliably style-identified heading is local and reversible;
            # Planner still requires a high-confidence paragraph locator.
            rules.append(make_rule(f"heading:{style_name}", property_name, expected, profile, warnings, "heading", template_uploaded, "low", True))

    # Caption text is deliberately never changed.  These generic rules only
    # normalize low-risk presentation properties on captions parsed by the
    # existing deterministic figure/table number recognizer.
    for kind in ("figure", "table"):
        for property_name, expected in {"font_name": "宋体", "font_size": 10.5, "alignment": 1, "line_spacing": 1.0, "bold": False}.items():
            rules.append(Rule(f"caption-{kind}-{property_name}", f"caption:{kind}", property_name, expected, RuleSource.DEFAULT, "default_caption_profile", 0.72, "low", True))

    # These rules are explicitly inferred from current validation semantics;
    # they are review rules, not claims about an uploaded template.
    rules.extend(
        [
            Rule("inferred-reference-numbering", "references", "numbering_integrity", "continuous_unique", RuleSource.INFERRED, "docx_analyzer.reference_check", 0.82, "high_risk", False),
            Rule("inferred-figure-table-numbering", "figures_tables", "numbering_integrity", "continuous_unique", RuleSource.INFERRED, "docx_analyzer.figure_table_check", 0.82, "high_risk", False),
        ]
    )
    return rules


def make_rule(
    target: str,
    property_name: str,
    expected: Any,
    profile: dict[str, Any],
    warnings: list[str],
    group: str,
    template_uploaded: bool,
    risk_level: str,
    auto_fixable: bool,
) -> Rule:
    fallback = has_group_warning(warnings, group)
    source = RuleSource.TEMPLATE if template_uploaded and not fallback else RuleSource.DEFAULT
    origin = f"template_profile.{group}.{property_name}" if source is RuleSource.TEMPLATE else f"default_profile.{group}.{property_name}"
    if fallback:
        origin += " (template extraction fallback)"
    return Rule(
        id=f"{target.replace(':', '-')}-{property_name}",
        target=target,
        property=property_name,
        expected=expected,
        source=source,
        evidence=origin,
        confidence=0.9 if source is RuleSource.TEMPLATE else 0.72,
        risk_level=risk_level,
        auto_fixable=auto_fixable,
    )


def has_group_warning(warnings: list[str], group: str) -> bool:
    markers = {
        "margins": ("页边距",),
        "normal": ("正文样式",),
        "body": ("正文段落",),
        "heading": ("标题样式",),
    }
    return any(any(marker in warning for marker in markers[group]) for warning in warnings)
