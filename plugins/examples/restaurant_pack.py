"""Restaurant industry pack — an example of a realistic SYJ LeadForge plugin.

Bumps the category weight for restaurants and related food-service
categories, checks for online-ordering/reservation/menu signals on the
website, and recommends adding them when missing.
"""
from __future__ import annotations

from leadforge.plugins import AuditCheckContext, PluginRegistry, ScoreAdjustment, ScoringContext

RESTAURANT_CATEGORIES = {"restaurant", "cafe", "bakery", "food truck", "catering"}

ORDERING_PLATFORM_MARKERS = (
    "zomato", "swiggy", "ubereats", "uber eats", "doordash", "grubhub",
    "opentable", "resy", "toasttab", "toast.com",
)
MENU_MARKERS = ("menu", "our-menu", "our menu")


def register(registry: PluginRegistry) -> None:
    for category in RESTAURANT_CATEGORIES:
        registry.add_category_weight(category, 1.15)

    registry.add_audit_check(check_ordering_and_menu)
    registry.add_scoring_rule(recommend_online_ordering)


def _is_restaurant_category(category: str) -> bool:
    return category.strip().lower() in RESTAURANT_CATEGORIES


def check_ordering_and_menu(context: AuditCheckContext) -> list[str]:
    if context.business is None or not _is_restaurant_category(context.business.category):
        return []
    if not context.html:
        return []

    html_lower = context.html.lower()
    issues = []

    if not any(marker in html_lower for marker in MENU_MARKERS):
        issues.append("No menu page or menu link detected")

    if not any(marker in html_lower for marker in ORDERING_PLATFORM_MARKERS):
        issues.append("No online ordering or reservation platform detected")

    return issues


def recommend_online_ordering(context: ScoringContext) -> ScoreAdjustment:
    if not _is_restaurant_category(context.business.category):
        return ScoreAdjustment()

    if context.audit is None:
        return ScoreAdjustment()

    missing_ordering = "No online ordering or reservation platform detected" in context.audit.issues
    missing_menu = "No menu page or menu link detected" in context.audit.issues

    if not missing_ordering and not missing_menu:
        return ScoreAdjustment()

    reasons = []
    delta = 0
    if missing_menu:
        reasons.append("Restaurant pack: no menu found on the website — easy, high-value addition")
        delta += 5
    if missing_ordering:
        reasons.append("Restaurant pack: recommend adding online ordering or a reservation link")
        delta += 8

    return ScoreAdjustment(delta=delta, reasons=reasons)
