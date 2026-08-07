# Changelog

All notable changes to this project are documented here. Format loosely follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Fixed
- **Windows console crash (`UnicodeEncodeError`)** — the CLI printed Unicode symbols (`★`, `—`) directly, which crashed on Windows `cmd.exe`/legacy PowerShell consoles reporting `cp1252`/`cp437` encoding. Added `leadforge/term.py` with `safe_print`, `stars`, and `format_symbol` helpers that detect console capability and adaptively fall back to ASCII (`*`, `-`) without ever raising. Full Unicode output is preserved on UTF-8-capable terminals. All CLI output now routes through these helpers instead of scattering encoding logic across the codebase.
- Added `tests/test_term.py` (15 tests) simulating UTF-8, cp1252, cp437, and strict-ASCII console encodings.
- CI now runs an additional Windows/Linux/macOS smoke-test pass with `PYTHONIOENCODING=cp1252` forced, to catch regressions of this kind going forward.

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
