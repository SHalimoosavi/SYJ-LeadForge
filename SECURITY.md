# Security Policy

## Reporting a vulnerability

If you discover a security vulnerability in SYJ LeadForge, please open a GitHub issue marked `security` or contact the maintainers privately if the issue is sensitive (e.g. could enable abuse of the audit feature against third parties). Please do not include exploit details in a public issue until a fix is available.

## Scope & principles

SYJ LeadForge is designed to be safe by default:

- **No telemetry, no hidden analytics, no tracking.**
- **No API keys or secrets are ever hardcoded** — configuration is via environment variables only (see `leadforge/config.py`).
- **The audit module makes a single, standard HTTP GET** per business website, with a configurable timeout, a descriptive User-Agent identifying the tool, and a configurable delay between requests to avoid anything resembling a denial-of-service pattern. It does not crawl, does not follow internal links, and does not attempt to bypass authentication, CAPTCHAs, or rate limiting.
- **No personal data is collected automatically.** All business data comes from CSVs the user supplies themselves.

## Supported versions

| Version | Supported |
|---|---|
| 0.1.x   | ✅ |
