"""Legal industry pack — a second example SYJ LeadForge plugin.

Bumps the category weight for legal categories (law firms typically
justify bigger project budgets and higher-touch relationships), and
checks for practice-area and attorney-bio content, which is usually the
single highest-value addition to a small law firm's website.
"""
from __future__ import annotations

from leadforge.plugins import AuditCheckContext, PluginRegistry, ScoreAdjustment, ScoringContext

LEGAL_CATEGORIES = {"law firm", "chartered accountant", "notary"}

PRACTICE_AREA_MARKERS = ("practice area", "practice-area", "areas of practice", "our services")
ATTORNEY_BIO_MARKERS = ("attorney", "advocate", "partner", "associate", "our team", "meet the team")


def register(registry: PluginRegistry) -> None:
    registry.add_category_weight("law firm", 1.5)
    registry.add_category_weight("chartered accountant", 1.35)

    registry.add_audit_check(check_practice_areas_and_bios)
    registry.add_scoring_rule(recommend_practice_area_page)


def _is_legal_category(category: str) -> bool:
    return category.strip().lower() in LEGAL_CATEGORIES


def check_practice_areas_and_bios(context: AuditCheckContext) -> list[str]:
    if context.business is None or not _is_legal_category(context.business.category):
        return []
    if not context.html:
        return []

    html_lower = context.html.lower()
    issues = []

    if not any(marker in html_lower for marker in PRACTICE_AREA_MARKERS):
        issues.append("No clear practice areas / services section detected")

    if not any(marker in html_lower for marker in ATTORNEY_BIO_MARKERS):
        issues.append("No attorney bios or team page detected")

    return issues


def recommend_practice_area_page(context: ScoringContext) -> ScoreAdjustment:
    if not _is_legal_category(context.business.category):
        return ScoreAdjustment()
    if context.audit is None:
        return ScoreAdjustment()

    reasons = []
    delta = 0

    if "No clear practice areas / services section detected" in context.audit.issues:
        reasons.append("Legal pack: recommend a clear practice-areas page — the #1 conversion driver for law firm sites")
        delta += 8

    if "No attorney bios or team page detected" in context.audit.issues:
        reasons.append("Legal pack: recommend adding attorney bios — builds trust for a high-consideration purchase")
        delta += 5

    return ScoreAdjustment(delta=delta, reasons=reasons)
