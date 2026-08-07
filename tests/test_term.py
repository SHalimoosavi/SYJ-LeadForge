"""Tests for leadforge.term — cross-platform-safe console output.

These simulate real-world console encodings (notably Windows cmd.exe's
cp1252/cp437) using in-memory streams with a fixed `.encoding`, so the
tests run identically on Linux/macOS/Windows CI without needing an
actual Windows console.
"""
from __future__ import annotations

import pytest

from leadforge.term import format_symbol, safe_print, stars, supports_unicode


class _FakeStream:
    """A minimal in-memory text stream that reports a fixed `.encoding`
    and raises UnicodeEncodeError on write() for characters that
    encoding can't represent -- mimicking a real Windows console.

    (Not a subclass of io.StringIO/TextIOBase because those types make
    `.encoding` a read-only property, which we need to control here.)
    """

    def __init__(self, encoding: str) -> None:
        self.encoding = encoding
        self._buffer: list[str] = []

    def write(self, s: str) -> int:
        s.encode(self.encoding)  # raises UnicodeEncodeError if unsupported
        self._buffer.append(s)
        return len(s)

    def flush(self) -> None:
        pass

    def getvalue(self) -> str:
        return "".join(self._buffer)


def test_supports_unicode_true_for_utf8():
    stream = _FakeStream("utf-8")
    assert supports_unicode(stream) is True


def test_supports_unicode_false_for_cp1252():
    stream = _FakeStream("cp1252")
    assert supports_unicode(stream) is False


def test_supports_unicode_false_for_cp437():
    stream = _FakeStream("cp437")
    assert supports_unicode(stream) is False


def test_supports_unicode_handles_missing_encoding_attr():
    stream = object()  # no .encoding attribute at all
    assert supports_unicode(stream) in (True, False)  # must not raise


def test_format_symbol_unicode_terminal():
    stream = _FakeStream("utf-8")
    assert format_symbol("★", stream=stream) == "★"


def test_format_symbol_ascii_terminal():
    stream = _FakeStream("cp1252")
    assert format_symbol("★", stream=stream) == "*"


def test_format_symbol_unknown_symbol_passthrough():
    stream = _FakeStream("cp1252")
    # No fallback registered for this symbol -> returned unchanged.
    assert format_symbol("♣", stream=stream) == "♣"


def test_stars_unicode_terminal():
    stream = _FakeStream("utf-8")
    assert stars(3, stream=stream) == "★★★"


def test_stars_ascii_terminal():
    stream = _FakeStream("cp1252")
    assert stars(3, stream=stream) == "***"


def test_stars_clamped_to_bounds():
    stream = _FakeStream("utf-8")
    assert stars(-2, stream=stream) == ""
    assert stars(999, max_count=5, stream=stream) == "★" * 5


def test_safe_print_unicode_terminal_keeps_unicode():
    stream = _FakeStream("utf-8")
    safe_print("Rating:", stars(4, stream=stream), file=stream)
    assert "★★★★" in stream.getvalue()


def test_safe_print_ascii_terminal_falls_back_without_raising():
    stream = _FakeStream("cp1252")
    # Directly write a Unicode star (as if hardcoded) through safe_print;
    # it must not raise UnicodeEncodeError and must produce readable output.
    safe_print("Rating: ★★★★★ done", file=stream)
    output = stream.getvalue()
    assert "*****" in output
    assert "done" in output


def test_safe_print_handles_unmapped_non_ascii_data_gracefully():
    """Simulates a business name with an accented character imported from
    a CSV, printed on a strict-ASCII console. Must never crash."""
    stream = _FakeStream("ascii")
    try:
        safe_print("Café Résumé — ✓ done", file=stream)
    except UnicodeEncodeError:
        pytest.fail("safe_print must never raise UnicodeEncodeError")
    assert "done" in stream.getvalue()


def test_safe_print_multiple_args_and_sep():
    stream = _FakeStream("utf-8")
    safe_print("a", "b", "c", sep="-", file=stream)
    assert stream.getvalue().strip() == "a-b-c"


def test_safe_print_to_real_stdout_does_not_raise(capsys):
    # Sanity check against the real captured stdout stream too.
    safe_print("Rating:", stars(5))
    captured = capsys.readouterr()
    assert "Rating:" in captured.out
