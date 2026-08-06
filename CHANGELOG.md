# Changelog

All notable changes to this project are documented here. Format loosely follows [Keep a Changelog](https://keepachangelog.com/).

## [0.1.0] - 2026-08-06

### Added
- Initial CLI: `leadforge import|audit|score|export|list|doctor`
- CSV importer with flexible column-name aliasing and validation
- Website auditor: HTTPS/SSL validation, viewport/title/meta/H1/favicon detection, alt-text coverage, WhatsApp/contact-link detection, redirect and response-time tracking
- Transparent, explainable 0–100 opportunity scoring with configurable category weights and excluded categories
- CSV, JSON, and Markdown exporters with tier/min-score filters
- SQLite local storage, zero external services required
- Test suite (pytest, fully mocked/offline) + GitHub Actions CI across Linux/macOS/Windows and Python 3.10–3.12
- MIT License, README, CONTRIBUTING, SECURITY, CODE_OF_CONDUCT, architecture & roadmap docs
