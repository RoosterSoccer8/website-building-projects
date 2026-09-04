"""Offline unit tests — no network, no API keys. Run: python -m pytest tests/ -q
(or plain `python tests/test_pipeline.py`)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scanner import classify_audit_response, extract_zip, make_slug, score_lead
from generator import strip_fences, inject_preview_guards, build_payload


FILLER = "<p>" + "Welcome to our shop. " * 30 + "</p>"  # realistic page bulk


def test_audit_dead():
    assert classify_audit_response("https://x.com", 404, "") == ["dead_http_404"]


def test_audit_bot_blocked_is_unverified_not_dead():
    # A WAF 403 proves nothing about what humans see — never a pitch signal.
    assert classify_audit_response("https://x.com", 403, "") == ["unverified_bot_blocked"]
    assert classify_audit_response("https://x.com", 429, "") == ["unverified_bot_blocked"]


def test_audit_good_site():
    html = f'<html><head><meta name="viewport" content="width=device-width"></head><body>{FILLER}© 2026 Acme</body></html>'
    assert classify_audit_response("https://acme.com", 200, html) == []


def test_audit_viewport_unquoted_counts_as_responsive():
    html = f'<html><head><meta name=viewport content=width=device-width></head><body>{FILLER}© 2026</body></html>'
    assert classify_audit_response("https://acme.com", 200, html) == []


def test_audit_copyright_range_uses_latest_year():
    # "© 2010-2026" must NOT flag stale — the range ends now.
    html = f'<html><head><meta name="viewport" content="w"></head><body>{FILLER}© 2010-2026 Tony</body></html>'
    assert classify_audit_response("https://tonys.com", 200, html) == []


def test_audit_near_empty_page():
    flags = classify_audit_response("https://ghost.com", 200, "<html><body>hi</body></html>")
    assert "near_empty_page" in flags


def test_audit_not_responsive_and_stale():
    html = f'<html><head><meta charset="utf-8"></head><body>{FILLER}Copyright 2014 Tony</body></html>'
    flags = classify_audit_response("https://tonys.com", 200, html)
    assert "not_mobile_responsive" in flags
    assert "stale_copyright_2014" in flags


def test_audit_social_only_and_http():
    html = f'<html><head><meta name="viewport" content="x"></head><body>{FILLER}© 2026</body></html>'
    flags = classify_audit_response("http://www.facebook.com/tonyspizza", 200, html)
    assert "social_profile_only" in flags
    assert "no_https" in flags


def test_audit_parked():
    flags = classify_audit_response("https://oldsite.com", 200,
                                    "<html><body>This domain is for sale!</body></html>")
    assert "parked_domain" in flags


def test_zip_filter():
    assert extract_zip("1200 Snyder Ave, Philadelphia, PA 19148, USA") == "19148"
    assert extract_zip("no zip here") is None


def test_slug_collision_proof():
    a = make_slug("Tony's Pizza", "ChIJAAAAAAAAAAAAABCDEF")
    b = make_slug("Tony's Pizza", "ChIJZZZZZZZZZZZZZUVWXYZ")
    assert a != b and a.startswith("tony-s-pizza-")


def test_slug_non_ascii_name():
    s = make_slug("李记面馆", "ChIJ12345ABCDE")
    assert s.startswith("business-") and len(s) > len("business-")


def test_scoring_ranks_no_website_higher():
    assert score_lead("NO_WEBSITE", [], 4.5, 50) > score_lead("OUTDATED_WEBSITE", ["no_https"], 4.5, 50)


def test_strip_fences():
    fenced = "Here is your site:\n```html\n<!DOCTYPE html><html></html>\n```\nEnjoy!"
    assert strip_fences(fenced) == "<!DOCTYPE html><html></html>"
    bare = "<!DOCTYPE html><html></html>"
    assert strip_fences(bare) == bare
    preamble = "Sure thing!\n<!DOCTYPE html><html></html>"
    assert strip_fences(preamble) == "<!DOCTYPE html><html></html>"


def test_preview_guards():
    html = "<!DOCTYPE html><html><head><title>x</title></head><body>hi</body></html>"
    out = inject_preview_guards(html, "Tony's Pizza")
    assert 'name="robots" content="noindex,nofollow"' in out
    assert "Design preview prepared for Tony's Pizza" in out
    assert out.index('name="robots"') < out.index("<title>")


def test_preview_guards_escape_html_in_name():
    out = inject_preview_guards("<html><head></head><body></body></html>", 'X <script>alert(1)</script>')
    assert "<script>alert(1)</script>" not in out
    assert "&lt;script&gt;" in out


def test_process_place_skips_bot_blocked(monkeypatch=None):
    import scanner
    orig = scanner.audit_website
    scanner.audit_website = lambda url: {"flags": ["unverified_bot_blocked"], "final_url": url}
    try:
        ledger = {"leads": {}}
        place = {"id": "PID1", "displayName": {"text": "Blocked Biz"},
                 "websiteUri": "https://blocked.example",
                 "formattedAddress": "100 Main St, Philadelphia, PA 19148"}
        added, reason = scanner.process_place(place, ledger)
        assert not added and reason == "bot_blocked_unverified"
        assert ledger["leads"]["PID1"]["status"] == "skipped_unverified"
    finally:
        scanner.audit_website = orig


def test_process_place_null_primary_type():
    import scanner
    orig = scanner.audit_website
    scanner.audit_website = lambda url: {"flags": ["no_https"], "final_url": url}
    try:
        ledger = {"leads": {}}
        place = {"id": "PID2", "displayName": {"text": "Old Site Biz"},
                 "websiteUri": "http://old.example", "primaryTypeDisplayName": None,
                 "types": ["hair_salon"],
                 "formattedAddress": "200 Main St, Philadelphia, PA 19145"}
        added, _ = scanner.process_place(place, ledger)
        assert added and ledger["leads"]["PID2"]["category"] == "Hair Salon"
    finally:
        scanner.audit_website = orig


def test_payload_never_invents():
    lead = {"business_name": "X", "lead_type": "NO_WEBSITE", "category": "Deli",
            "address": None, "phone": None, "rating": None, "review_count": None,
            "hours": None, "website": None}
    p = build_payload(lead)
    assert p["photo_urls"] == [] and p["services_or_menu"] is None
    assert p["hours"] is None and p["status"] == "NO_WEBSITE"


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} tests passed.")
