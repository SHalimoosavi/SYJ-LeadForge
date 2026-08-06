# Contributing to SYJ LeadForge

Thanks for considering a contribution! This project is community-driven and welcomes issues, discussions, and pull requests.

## Ground rules

- No feature may scrape data without permission, bypass rate limits/robots.txt-style access controls, or automate unsolicited outreach. PRs that add such behavior will be declined regardless of usefulness.
- Keep the core (`leadforge/`) dependency-light — it should keep working on low-end devices (Termux, Raspberry Pi) with just `requests` installed.
- Every score or audit signal must be explainable — no unexplained "black box" numbers.

## Setup

```bash
git clone https://github.com/SHalimoosavi/SYJ-LeadForge.git
cd SYJ-LeadForge
pip install -e ".[dev]"
pytest -q
ruff check leadforge tests
```

## Making a change

1. Open an issue first for anything non-trivial, so design direction can be discussed.
2. Write or update tests for any behavior change — audit and scoring logic especially should stay covered, since they're the trust foundation of the project.
3. Run `pytest -q` and `ruff check leadforge tests` before opening a PR.
4. Keep PRs focused; smaller PRs get reviewed faster.

## Reporting bugs

Open a GitHub issue with: what you ran, what you expected, what happened instead, and your OS/Python version (`leadforge doctor` output is helpful here).

## Code of Conduct

Be respectful and constructive. See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
