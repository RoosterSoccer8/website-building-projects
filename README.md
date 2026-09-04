# South Philly Sites — lead pipeline

Finds South Philadelphia businesses with **no website** or a **genuinely broken/outdated one**, ranks them by pitch-worthiness, and builds unlisted preview sites for the leads *you* flag — so you demo an MVP, collect the owner's input, and close, instead of rebuilding sites nobody asked for.

## How it flows

1. **Daily scan (automatic, 8am ET).** `scanner.py` searches Google Places (New API) for that weekday's category rotation (Mon restaurants, Tue barbers/salons, Wed contractors…). Every business is checked exactly once, ever — the `leads.json` ledger dedupes on `place_id`, so you never pay Google twice for the same lead.
2. **Honest audit.** If a business has a website, the scanner actually fetches it and only marks it OUTDATED for real problems: dead/unreachable, parked domain, Facebook-page-only, no HTTPS, no mobile viewport, near-empty page, stale copyright. Good sites are recorded and skipped — you'll never pitch a redesign to someone with a fine website. Sites that block automated checks (WAF 403s) are recorded as *unverified* and kept out of the queue too, so you never claim "your site is down" off a bot-block.
3. **You review the queue.** The dashboard (GitHub Pages, `docs/index.html`) shows every lead ranked by score with audit flags, your notes, and one-tap call/map links.
4. **You flag, it builds.** Change a lead's `"status"` to `"build"` in `leads.json` (GitHub app works fine from your phone) and commit. The Build Previews action generates its site with Claude — your zero-hallucination prompt, verbatim — into `docs/sites/<slug>/` and flips the status to `generated`.
5. **You pitch.** Each preview has an unlisted URL and a QR code on the dashboard. Walk in, hand them their site on your phone. Every preview carries `noindex,nofollow` and a visible "Design preview — not the official website" ribbon, so it can never be indexed or mistaken for the real thing.
6. **You track.** Update statuses as you go: `pitched` → `replied` → `sold` / `dead`, and keep call notes in each lead's `"notes"` field. The dashboard reflects it all.

## One-time setup (~10 minutes)

1. Create a **public** GitHub repo (public is required for free GitHub Pages), upload these files, and make sure the default branch is `main`.
2. **Secrets** — repo → Settings → Secrets and variables → Actions → New repository secret:
   - `GOOGLE_MAPS_API_KEY` — from Google Cloud Console, with **Places API (New)** enabled on the project (the legacy Places API won't work on new keys). Set a billing budget alert; Text Search + this field mask runs pennies per scan.
   - `ANTHROPIC_API_KEY` — from console.anthropic.com.
   - Optional: Settings → Variables → `CLAUDE_MODEL` to pin a model (defaults to the one in `config.py`).
3. **Pages** — Settings → Pages → Source: *Deploy from a branch* → branch `main`, folder `/docs`. Your dashboard lands at `https://<you>.github.io/<repo>/`.
4. **Kick it off** — Actions tab → *Daily lead scan* → Run workflow. It also runs itself every morning after that.

## Day-to-day (all from your phone)

- Open the dashboard, skim the ranked queue.
- Flag a lead: edit `leads.json` in the GitHub app → status `"build"` → commit. Preview appears in a couple of minutes.
- Pitch with the preview URL or QR code; log the outcome in status + notes.
- After a **yes**: get their real photos, menu/services, and hours from the owner, drop them into the payload, regenerate (or hand-edit), strip the ribbon and `noindex`, and move the site to their own domain. Don't ship Google's photos/reviews on the final site — Maps data is for your internal lead-gen only.

## Costs & knobs

- **Google**: only new place_ids incur Detail-level fields, and the field mask requests only what's used. The rotation (3 categories × 3 areas/day) is set in `config.py` — trim `AREAS` or categories to cut spend further.
- **Anthropic**: you pay only for previews you flag. One preview ≈ a few cents.
- Add/remove categories, areas, zips, audit thresholds in `config.py`.

## Files

| File | Role |
|---|---|
| `scanner.py` | Places search, website audit, scoring, dedupe ledger |
| `generator.py` | Claude site generation for flagged leads only |
| `build_dashboard.py` | Rebuilds `docs/index.html` from the ledger |
| `leads.json` | The database: every lead, status, notes |
| `prompts/site_prompt.txt` | Your anti-hallucination generation prompt |
| `docs/` | GitHub Pages root: dashboard + `sites/<slug>/` previews |
| `.github/workflows/` | `scan.yml` (daily cron) · `build.yml` (flag-triggered) |

A fictional sample preview ships at `docs/sites/demo-rowhouse-bakery-sample/` so you can see the output style before spending a token.

## Replit (optional)

There's no public Replit API to create repls automatically, but Replit imports GitHub repos directly (Create Repl → Import from GitHub) if you ever want to edit or host from there. The pipeline doesn't need it.
