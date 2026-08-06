from pathlib import Path

import pytest

from leadforge.importer import ImportError_, load_businesses_from_csv


def test_load_sample_csv():
    path = Path(__file__).parent.parent / "sample_data" / "businesses_sample.csv"
    businesses = load_businesses_from_csv(path)
    assert len(businesses) == 6
    names = {b.name for b in businesses}
    assert "Smile Care Dental Clinic" in names

    dental = next(b for b in businesses if b.name == "Smile Care Dental Clinic")
    assert dental.website == ""
    assert dental.category == "Dental Clinic"
    assert dental.rating == 4.6
    assert dental.review_count == 182

    diagnostics = next(b for b in businesses if "Diagnostics" in b.name)
    assert diagnostics.website.startswith("http://")


def test_missing_file_raises(tmp_path):
    with pytest.raises(ImportError_):
        load_businesses_from_csv(tmp_path / "does_not_exist.csv")


def test_missing_required_column(tmp_path):
    csv_path = tmp_path / "bad.csv"
    csv_path.write_text("category,city\nDental,Hyderabad\n", encoding="utf-8")
    with pytest.raises(ImportError_):
        load_businesses_from_csv(csv_path)


def test_url_normalization(tmp_path):
    csv_path = tmp_path / "biz.csv"
    csv_path.write_text("name,website\nAcme,acme.com\n", encoding="utf-8")
    businesses = load_businesses_from_csv(csv_path)
    assert businesses[0].website == "https://acme.com"


def test_blank_rows_skipped(tmp_path):
    csv_path = tmp_path / "biz.csv"
    csv_path.write_text("name,city\nAcme,Hyderabad\n,Nowhere\n", encoding="utf-8")
    businesses = load_businesses_from_csv(csv_path)
    assert len(businesses) == 1
