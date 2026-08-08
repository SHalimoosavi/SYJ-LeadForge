"""End-to-end tests for the SYJ LeadForge FastAPI backend.

Uses FastAPI's TestClient (no real network needed) with an isolated
temp `LEADFORGE_HOME` per test via the `api_client` fixture. Audit
endpoints mock `leadforge.audit.requests.get`, exactly like the CLI's
audit tests, so no real HTTP requests are made.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

SAMPLE_CSV = Path(__file__).parent.parent / "sample_data" / "businesses_sample.csv"

GOOD_HTML = """
<html lang="en">
<head>
  <title>Acme Dental Clinic</title>
  <meta name="description" content="Best dental clinic in town">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="icon" href="/favicon.ico">
</head>
<body>
  <h1>Welcome</h1>
  <img src="tooth.jpg" alt="Tooth illustration">
  <a href="mailto:hello@acme.com">Email us</a>
  <a href="https://wa.me/919000000000">WhatsApp us</a>
</body>
</html>
"""


def _mock_response(text, status_code=200, url="https://acme.example.com"):
    resp = MagicMock()
    resp.text = text
    resp.status_code = status_code
    resp.url = url
    resp.history = []
    return resp


# -- Health -----------------------------------------------------------------

def test_health(api_client):
    resp = api_client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "version" in body


# -- Businesses ---------------------------------------------------------------

def test_create_and_get_business(api_client):
    resp = api_client.post(
        "/businesses",
        json={"name": "Acme Dental", "category": "Dental Clinic", "city": "Hyderabad"},
    )
    assert resp.status_code == 201
    created = resp.json()
    assert created["id"] > 0
    assert created["name"] == "Acme Dental"

    resp = api_client.get(f"/businesses/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Acme Dental"


def test_get_business_not_found(api_client):
    resp = api_client.get("/businesses/9999")
    assert resp.status_code == 404


def test_list_businesses_empty_then_populated(api_client):
    assert api_client.get("/businesses").json() == []
    api_client.post("/businesses", json={"name": "A", "category": "Gym", "city": "X"})
    api_client.post("/businesses", json={"name": "B", "category": "Hotel", "city": "Y"})
    resp = api_client.get("/businesses")
    assert len(resp.json()) == 2


def test_list_businesses_filter_by_category_and_city(api_client):
    api_client.post("/businesses", json={"name": "A", "category": "Gym", "city": "Hyderabad"})
    api_client.post("/businesses", json={"name": "B", "category": "Hotel", "city": "Mumbai"})
    resp = api_client.get("/businesses", params={"category": "Gym"})
    names = [b["name"] for b in resp.json()]
    assert names == ["A"]
    resp = api_client.get("/businesses", params={"city": "Mumbai"})
    names = [b["name"] for b in resp.json()]
    assert names == ["B"]


def test_import_csv(api_client):
    with SAMPLE_CSV.open("rb") as f:
        resp = api_client.post(
            "/businesses/import",
            files={"file": ("businesses_sample.csv", f, "text/csv")},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["imported"] == 6
    assert len(body["businesses"]) == 6


def test_import_rejects_non_csv(api_client):
    resp = api_client.post(
        "/businesses/import",
        files={"file": ("businesses.txt", b"name\nAcme\n", "text/plain")},
    )
    assert resp.status_code == 400


def test_import_rejects_missing_required_column(api_client):
    resp = api_client.post(
        "/businesses/import",
        files={"file": ("bad.csv", b"category,city\nDental,Hyderabad\n", "text/csv")},
    )
    assert resp.status_code == 400
    assert "name" in resp.json()["detail"].lower()


# -- Audits -------------------------------------------------------------------

def test_audit_business_no_website(api_client):
    resp = api_client.post("/businesses", json={"name": "NoSite Co"})
    business_id = resp.json()["id"]
    resp = api_client.post(f"/businesses/{business_id}/audit")
    assert resp.status_code == 400


def test_audit_business_not_found(api_client):
    resp = api_client.post("/businesses/9999/audit")
    assert resp.status_code == 404


@patch("leadforge.audit._check_tls", return_value=True)
@patch("leadforge.audit.requests.get")
def test_audit_business_success(mock_get, mock_tls, api_client):
    mock_get.return_value = _mock_response(GOOD_HTML)
    resp = api_client.post(
        "/businesses", json={"name": "Acme", "website": "https://acme.example.com"}
    )
    business_id = resp.json()["id"]

    resp = api_client.post(f"/businesses/{business_id}/audit")
    assert resp.status_code == 200
    audit = resp.json()
    assert audit["reachable"] is True
    assert audit["overall_score"] > 70

    # latest audit is now retrievable via GET
    resp = api_client.get(f"/businesses/{business_id}/audit")
    assert resp.status_code == 200
    assert resp.json()["overall_score"] > 70


def test_get_latest_audit_when_none_exists(api_client):
    resp = api_client.post("/businesses", json={"name": "Acme", "website": "https://acme.example.com"})
    business_id = resp.json()["id"]
    resp = api_client.get(f"/businesses/{business_id}/audit")
    assert resp.status_code == 404


@patch("leadforge.audit._check_tls", return_value=True)
@patch("leadforge.audit.requests.get")
def test_run_all_audits(mock_get, mock_tls, api_client):
    mock_get.return_value = _mock_response(GOOD_HTML)
    api_client.post("/businesses", json={"name": "A", "website": "https://a.example.com"})
    api_client.post("/businesses", json={"name": "B", "website": "https://b.example.com"})
    api_client.post("/businesses", json={"name": "C"})  # no website, should be skipped

    resp = api_client.post("/audits/run")
    assert resp.status_code == 200
    body = resp.json()
    assert body["audited"] == 2
    assert len(body["results"]) == 2


# -- Scores ---------------------------------------------------------------------

def test_score_business_not_found(api_client):
    resp = api_client.post("/businesses/9999/score")
    assert resp.status_code == 404


def test_score_business_no_website_scores_high(api_client):
    resp = api_client.post(
        "/businesses",
        json={"name": "Dental Co", "category": "Dental Clinic", "rating": 4.6, "review_count": 182},
    )
    business_id = resp.json()["id"]

    resp = api_client.post(f"/businesses/{business_id}/score")
    assert resp.status_code == 200
    score = resp.json()
    assert score["opportunity_score"] > 50
    assert score["tier"] in {"High", "Very High"}

    resp = api_client.get(f"/businesses/{business_id}/score")
    assert resp.status_code == 200
    assert resp.json()["opportunity_score"] == score["opportunity_score"]


def test_get_latest_score_when_none_exists(api_client):
    resp = api_client.post("/businesses", json={"name": "Acme"})
    business_id = resp.json()["id"]
    resp = api_client.get(f"/businesses/{business_id}/score")
    assert resp.status_code == 404


def test_score_excluded_category_is_zero(api_client):
    resp = api_client.post("/businesses", json={"name": "Tea Stall Co", "category": "Tea Stall"})
    business_id = resp.json()["id"]
    resp = api_client.post(f"/businesses/{business_id}/score")
    assert resp.status_code == 200
    assert resp.json()["opportunity_score"] == 0
    assert resp.json()["tier"] == "Excluded"


def test_run_all_scores(api_client):
    api_client.post("/businesses", json={"name": "A", "category": "Gym"})
    api_client.post("/businesses", json={"name": "B", "category": "Hotel"})
    resp = api_client.post("/scores/run")
    assert resp.status_code == 200
    body = resp.json()
    assert body["scored"] == 2
    assert len(body["results"]) == 2


# -- Leads, export, stats --------------------------------------------------------

def _seed_and_score(api_client) -> None:
    with SAMPLE_CSV.open("rb") as f:
        api_client.post("/businesses/import", files={"file": ("s.csv", f, "text/csv")})
    api_client.post("/scores/run")


def test_list_leads_sorted_by_score(api_client):
    _seed_and_score(api_client)
    resp = api_client.get("/leads")
    assert resp.status_code == 200
    leads = resp.json()
    assert len(leads) == 6
    scores = [lead["score"]["opportunity_score"] for lead in leads if lead["score"]]
    assert scores == sorted(scores, reverse=True)


def test_list_leads_filter_by_tier_and_min_score(api_client):
    _seed_and_score(api_client)
    resp = api_client.get("/leads", params={"min_score": 90})
    for lead in resp.json():
        assert lead["score"]["opportunity_score"] >= 90

    resp = api_client.get("/leads", params={"tier": "Excluded"})
    for lead in resp.json():
        assert lead["score"]["tier"] == "Excluded"


def test_export_csv(api_client):
    _seed_and_score(api_client)
    resp = api_client.get("/leads/export/csv")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")
    assert b"opportunity_score" in resp.content


def test_export_json(api_client):
    _seed_and_score(api_client)
    resp = api_client.get("/leads/export/json")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 6


def test_export_markdown(api_client):
    _seed_and_score(api_client)
    resp = api_client.get("/leads/export/md")
    assert resp.status_code == 200
    assert b"SYJ LeadForge" in resp.content


def test_export_unsupported_format(api_client):
    _seed_and_score(api_client)
    resp = api_client.get("/leads/export/xlsx")
    assert resp.status_code == 400


def test_export_no_matching_leads(api_client):
    resp = api_client.get("/leads/export/csv")
    assert resp.status_code == 404


def test_stats(api_client):
    _seed_and_score(api_client)
    resp = api_client.get("/stats")
    assert resp.status_code == 200
    stats = resp.json()
    assert stats["total_businesses"] == 6
    assert stats["scored"] == 6
    assert "Excluded" in stats["tier_breakdown"]
    assert stats["average_score"] >= 0


def test_stats_empty_db(api_client):
    resp = api_client.get("/stats")
    assert resp.status_code == 200
    stats = resp.json()
    assert stats["total_businesses"] == 0
    assert stats["average_score"] == 0.0
