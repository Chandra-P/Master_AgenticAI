import pytest
from finpilot.rag import retrieve, ingest, loan_terms


def test_current_and_versions(db):
    hits = retrieve(db, "What APR is in my current auto loan?")
    assert hits[0]["document_id"] == "auto-current"
    assert loan_terms(hits)["apr"] == "6.49"
    both = retrieve(db, "Compare auto loan offers", include_superseded=True)
    assert {"auto-current", "auto-old"} <= {x["document_id"] for x in both}


def test_security_and_missing(db):
    hits = retrieve(db, "security test credit limit")
    assert any("Credit limit: $2,000" in x["passage"] for x in hits)
    assert all("ignore previous" not in x["passage"].lower() for x in hits)
    assert retrieve(db, "auto loan", user_id="stranger") == []
    with pytest.raises(ValueError):
        ingest(db, "../../x.exe", b"bad")
    with pytest.raises(ValueError):
        ingest(db, "large.txt", b"x" * (2 * 1024 * 1024 + 1))


def test_ingest_checksum_and_family(db):
    one = ingest(
        db,
        "offer.txt",
        b"SYNTHETIC\nVehicle price: $50,000\nAPR: 7.00%\nTerm: 60 months",
        family="custom-offer",
    )
    two = ingest(
        db,
        "offer.txt",
        b"SYNTHETIC\nVehicle price: $50,000\nAPR: 7.00%\nTerm: 60 months",
        family="custom-offer",
    )
    assert one["id"] == two["id"]
    updated = ingest(
        db,
        "offer2.txt",
        b"SYNTHETIC\nVehicle price: $50,000\nAPR: 8.00%\nTerm: 60 months",
        family="custom-offer",
        supersedes=one["id"],
    )
    assert updated["version"] == 2
