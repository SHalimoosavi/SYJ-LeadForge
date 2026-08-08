"""Pydantic schemas for the SYJ LeadForge API.

These mirror the dataclasses in `leadforge.models` field-for-field so
that responses are a faithful, typed representation of the same data
the CLI works with — no parallel data model to keep in sync.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class BusinessCreate(BaseModel):
    name: str
    category: str = ""
    city: str = ""
    state: str = ""
    country: str = ""
    phone: str = ""
    website: str = ""
    rating: float = 0.0
    review_count: int = 0
    notes: str = ""


class BusinessOut(BusinessCreate):
    id: int


class AuditOut(BaseModel):
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
    performance_score: int = 0
    design_score: int = 0
    seo_score: int = 0
    accessibility_score: int = 0
    trust_score: int = 0
    overall_score: int = 0
    issues: list[str] = Field(default_factory=list)


class ScoreOut(BaseModel):
    business_id: int
    opportunity_score: int = 0
    stars: int = 0
    estimated_value_low: int = 0
    estimated_value_high: int = 0
    currency: str = "INR"
    tier: str = "Low"
    reasons: list[str] = Field(default_factory=list)


class ImportResult(BaseModel):
    imported: int
    businesses: list[BusinessOut]


class AuditRunResult(BaseModel):
    audited: int
    results: list[AuditOut]


class ScoreRunResult(BaseModel):
    scored: int
    results: list[ScoreOut]


class LeadOut(BaseModel):
    id: int
    name: str
    category: str = ""
    city: str = ""
    state: str = ""
    country: str = ""
    phone: str = ""
    website: str = ""
    rating: float = 0.0
    review_count: int = 0
    score: ScoreOut | None = None
    audit: AuditOut | None = None


class StatsOut(BaseModel):
    total_businesses: int
    audited: int
    scored: int
    tier_breakdown: dict[str, int]
    average_score: float


class ErrorDetail(BaseModel):
    detail: str
