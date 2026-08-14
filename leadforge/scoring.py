"""Opportunity scoring: combines business signals + website audit into a
single 0-100 lead score, star rating, and rough project value estimate.

This is a transparent, rule-based scorer (not a black box) so that
freelancers can trust and tune it. It intentionally never contacts any
third-party service.

Plugins (see `leadforge.plugins`) can add or override category weights,
add excluded categories, and register scoring rules that nudge the
final score with their own point delta and reason strings — see
`docs/PLUGIN_GUIDE.md`.
"""
from __future__ import annotations

from .config import DEFAULT_CATEGORY_WEIGHTS, DEFAULT_EXCLUDED_CATEGORIES
from .models import AuditResult, Business, LeadScore
from .plugins import PluginRegistry, ScoringContext, get_registry

# Sentinel distinguishing "caller didn't specify a registry" (auto-load
# the global one) from "caller explicitly passed registry=None" (use no
# registry at all — plugins fully disabled). A plain `None` default
# can't express that distinction on its own.
_REGISTRY_UNSET = object()


def is_excluded_category(
    category: str,
    excluded: set[str] | None = None,
    *,
    registry: PluginRegistry | None = _REGISTRY_UNSET,  # type: ignore[assignment]
) -> bool:
    """True if `category` should always score 0.

    If `excluded` is explicitly passed, it's used as-is (useful for
    tests or callers that want full control). Otherwise this is the
    built-in default list unioned with the plugin registry's additions
    — the global loaded registry by default, or none at all if the
    caller explicitly passes `registry=None`.
    """
    if excluded is None:
        if registry is _REGISTRY_UNSET:
            registry = get_registry()
        extra = registry.excluded_categories if registry is not None else set()
        excluded = DEFAULT_EXCLUDED_CATEGORIES | extra
    return category.strip().lower() in excluded


def _category_weight(
    category: str,
    weights: dict | None = None,
    *,
    registry: PluginRegistry | None = _REGISTRY_UNSET,  # type: ignore[assignment]
) -> float:
    if weights is None:
        if registry is _REGISTRY_UNSET:
            registry = get_registry()
        extra = registry.category_weights if registry is not None else {}
        weights = {**DEFAULT_CATEGORY_WEIGHTS, **extra}
    return weights.get(category.strip().lower(), 1.0)


def _tier_for_score(score: int) -> str:
    if score >= 80:
        return "Very High"
    if score >= 60:
        return "High"
    if score >= 40:
        return "Medium"
    if score >= 20:
        return "Low"
    return "Very Low"


def score_business(
    business: Business,
    audit: AuditResult | None = None,
    excluded_categories: set[str] | None = None,
    category_weights: dict | None = None,
    *,
    use_plugins: bool = True,
) -> LeadScore:
    """Compute an opportunity score for a business.

    - No website at all is generally the single biggest opportunity signal.
    - A website that exists but scores poorly on the audit is also a strong
      opportunity, just slightly weaker than "no website" since there is
      more inertia to overcome ("it already works for them").
    - Reputation (rating x review_count, log-dampened) scales the estimate:
      a well-reviewed business can typically justify a bigger budget.

    If `use_plugins` is True (the default), registered scoring rules run
    after the core computation below: their point deltas are summed, the
    final score is re-clamped to 0-100, and stars/tier/estimated value are
    recomputed from that final number, so a business's tier always matches
    its own score. Pass `use_plugins=False` for a deterministic, plugin-free
    result (mainly useful for testing the core scorer in isolation).
    """
    reasons: list[str] = []
    score = LeadScore(business_id=business.id or 0)
    registry = get_registry() if use_plugins else None

    if is_excluded_category(business.category, excluded_categories, registry=registry):
        score.opportunity_score = 0
        score.stars = 0
        score.tier = "Excluded"
        score.reasons.append(f"Category '{business.category}' is excluded by default configuration")
        return score

    base = 0.0

    if not business.website:
        base += 55
        reasons.append("No website found — strong opportunity")
    elif audit is not None:
        if not audit.reachable:
            base += 50
            reasons.append("Existing website is unreachable/down")
        else:
            website_gap = max(0, 100 - audit.overall_score)
            base += website_gap * 0.5
            if audit.overall_score < 40:
                reasons.append(f"Existing website scores poorly ({audit.overall_score}/100)")
            elif audit.overall_score < 70:
                reasons.append(f"Existing website has room to improve ({audit.overall_score}/100)")
            else:
                reasons.append(f"Existing website is already solid ({audit.overall_score}/100)")
    else:
        base += 20
        reasons.append("Website present but not yet audited")

    # Reputation signal: businesses with strong reviews can usually
    # justify a bigger project, and are more likely to convert as clients.
    reputation_bonus = 0.0
    if business.review_count > 0 and business.rating > 0:
        import math

        reputation_bonus = min(20, math.log2(business.review_count + 1) * 2) * (business.rating / 5)
        if business.rating >= 4.3 and business.review_count >= 25:
            reasons.append(f"Strong reputation ({business.rating}★, {business.review_count} reviews)")
    base += reputation_bonus

    weight = _category_weight(business.category, category_weights, registry=registry)
    weighted = base * weight
    if weight > 1.0:
        reasons.append(f"High-value category multiplier ({weight}x)")

    final = max(0, min(100, round(weighted)))

    if registry is not None and registry.scoring_rules:
        total_delta = 0
        for plugin_name, rule in registry.scoring_rules:
            try:
                adjustment = rule(ScoringContext(business=business, audit=audit, score=score))
            except Exception as exc:
                import logging

                logging.getLogger("leadforge.plugins").warning(
                    "Scoring rule from plugin '%s' failed: %s", plugin_name, exc
                )
                continue
            if adjustment is None:
                continue
            total_delta += adjustment.delta
            reasons.extend(adjustment.reasons)
        final = max(0, min(100, final + total_delta))

    score.opportunity_score = final
    score.stars = max(1, min(5, round(final / 20)))
    score.tier = _tier_for_score(final)

    low, high = _estimate_value(final, weight)
    score.estimated_value_low = low
    score.estimated_value_high = high
    score.reasons = reasons
    return score


def _estimate_value(opportunity_score: int, category_weight: float) -> tuple[int, int]:
    """Rough illustrative INR project-value band. Category weight is the
    main lever plugins have for "suggested pricing" — an industry-pack
    plugin that sets a higher weight for its categories naturally widens
    the suggested range too, without needing a separate pricing hook."""
    base_low = 8_000
    base_high = 25_000
    scale = 1 + (opportunity_score / 100) * 3  # up to 4x at score 100
    scale *= category_weight
    low = int(round((base_low * scale) / 500) * 500)
    high = int(round((base_high * scale) / 500) * 500)
    return low, high
