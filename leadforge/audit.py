"""Website detection and audit.

Fetches a single page (the business's own homepage) via a normal HTTP GET,
exactly as a browser or search engine would, and inspects publicly served
HTML for quality signals. This module never attempts to bypass
authentication, robots.txt-disallowed paths, rate limits, or any other
access control.
"""
from __future__ import annotations

import socket
import ssl
import time
from html.parser import HTMLParser
from urllib.parse import urlparse

import requests

from .config import Settings
from .models import AuditResult


class _PageAnalyzer(HTMLParser):
    """Minimal, dependency-free HTML analyzer for audit signals."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.has_title = False
        self.has_meta_description = False
        self.has_viewport_meta = False
        self.has_favicon = False
        self.has_h1 = False
        self.image_count = 0
        self.images_missing_alt = 0
        self.html_lang_present = False
        self._link_hrefs: list[str] = []
        self._in_title = False
        self._title_text = ""

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        tag = tag.lower()
        if tag == "html" and attrs_dict.get("lang"):
            self.html_lang_present = True
        elif tag == "title":
            self._in_title = True
        elif tag == "meta":
            name = (attrs_dict.get("name") or "").lower()
            if name == "description" and attrs_dict.get("content"):
                self.has_meta_description = True
            if name == "viewport" and attrs_dict.get("content"):
                self.has_viewport_meta = True
        elif tag == "link":
            rel = (attrs_dict.get("rel") or "").lower()
            if "icon" in rel:
                self.has_favicon = True
        elif tag == "h1":
            self.has_h1 = True
        elif tag == "img":
            self.image_count += 1
            alt = attrs_dict.get("alt")
            if alt is None or not alt.strip():
                self.images_missing_alt += 1
        elif tag == "a":
            href = attrs_dict.get("href") or ""
            self._link_hrefs.append(href.lower())

    def handle_endtag(self, tag):
        if tag.lower() == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title and data.strip():
            self._title_text += data.strip()
            self.has_title = True

    @property
    def has_whatsapp_link(self) -> bool:
        return any("wa.me" in h or "api.whatsapp.com" in h for h in self._link_hrefs)

    @property
    def has_contact_info(self) -> bool:
        return any(h.startswith(("mailto:", "tel:")) or "contact" in h for h in self._link_hrefs)


def _check_tls(hostname: str, timeout: float) -> bool:
    """Return True if a valid TLS handshake succeeds on port 443."""
    try:
        ctx = ssl.create_default_context()
        with (
            socket.create_connection((hostname, 443), timeout=timeout) as sock,
            ctx.wrap_socket(sock, server_hostname=hostname),
        ):
            return True
    except Exception:
        return False


def audit_website(business_id: int, url: str, settings: Settings) -> AuditResult:
    """Fetch and analyze a single business website. Never raises; failures
    are captured in the returned AuditResult so a batch run can continue."""
    result = AuditResult(business_id=business_id, url=url)

    if not url:
        result.error = "No website URL provided"
        return result

    parsed = urlparse(url)
    hostname = parsed.hostname or ""

    headers = {"User-Agent": settings.user_agent}
    start = time.monotonic()
    try:
        resp = requests.get(
            url,
            headers=headers,
            timeout=settings.request_timeout,
            allow_redirects=True,
        )
        elapsed_ms = (time.monotonic() - start) * 1000
        result.reachable = True
        result.status_code = resp.status_code
        result.response_time_ms = round(elapsed_ms, 1)
        result.redirect_count = len(resp.history)
        result.https = resp.url.startswith("https://")

        if resp.status_code >= 400:
            result.issues.append(f"Website returned HTTP {resp.status_code}")

        analyzer = _PageAnalyzer()
        try:
            analyzer.feed(resp.text)
        except Exception:
            pass

        result.has_title = analyzer.has_title
        result.has_meta_description = analyzer.has_meta_description
        result.has_viewport_meta = analyzer.has_viewport_meta
        result.has_favicon = analyzer.has_favicon
        result.has_h1 = analyzer.has_h1
        result.image_count = analyzer.image_count
        result.images_missing_alt = analyzer.images_missing_alt
        result.has_whatsapp_link = analyzer.has_whatsapp_link
        result.has_contact_info = analyzer.has_contact_info
        result.html_lang_present = analyzer.html_lang_present

    except requests.exceptions.SSLError as exc:
        result.reachable = False
        result.error = f"SSL error: {exc}"
    except requests.exceptions.Timeout:
        result.reachable = False
        result.error = "Request timed out"
    except requests.exceptions.RequestException as exc:
        result.reachable = False
        result.error = f"Request failed: {exc}"
    except Exception as exc:  # defensive: never let one bad site abort a batch run
        result.reachable = False
        result.error = f"Unexpected error: {exc}"

    if hostname:
        result.has_ssl_valid = _check_tls(hostname, settings.request_timeout)

    _score_result(result)
    return result


def _score_result(result: AuditResult) -> None:
    """Derive 0-100 sub-scores and an overall score from raw signals."""
    if not result.reachable:
        result.issues.append("Website is unreachable or down")
        result.performance_score = 0
        result.design_score = 0
        result.seo_score = 0
        result.accessibility_score = 0
        result.trust_score = 0
        result.overall_score = 0
        return

    # Performance: reward fast, non-error, low-redirect responses.
    perf = 100
    if result.response_time_ms is not None:
        if result.response_time_ms > 3000:
            perf -= 40
            result.issues.append("Slow server response (>3s)")
        elif result.response_time_ms > 1500:
            perf -= 20
    if result.redirect_count > 2:
        perf -= 15
        result.issues.append("Excessive redirects")
    if result.status_code and result.status_code >= 400:
        perf = 0
    result.performance_score = max(0, min(100, perf))

    # Design: viewport + favicon + reasonable image usage as rough proxies.
    design = 40
    if result.has_viewport_meta:
        design += 30
    else:
        result.issues.append("Missing responsive viewport meta tag (poor mobile experience)")
    if result.has_favicon:
        design += 15
    if result.image_count > 0:
        design += 15
    result.design_score = max(0, min(100, design))

    # SEO: title, meta description, h1, https.
    seo = 0
    if result.has_title:
        seo += 30
    else:
        result.issues.append("Missing page <title>")
    if result.has_meta_description:
        seo += 30
    else:
        result.issues.append("Missing meta description")
    if result.has_h1:
        seo += 20
    else:
        result.issues.append("Missing H1 heading")
    if result.https:
        seo += 20
    else:
        result.issues.append("Not served over HTTPS")
    result.seo_score = max(0, min(100, seo))

    # Accessibility: alt text coverage + lang attribute.
    access = 50 if result.html_lang_present else 20
    if not result.html_lang_present:
        result.issues.append("Missing lang attribute on <html>")
    if result.image_count > 0:
        alt_ratio = 1 - (result.images_missing_alt / result.image_count)
        access += int(alt_ratio * 50)
        if alt_ratio < 0.5:
            result.issues.append("Most images are missing alt text")
    else:
        access += 30
    result.accessibility_score = max(0, min(100, access))

    # Trust: valid SSL cert, https, contact info.
    trust = 0
    if result.has_ssl_valid:
        trust += 40
    else:
        result.issues.append("SSL certificate could not be validated")
    if result.https:
        trust += 20
    if result.has_contact_info:
        trust += 20
    else:
        result.issues.append("No visible contact info (mailto/tel/contact link)")
    if result.has_whatsapp_link:
        trust += 20
    else:
        result.issues.append("No WhatsApp contact link detected")
    result.trust_score = max(0, min(100, trust))

    result.overall_score = round(
        result.performance_score * 0.2
        + result.design_score * 0.2
        + result.seo_score * 0.25
        + result.accessibility_score * 0.15
        + result.trust_score * 0.2
    )
