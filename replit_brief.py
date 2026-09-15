"""Writes a ready-to-paste Replit build brief for one lead.

The automated preview is the fast tier: good enough to walk in with, built in
a minute for pennies. This is the wow tier — a complete brief you paste into
Replit Agent, which has image generation and a stronger visual hand, for the
leads worth extra effort.

Every brief is saved as  briefs/<business-slug>-<YYYY-MM-DD>.md  so you always
know which business it belongs to and when it was written.

Usage:
    python replit_brief.py                  # brief for every generated lead missing one
    python replit_brief.py slug1,slug2      # briefs for these slugs
"""

import datetime
import os
import sys

import config
from scanner import load_ledger, save_ledger
from seed import design_seed

BRIEFS_DIR = "briefs"

# Art direction hints by trade. These steer the imagery Replit generates; they
# are never facts about the business.
CATEGORY_ART = {
    "auto": "the texture of a working garage — lifts, tools, tire walls, chrome, oil-stained concrete, work lights",
    "barber": "barbering craft — clippers, chair leather, mirrors, tile floors, neon, the back of a fresh cut",
    "salon": "salon atmosphere — styling stations, warm light, product shelves, soft focus interiors",
    "nail": "close-up hands, polish rows, clean bright surfaces, soft gradients",
    "restaurant": "food and room — steam, char, a busy pass, worn wood tables, warm evening light",
    "pizza": "dough, flame, a peel pulling a pie, flour dust, a red-sauce palette",
    "bakery": "proofing baskets, crust, powdered surfaces, morning light through a shop window",
    "cafe": "espresso pour, steam, ceramic, a sunlit counter",
    "contractor": "job-site materials — lumber, framing, tools, blueprints, work gloves",
    "plumb": "clean pipe work, fittings, a tidy van, tools laid out",
    "electric": "conduit, panels, tidy wiring, work light glow",
    "detail": "water beading on paint, a buffer arc, reflections on a clean panel, foam",
    "market": "produce crates, deli case, hanging goods, hand-lettered signs, packed shelves",
    "gym": "iron, chalk, rubber flooring, hard side light",
    "tattoo": "ink work, machine detail, linework, dark studio with focused light",
    "laundr": "machines in a row, folded stacks, bright fluorescent order",
    "groom": "dogs mid-groom, towels, tubs, playful energy",
    "florist": "stems, buckets, wrapping paper, a cool bright cooler",
    "cleaning": "spotless surfaces, light through clean glass, neat supplies",
}


def art_direction(lead):
    blob = f"{lead.get('category','')} {lead.get('business_name','')}".lower()
    for key, hint in CATEGORY_ART.items():
        if key in blob:
            return hint
    return ("the real texture of this trade — tools, materials, surfaces and light that someone "
            "in this business would recognize immediately")


def fact_or_missing(value, label=None):
    if value in (None, "", [], {}):
        return "NOT PROVIDED — you may not invent this"
    if isinstance(value, list):
        return "\n  - " + "\n  - ".join(str(v) for v in value)
    return f"{value}{f' ({label})' if label else ''}"


def build_brief(lead, seed=None):
    """Render the brief.

    The seed is FRESH by default — deliberately not the one the automated
    preview used. That way Replit explores a different direction and you walk
    into the meeting with two real options instead of one idea twice.
    """
    name = lead.get("business_name") or "This business"
    seed = seed or design_seed()
    today = datetime.date.today().isoformat()
    # Only claim a rival design exists when one actually does.
    has_preview = bool(lead.get("design_seed") and lead.get("preview_path"))
    seed_note = (
        "This seed is new. A different design for this same business already exists, and the point\n"
        "of this build is to arrive somewhere else — a different palette, a different type voice, a\n"
        "different structure — so the owner has two real options to react to. Follow the seed where\n"
        "it leads rather than reaching for the safe version."
        if has_preview else
        "Follow the seed where it leads rather than reaching for the safe version. A generic result\n"
        "is a failed result here."
    )
    rating = lead.get("rating")
    reviews = lead.get("review_count")
    rating_line = (f"{rating} out of 5 from {reviews} Google reviews — you may show this ONLY "
                   f'labeled "Rating on Google"') if rating else "NOT PROVIDED — you may not invent this"

    return f"""# Replit build brief — {name}
Prepared {today} · lead `{lead.get('slug','')}` · Rooster Innovations

Paste everything below the line into Replit Agent. It is written to be pasted whole.

---

Build a single-page marketing website for a real local business. This is a design proposal
I will show the owner in person, so it has to look like a designer made it — not like a
template with the words swapped.

## VERIFIED FACTS — the only facts about this business you may state

- **Business name:** {name}
- **Type of business:** {fact_or_missing(lead.get('category'))}
- **Address:** {fact_or_missing(lead.get('address'))}
- **Phone:** {fact_or_missing(lead.get('phone'))}
- **Google rating:** {rating_line}
- **Hours:** {fact_or_missing(lead.get('hours'))}
- **Existing website:** {fact_or_missing(lead.get('website'))}

Anything marked NOT PROVIDED must be handled with a graceful fallback, never invented.

## DESIGN DIRECTION

Use this random string as a creative seed. Read it for subpatterns — letter clusters, digit
runs, repeats, symmetry — and let what you find drive a specific direction before you consider
anything else: an actual color palette (name the hex values), a display + body type pairing,
a layout structure, and a texture treatment.

    {seed}

{seed_note}

Then bend that direction toward this specific business and neighborhood (South Philadelphia)
so it feels like this place and not a generic template. Commit to ONE layout archetype and
execute it properly:

- editorial split (full-height type column beside a full-bleed image or color field)
- type-poster hero (oversized display type IS the hero)
- asymmetric grid with deliberate offset
- alternating full-bleed bands with generous vertical rhythm
- framed/letterpress composition with wide margins

**Do not build:** a centered gradient hero above three rounded cards with emoji icons. No emoji
used as iconography. No identical border-radius on every element. No "Why Choose Us" checkmark
trio. That combination is what makes a site look like a free website builder, and it is the
single thing this design must avoid.

## IMAGERY — this is why I am building here instead of my automated pipeline

Generate 4 to 6 original images and use them at real scale: a full-bleed hero, one or two
supporting scene images, and a texture or detail shot. Art direction: {art_direction(lead)}.
Match the images to the palette so the page reads as one designed object.

Rules for the imagery:

1. The images are ORIGINAL ART, not documentation. Never generate anything that purports to
   show this business's actual storefront, sign, staff, vehicles, or work. No invented logos,
   no invented signage text, no recognizable faces presented as employees or customers.
2. Every page that uses generated imagery must carry one small, legible line near the footer:
   *"Placeholder imagery — replaced with {name}'s own photos before launch."*
   Keep it subtle but present. It is honest, and it makes the proposal look more professional,
   not less.
3. Do not scrape, embed, or hotlink photos from Google, Yelp, Facebook or the existing site.

## HARD RULES — these override every creative instinct

1. **Invent nothing factual.** No prices, no menu or service lists, no years in business, no
   founding story, no family history, no awards, no quoted reviews, no customer counts.
2. **No certifications or licenses.** Never state or imply state inspection, emissions
   licensing, ASE or manufacturer certification, insurance approval, or any credential —
   not even if it would be plausible for this trade.
3. **No service list** unless one appears under VERIFIED FACTS above. Instead include a clear
   callout inviting a call for the full list, paired with the phone number.
4. **Ratings** may appear only as "Rating on Google" with the real number. Never restate a
   review count as customers served or satisfaction.
5. **Hours** — print them exactly as listed above, or if NOT PROVIDED, show a line telling
   visitors to call for today's hours. Never guess.

## DELIVERABLE

- One mobile-first page. Real typographic hierarchy, deliberate spacing, considered color.
- Tap-to-call links using `tel:` and a directions link to
  `https://maps.google.com/?q=` plus the URL-encoded address.
- Schema.org LocalBusiness JSON-LD in the head using only the verified facts above.
- Fast: no heavy frameworks, no layout shift, works on a phone on cellular data.
- Include the placeholder-imagery line described above.

Build it so the owner's first reaction is that someone took their business seriously.
"""


def write_brief(lead, path_dir=BRIEFS_DIR, seed=None):
    os.makedirs(path_dir, exist_ok=True)
    fname = f"{lead.get('slug','lead')}-{datetime.date.today().isoformat()}.md"
    full = os.path.join(path_dir, fname)
    seed = seed or design_seed()
    with open(full, "w", encoding="utf-8") as f:
        f.write(build_brief(lead, seed=seed))
    lead["brief_path"] = f"{path_dir}/{fname}"
    lead["brief_seed"] = seed   # recorded so a re-roll is a deliberate choice
    return full


def main():
    requested = set()
    if len(sys.argv) > 1 and sys.argv[1].strip():
        requested = {s.strip() for s in sys.argv[1].split(",") if s.strip()}

    ledger = load_ledger()
    targets = [l for l in ledger["leads"].values()
               if l.get("slug") and (l["slug"] in requested or
                                     (not requested and l.get("status") == "generated"
                                      and not l.get("brief_path")))]
    if not targets:
        print("No briefs to write.")
        return
    for lead in targets:
        print(f"Brief: {lead['business_name']} -> {write_brief(lead)}")
    save_ledger(ledger)
    print(f"\nWrote {len(targets)} brief(s).")


if __name__ == "__main__":
    main()
