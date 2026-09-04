"""Daily lead scanner.

- Uses Google Places API (New) text search with field masks (pay only for
  fields we use) and full pagination.
- Rotates categories by weekday (see config.CATEGORY_ROTATION).
- Dedupes on place_id: a business is fetched and audited exactly once, ever.
- OUTDATED_WEBSITE is decided by a real HTTP audit of the site, never by
  review counts.
- Appends new leads to leads.json with status "new" and a pitch score.

Env vars:
  GOOGLE_MAPS_API_KEY  (required)
  SCAN_CATEGORIES      optional comma-separated override of today's rotation
"""

import datetime
import json
import os
import re
import sys
import time
from urllib.parse import urlparse

import requests

import config

PLACES_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
FIELD_MASK = ",".join([
    "places.id",
    "places.displayName",
    "places.types",
    "places.primaryTypeDisplayName",
    "places.formattedAddress",
    "places.nationalPhoneNumber",
    "places.rating",
    "places.userRatingCount",
    "places.websiteUri",
    "places.regularOpeningHours.weekdayDescriptions",
    "places.businessStatus",
    "nextPageToken",
])

UA = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
      "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile Safari/604.1")


# --------------------------------------------------------------------------
# Ledger
# --------------------------------------------------------------------------

def load_ledger(path=config.LEDGER_PATH):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {"leads": {}}


def save_ledger(ledger, path=config.LEDGER_PATH):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(ledger, f, indent=2, ensure_ascii=False)


# --------------------------------------------------------------------------
# Places API (New)
# --------------------------------------------------------------------------

def text_search(query, api_key, max_pages=3):
    """Yield place dicts for a text query, following pagination (~60 max)."""
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": FIELD_MASK,
    }
    body = {"textQuery": query, "pageSize": 20}
    for _ in range(max_pages):
        resp = requests.post(PLACES_SEARCH_URL, headers=headers, json=body, timeout=30)
        if resp.status_code != 200:
            print(f"  ! Places API error {resp.status_code}: {resp.text[:300]}")
            return
        data = resp.json()
        for place in data.get("places", []):
            yield place
        token = data.get("nextPageToken")
        if not token:
            return
        body = {"textQuery": query, "pageSize": 20, "pageToken": token}
        time.sleep(1.5)


# --------------------------------------------------------------------------
# Website audit — the honest OUTDATED detector
# --------------------------------------------------------------------------

def classify_audit_response(final_url, status_code, html):
    """Pure function: derive audit flags from a fetched response.

    Separated from fetching so it can be unit-tested offline.
    """
    flags = []
    host = urlparse(final_url).netloc.lower().removeprefix("www.")

    # Bot-blocking responses (Cloudflare/WAF 403s, rate limits) do NOT prove
    # the site is broken for humans. Never pitch "your site is down" off one.
    if status_code in (401, 403, 406, 429):
        return ["unverified_bot_blocked"]

    if status_code >= 400:
        flags.append(f"dead_http_{status_code}")
        return flags

    if any(h in host for h in config.SOCIAL_ONLY_HOSTS):
        flags.append("social_profile_only")

    low = (html or "").lower()

    if any(p in low for p in config.PARKED_PHRASES):
        flags.append("parked_domain")

    if final_url.startswith("http://"):
        flags.append("no_https")

    if len(low.strip()) < 300 and "social_profile_only" not in flags:
        flags.append("near_empty_page")

    # Robust to name=viewport, name = "viewport", single/double/no quotes.
    if "<html" in low and not re.search(r"name\s*=\s*[\"']?viewport", low):
        flags.append("not_mobile_responsive")

    # Collect years near each copyright marker, handling ranges ("© 2010-2024").
    years = []
    for m in re.finditer(r"©|&copy;|copyright", low):
        window = low[m.end():m.end() + 60]
        years += [int(y) for y in re.findall(r"\b((?:19|20)\d{2})\b", window)]
    if years and max(years) < config.STALE_COPYRIGHT_BEFORE:
        flags.append(f"stale_copyright_{max(years)}")

    return flags


def audit_website(url):
    """Fetch a business's site and return {'flags': [...], 'final_url': str}."""
    try:
        resp = requests.get(
            url, headers={"User-Agent": UA}, timeout=config.AUDIT_TIMEOUT_SECONDS,
            allow_redirects=True,
        )
        flags = classify_audit_response(resp.url, resp.status_code, resp.text[:200_000])
        return {"flags": flags, "final_url": resp.url}
    except requests.exceptions.SSLError:
        return {"flags": ["broken_ssl"], "final_url": url}
    except requests.exceptions.RequestException as e:
        return {"flags": [f"unreachable_{type(e).__name__}"], "final_url": url}


# --------------------------------------------------------------------------
# Scoring — ranks the pitch queue
# --------------------------------------------------------------------------

def score_lead(status, flags, rating, review_count):
    s = 60 if status == "NO_WEBSITE" else 30
    s += 8 * len(flags)                                # worse site = better pitch
    s += min(review_count or 0, 150) * 0.2             # traction, capped
    s += (rating or 0) * 2                             # quality business
    return round(s, 1)


# --------------------------------------------------------------------------
# Lead building
# --------------------------------------------------------------------------

ZIP_RE = re.compile(r"\b(191\d{2})\b")


def extract_zip(address):
    m = ZIP_RE.search(address or "")
    return m.group(1) if m else None


def make_slug(name, place_id):
    base = re.sub(r"[^a-z0-9]+", "-", (name or "").lower()).strip("-")[:40]
    base = base or "business"  # names with no ASCII alphanumerics
    suffix = re.sub(r"[^A-Za-z0-9]", "", place_id)[-6:].lower()
    return f"{base}-{suffix}"


def process_place(place, ledger):
    """Return (added: bool, reason: str)."""
    pid = place.get("id")
    if not pid or pid in ledger["leads"]:
        return False, "already_known"
    if place.get("businessStatus") not in (None, "OPERATIONAL"):
        return False, "closed"

    address = place.get("formattedAddress")
    zip_code = extract_zip(address)
    if zip_code and zip_code not in config.TARGET_ZIPS:
        return False, "outside_target_zips"

    name = (place.get("displayName") or {}).get("text")
    website = place.get("websiteUri")
    rating = place.get("rating")
    reviews = place.get("userRatingCount")

    audit = None
    if not website:
        status = "NO_WEBSITE"
        flags = []
    else:
        audit = audit_website(website)
        flags = audit["flags"]
        if not flags:
            # Site is fine. Record so we never pay to re-check, but keep it
            # out of the pitch queue.
            ledger["leads"][pid] = {
                "business_name": name, "status": "skipped_good_site",
                "website": website, "seen": today(),
            }
            return False, "has_good_site"
        if flags == ["unverified_bot_blocked"]:
            # Site blocked our checker; we can't prove anything is wrong.
            # Record (so we never re-pay for it) but keep it out of the queue.
            ledger["leads"][pid] = {
                "business_name": name, "status": "skipped_unverified",
                "website": website, "seen": today(),
            }
            return False, "bot_blocked_unverified"
        status = "OUTDATED_WEBSITE"

    category = (place.get("primaryTypeDisplayName") or {}).get("text") \
        or (place.get("types") or ["local business"])[0].replace("_", " ").title()

    hours = (place.get("regularOpeningHours") or {}).get("weekdayDescriptions")

    ledger["leads"][pid] = {
        "slug": make_slug(name, pid),
        "business_name": name,
        "status": "new",                     # new -> build -> generated -> pitched -> replied -> sold/dead
        "lead_type": status,                 # NO_WEBSITE | OUTDATED_WEBSITE
        "category": category,
        "address": address,
        "zip": zip_code,
        "phone": place.get("nationalPhoneNumber"),
        "rating": rating,
        "review_count": reviews,
        "hours": hours,
        "website": website,
        "audit_flags": flags,
        "score": score_lead(status, flags, rating, reviews),
        "notes": "",
        "seen": today(),
        "generated_at": None,
        "preview_path": None,
    }
    return True, status


def today():
    return datetime.date.today().isoformat()


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main():
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        sys.exit("GOOGLE_MAPS_API_KEY is not set.")

    override = os.environ.get("SCAN_CATEGORIES", "").strip()
    if override:
        categories = [c.strip() for c in override.split(",") if c.strip()]
    else:
        categories = config.CATEGORY_ROTATION[datetime.date.today().weekday()]

    ledger = load_ledger()
    added = 0
    for cat in categories:
        for area in config.AREAS:
            query = f"{cat} in {area}"
            print(f"Searching: {query}")
            for place in text_search(query, api_key):
                ok, reason = process_place(place, ledger)
                if ok:
                    added += 1
                    lead = ledger["leads"][place["id"]]
                    print(f"  + {lead['business_name']} [{lead['lead_type']}] score={lead['score']}")

    save_ledger(ledger)
    queue = [l for l in ledger["leads"].values() if l.get("status") == "new"]
    print(f"\nDone. {added} new leads this run; {len(queue)} total awaiting review.")


if __name__ == "__main__":
    main()
