from leadforge.models import AuditResult, Business
from leadforge.scoring import is_excluded_category, score_business


def test_no_website_scores_high():
    b = Business(id=1, name="Smile Dental", category="Dental Clinic", rating=4.6, review_count=182)
    score = score_business(b)
    assert score.opportunity_score > 50
    assert score.tier in {"High", "Very High"}
    assert any("No website" in r for r in score.reasons)


def test_excluded_category_scores_zero():
    b = Business(id=1, name="Rahul's Tea Stall", category="Tea Stall")
    score = score_business(b)
    assert score.opportunity_score == 0
    assert score.tier == "Excluded"
    assert is_excluded_category("Tea Stall")


def test_good_existing_website_scores_lower_than_no_website():
    b_no_site = Business(id=1, name="A", category="Restaurant", rating=4.5, review_count=50)
    b_good_site = Business(id=2, name="B", category="Restaurant", website="https://b.example.com", rating=4.5, review_count=50)

    good_audit = AuditResult(business_id=2, url="https://b.example.com", reachable=True, overall_score=90)

    score_no_site = score_business(b_no_site)
    score_good_site = score_business(b_good_site, audit=good_audit)

    assert score_no_site.opportunity_score > score_good_site.opportunity_score


def test_unreachable_website_scores_high():
    b = Business(id=1, name="C", category="Hotel", website="https://down.example.com")
    audit = AuditResult(business_id=1, url="https://down.example.com", reachable=False, error="timeout")
    score = score_business(b, audit=audit)
    assert score.opportunity_score >= 40
    assert any("unreachable" in r.lower() for r in score.reasons)


def test_score_bounds():
    b = Business(id=1, name="D", category="Law Firm", rating=5.0, review_count=10000)
    score = score_business(b)
    assert 0 <= score.opportunity_score <= 100
    assert 1 <= score.stars <= 5
