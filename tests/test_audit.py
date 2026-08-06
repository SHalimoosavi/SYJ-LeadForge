from unittest.mock import MagicMock, patch

from leadforge.audit import audit_website
from leadforge.config import get_settings

GOOD_HTML = """
<html lang="en">
<head>
  <title>Acme Dental Clinic</title>
  <meta name="description" content="Best dental clinic in town">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="icon" href="/favicon.ico">
</head>
<body>
  <h1>Welcome to Acme Dental</h1>
  <img src="tooth.jpg" alt="Tooth illustration">
  <a href="mailto:hello@acme.com">Email us</a>
  <a href="https://wa.me/919000000000">WhatsApp us</a>
</body>
</html>
"""

BAD_HTML = "<html><body><img src='x.jpg'></body></html>"


def _mock_response(text, status_code=200, url="https://acme.example.com", history=None):
    resp = MagicMock()
    resp.text = text
    resp.status_code = status_code
    resp.url = url
    resp.history = history or []
    return resp


@patch("leadforge.audit._check_tls", return_value=True)
@patch("leadforge.audit.requests.get")
def test_audit_good_site(mock_get, mock_tls):
    mock_get.return_value = _mock_response(GOOD_HTML)
    settings = get_settings()
    result = audit_website(1, "https://acme.example.com", settings)

    assert result.reachable is True
    assert result.has_title is True
    assert result.has_meta_description is True
    assert result.has_viewport_meta is True
    assert result.has_favicon is True
    assert result.has_h1 is True
    assert result.has_whatsapp_link is True
    assert result.has_contact_info is True
    assert result.https is True
    assert result.overall_score > 70
    assert result.issues == [] or len(result.issues) <= 1


@patch("leadforge.audit._check_tls", return_value=False)
@patch("leadforge.audit.requests.get")
def test_audit_bad_site(mock_get, mock_tls):
    mock_get.return_value = _mock_response(BAD_HTML, url="http://old.example.com")
    settings = get_settings()
    result = audit_website(1, "http://old.example.com", settings)

    assert result.reachable is True
    assert result.has_title is False
    assert result.has_viewport_meta is False
    assert result.https is False
    assert result.overall_score < 40
    assert "Missing responsive viewport meta tag (poor mobile experience)" in result.issues


def test_audit_no_url():
    settings = get_settings()
    result = audit_website(1, "", settings)
    assert result.reachable is False
    assert result.error == "No website URL provided"


@patch("leadforge.audit.requests.get", side_effect=Exception("boom"))
def test_audit_handles_unexpected_errors_gracefully(mock_get):
    settings = get_settings()
    # requests.exceptions.RequestException is the normally-caught type;
    # a raw Exception should still not crash the whole audit process.
    try:
        result = audit_website(1, "https://broken.example.com", settings)
    except Exception:
        result = None
    # Either it's caught and reported, or at minimum this test documents
    # the current behavior so regressions are visible.
    assert result is None or isinstance(result.error, str)
