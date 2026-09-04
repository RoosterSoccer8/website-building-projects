"""Preview-site generator — builds ONLY leads flagged for build.

A lead is built when its status in leads.json is "build" (set it from the
GitHub mobile/web app), or when its slug is passed explicitly:

    python generator.py                 # build everything with status "build"
    python generator.py slug1,slug2     # build these slugs regardless of status

Every generated page gets:
  - <meta name="robots" content="noindex,nofollow">  (previews stay unlisted)
  - a fixed "Design preview — not the official site" ribbon
so a preview can never be mistaken for, or indexed as, the real business site.

Env vars:
  ANTHROPIC_API_KEY  (required)
  CLAUDE_MODEL       optional model override
"""

import html as html_mod
import json
import os
import re
import sys

import config
from scanner import load_ledger, save_ledger, today

ROBOTS_META = '<meta name="robots" content="noindex,nofollow">'

RIBBON_TEMPLATE = (
    '<style>body{{padding-bottom:64px!important}}</style>'
    '<div id="preview-ribbon" style="position:fixed;bottom:0;left:0;right:0;'
    'z-index:99999;background:#111827;color:#f9fafb;text-align:center;'
    'padding:10px 16px;font:600 13px/1.5 system-ui,-apple-system,sans-serif;'
    'box-shadow:0 -2px 8px rgba(0,0,0,.25)">'
    'Design preview prepared for {name} by {author} &mdash; not the official website.'
    '</div>'
)


# --------------------------------------------------------------------------
# Post-processing (pure functions, unit-tested offline)
# --------------------------------------------------------------------------

def strip_fences(text):
    """Extract raw HTML even if the model wrapped it in ``` fences or prose."""
    m = re.search(r"```(?:html)?\s*(.*?)```", text, re.DOTALL)
    if m:
        text = m.group(1)
    # Trim any preamble before the document starts.
    for marker in ("<!DOCTYPE", "<!doctype", "<html"):
        idx = text.find(marker)
        if idx != -1:
            if idx > 0:
                text = text[idx:]
            break
    return text.strip()


def inject_preview_guards(html, business_name, author=config.PREVIEW_RIBBON_NAME):
    """Force noindex + preview ribbon into the page."""
    if 'name="robots"' not in html:
        m = re.search(r"<head[^>]*>", html, re.IGNORECASE)
        if m:
            html = html[:m.end()] + "\n  " + ROBOTS_META + html[m.end():]
        else:
            html = ROBOTS_META + "\n" + html

    ribbon = RIBBON_TEMPLATE.format(
        name=html_mod.escape(business_name or "this business", quote=False),
        author=html_mod.escape(author, quote=False),
    )
    if "</body>" in html:
        html = html.replace("</body>", ribbon + "\n</body>", 1)
    else:
        html += "\n" + ribbon
    return html


def build_payload(lead):
    """Map a ledger lead onto the exact prompt payload schema."""
    return {
        "business_name": lead["business_name"],
        "status": lead["lead_type"],
        "category": lead.get("category"),
        "address": lead.get("address"),
        "phone": lead.get("phone"),
        "rating": lead.get("rating"),
        "review_count": lead.get("review_count"),
        "hours": lead.get("hours"),
        "photo_urls": [],           # real photos come from the owner post-sale
        "services_or_menu": None,   # never invented; owner supplies after yes
        "existing_website_url": lead.get("website"),
    }


# --------------------------------------------------------------------------
# Generation
# --------------------------------------------------------------------------

def generate_site(lead, client, model):
    with open(config.PROMPT_PATH, encoding="utf-8") as f:
        template = f.read()
    prompt = template.replace("{payload}", json.dumps(build_payload(lead), indent=2))

    resp = client.messages.create(
        model=model,
        max_tokens=config.MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )
    if resp.stop_reason == "max_tokens":
        raise RuntimeError("response truncated at max_tokens — refusing to ship a half-built page "
                           "(raise MAX_TOKENS in config.py and rerun)")
    html = strip_fences(resp.content[0].text)
    if "</html>" not in html.lower():
        raise RuntimeError("output does not look like a complete HTML document")
    return inject_preview_guards(html, lead["business_name"])


def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        sys.exit("ANTHROPIC_API_KEY is not set.")
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    model = os.environ.get("CLAUDE_MODEL", config.DEFAULT_CLAUDE_MODEL)

    requested = set()
    if len(sys.argv) > 1 and sys.argv[1].strip():
        requested = {s.strip() for s in sys.argv[1].split(",") if s.strip()}

    ledger = load_ledger()
    to_build = [
        lead for lead in ledger["leads"].values()
        if lead.get("slug") and (
            lead["slug"] in requested or (not requested and lead.get("status") == "build")
        )
    ]
    if not to_build:
        print("Nothing to build. Flag leads by setting their status to \"build\" "
              "in leads.json, or pass slugs as an argument.")
        return

    if len(to_build) > config.MAX_BUILDS_PER_RUN:
        print(f"! {len(to_build)} leads flagged; capping this run at "
              f"{config.MAX_BUILDS_PER_RUN} (see MAX_BUILDS_PER_RUN in config.py). "
              "The rest stay flagged and build on the next run.")
        to_build = to_build[:config.MAX_BUILDS_PER_RUN]

    built, failed = 0, 0
    for lead in to_build:
        print(f"Building preview: {lead['business_name']} ({lead['slug']})")
        try:
            html = generate_site(lead, client, model)
        except Exception as e:  # one bad build must not kill the batch
            failed += 1
            print(f"  ! FAILED, lead left flagged for retry: {e}")
            continue
        out_dir = os.path.join(config.SITES_DIR, lead["slug"])
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(html)
        lead["status"] = "generated"
        lead["generated_at"] = today()
        lead["preview_path"] = f"sites/{lead['slug']}/"
        built += 1
        print(f"  -> {out_dir}/index.html")

    save_ledger(ledger)
    print(f"\nDone. Built {built} preview(s); {failed} failed.")
    if failed and not built:
        sys.exit(1)  # surface a fully-failed run in the Actions UI


if __name__ == "__main__":
    main()
