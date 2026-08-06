"""Core data models used across SYJ LeadForge."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field


@dataclass
class Business:
    """A single business record, imported from a user-supplied CSV.

    SYJ LeadForge never scrapes or auto-collects personal data. Records
    come from CSVs the user has legitimately compiled (e.g. exported
    from their own CRM, a public directory export they are entitled to
    use, or manual research) or from official APIs they have configured.
    """

    id: int | None = None
    name: str = ""
    category: str = ""
    city: str = ""
    state: str = ""
    country: str = ""
    phone: str = ""
    website: str = ""
    rating: float = 0.0
    review_count: int = 0
    notes: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AuditResult:
    """Result of auditing a single business website."""

    business_id: int
    url: str
    reachable: bool = False
    status_code: int | None = None
    https: bool = False
    response_time_ms: float | None = None
    redirect_count: int = 0
    has_title: bool = False
    has_meta_description: bool = False
    has_viewport_meta: bool = False
    has_favicon: bool = False
    has_h1: bool = False
    image_count: int = 0
    images_missing_alt: int = 0
    has_whatsapp_link: bool = False
    has_contact_info: bool = False
    has_ssl_valid: bool = False
    html_lang_present: bool = False
    error: str = ""

    # Sub-scores, 0-100
    performance_score: int = 0
    design_score: int = 0
    seo_score: int = 0
    accessibility_score: int = 0
    trust_score: int = 0
    overall_score: int = 0

    issues: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


@dataclass
class LeadScore:
    """Opportunity score for a business, combining audit + business signals."""

    business_id: int
    opportunity_score: int = 0
    stars: int = 0
    estimated_value_low: int = 0
    estimated_value_high: int = 0
    currency: str = "INR"
    tier: str = "Low"
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)
