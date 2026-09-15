# Replit build brief — P&P Auto Services
Prepared 2026-09-15 · lead `p-p-auto-services-utiimc` · Rooster Innovations

Paste everything below the line into Replit Agent. It is written to be pasted whole.

---

Build a single-page marketing website for a real local business. This is a design proposal
I will show the owner in person, so it has to look like a designer made it — not like a
template with the words swapped.

## VERIFIED FACTS — the only facts about this business you may state

- **Business name:** P&P Auto Services
- **Type of business:** Car repair and maintenance service
- **Address:** 2008 S Bancroft St, Philadelphia, PA 19145, USA
- **Phone:** (215) 463-1108
- **Google rating:** 5 out of 5 from 241 Google reviews — you may show this ONLY labeled "Rating on Google"
- **Hours:** 
  - Monday: 9:00 AM – 6:00 PM
  - Tuesday: 9:00 AM – 6:00 PM
  - Wednesday: 9:00 AM – 6:00 PM
  - Thursday: 9:00 AM – 6:00 PM
  - Friday: 9:00 AM – 6:00 PM
  - Saturday: Closed
  - Sunday: Closed
- **Existing website:** NOT PROVIDED — you may not invent this

Anything marked NOT PROVIDED must be handled with a graceful fallback, never invented.

## DESIGN DIRECTION

Use this random string as a creative seed. Read it for subpatterns — letter clusters, digit
runs, repeats, symmetry — and let what you find drive a specific direction before you consider
anything else: an actual color palette (name the hex values), a display + body type pairing,
a layout structure, and a texture treatment.

    QXF7J33k51jffmbxE1AkRz1fN14TsVsa74QtsNoYEP8zIWDn

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
supporting scene images, and a texture or detail shot. Art direction: the texture of a working garage — lifts, tools, tire walls, chrome, oil-stained concrete, work lights.
Match the images to the palette so the page reads as one designed object.

Rules for the imagery:

1. The images are ORIGINAL ART, not documentation. Never generate anything that purports to
   show this business's actual storefront, sign, staff, vehicles, or work. No invented logos,
   no invented signage text, no recognizable faces presented as employees or customers.
2. Every page that uses generated imagery must carry one small, legible line near the footer:
   *"Placeholder imagery — replaced with P&P Auto Services's own photos before launch."*
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
