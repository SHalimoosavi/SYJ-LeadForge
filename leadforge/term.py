"""Cross-platform-safe terminal output helpers.

Different consoles support different output encodings:

- Linux/macOS terminals: almost always UTF-8, full Unicode support.
- Windows Terminal / PowerShell 7+: usually UTF-8.
- Legacy Windows `cmd.exe`, older PowerShell hosts, and some CI runners
  (notably GitHub Actions' Windows matrix): often report `cp1252` or
  `cp437`, which cannot encode characters like the star glyph (`★`) or
  an em dash (`—`), and raise `UnicodeEncodeError` on `print()`.

This module is the single place that decides whether to emit Unicode
symbols or their ASCII fallback, and provides `safe_print`, which can
never crash a CLI run because of a console encoding limitation --
regardless of whether the "unsafe" character came from a hardcoded
string (like a star rating) or from user data (like an imported
business name containing an accented or non-Latin character).

Nothing elsewhere in the codebase should need to reason about console
encoding directly; import from here instead.
"""
from __future__ import annotations

import sys
from typing import TextIO

# Unicode symbol -> ASCII-safe fallback, used both for known glyphs we
# emit ourselves (stars, arrows, dashes) and as a generic safety net.
_SYMBOL_FALLBACKS: dict[str, str] = {
    "★": "*",
    "☆": "*",
    "✓": "OK",
    "✔": "OK",
    "✗": "X",
    "✘": "X",
    "→": "->",
    "—": "-",
    "–": "-",
    "…": "...",
}


def supports_unicode(stream: TextIO | None = None) -> bool:
    """Best-effort, cached-per-call detection of whether `stream` can
    safely encode the Unicode symbols this CLI uses.

    Rather than trusting an encoding *name* (some streams report
    'utf-8' but are still backed by a codepage that can't represent
    everything), this actually attempts to encode a representative
    sample using the stream's reported encoding -- the same check
    `safe_print` relies on.
    """
    stream = stream if stream is not None else sys.stdout
    encoding = getattr(stream, "encoding", None) or "ascii"
    sample = "".join(_SYMBOL_FALLBACKS.keys())
    try:
        sample.encode(encoding)
        return True
    except (UnicodeEncodeError, LookupError, TypeError):
        return False


def _to_ascii_fallback(text: str) -> str:
    for symbol, fallback in _SYMBOL_FALLBACKS.items():
        if symbol in text:
            text = text.replace(symbol, fallback)
    return text


def format_symbol(symbol: str, *, stream: TextIO | None = None) -> str:
    """Return `symbol` unchanged if `stream` supports it, else its ASCII fallback."""
    if supports_unicode(stream):
        return symbol
    return _SYMBOL_FALLBACKS.get(symbol, symbol)


def stars(count: int, max_count: int = 5, *, stream: TextIO | None = None) -> str:
    """Render a star rating as Unicode stars where supported, else asterisks."""
    count = max(0, min(count, max_count))
    glyph = "*" if not supports_unicode(stream) else "★"
    return glyph * count


def safe_print(
    *args: object,
    sep: str = " ",
    end: str = "\n",
    file: TextIO | None = None,
    flush: bool = False,
) -> None:
    """`print()` that can never raise `UnicodeEncodeError`.

    Order of attempts:
    1. Print the text as-is (full Unicode fidelity on capable terminals).
    2. If that fails, print an ASCII-fallback version (known symbols
       swapped for their ASCII equivalents).
    3. If even that fails (e.g. the text contains other, unmapped
       non-ASCII characters -- such as an accented name from an
       imported CSV -- on a strict-ASCII console), replace whatever
       characters the stream truly cannot represent rather than
       crashing the whole CLI run.
    """
    stream = file if file is not None else sys.stdout
    text = sep.join(str(a) for a in args)

    try:
        print(text, end=end, file=stream, flush=flush)
        return
    except UnicodeEncodeError:
        pass

    fallback_text = _to_ascii_fallback(text)
    try:
        print(fallback_text, end=end, file=stream, flush=flush)
        return
    except UnicodeEncodeError:
        pass

    encoding = getattr(stream, "encoding", None) or "ascii"
    safe_text = fallback_text.encode(encoding, errors="replace").decode(encoding, errors="replace")
    print(safe_text, end=end, file=stream, flush=flush)
