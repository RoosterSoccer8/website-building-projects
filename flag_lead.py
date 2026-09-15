"""Apply a status change requested from the dashboard.

The dashboard's buttons open a GitHub issue titled "<action>: <slug>".
The flag workflow runs this with that title; it validates the request and
updates leads.json. Nothing here trusts the issue text beyond matching it
against the allow-list below.

Usage:  python flag_lead.py "build: tony-s-pizza-abc123"
Prints a one-line result (posted back as the issue comment) and exits
non-zero if the request could not be applied.
"""

import re
import sys

from scanner import load_ledger, save_ledger

# Only these transitions can be requested from a phone. "build" is the one
# that spends money, so it is deliberately the only one that triggers work.
ALLOWED = {"build", "pitched", "replied", "sold", "dead"}

TITLE_RE = re.compile(r"^\s*([a-z]+)\s*:\s*([A-Za-z0-9\-]+)\s*$", re.IGNORECASE)


def parse_title(title):
    """Return (action, slug) or raise ValueError."""
    m = TITLE_RE.match(title or "")
    if not m:
        raise ValueError(
            'Could not read that request. Expected a title like "build: some-slug".')
    action, slug = m.group(1).lower(), m.group(2).lower()
    if action not in ALLOWED:
        raise ValueError(
            f'"{action}" is not something I can do. Allowed: {", ".join(sorted(ALLOWED))}.')
    return action, slug


def apply(title, ledger):
    """Apply the request to the ledger. Returns (message, action, lead)."""
    action, slug = parse_title(title)

    lead = next((l for l in ledger["leads"].values() if l.get("slug") == slug), None)
    if lead is None:
        raise ValueError(f'No lead found with slug "{slug}".')

    if lead.get("status") == action:
        return (f'{lead["business_name"]} is already marked **{action}** — nothing to do.',
                None, lead)

    previous = lead.get("status")
    lead["status"] = action
    msg = f'{lead["business_name"]}: **{previous} → {action}**'
    if action == "build":
        msg += "\n\nBuilding the preview now — this issue will update with the link."
    return msg, action, lead


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: flag_lead.py \"<action>: <slug>\"")

    ledger = load_ledger()
    try:
        message, action, lead = apply(sys.argv[1], ledger)
    except ValueError as e:
        print(f"RESULT:{e}")
        sys.exit(1)

    save_ledger(ledger)
    print(f"RESULT:{message}")
    # Consumed by the workflow to decide whether to run the generator.
    print(f"ACTION:{action or ''}")
    print(f"SLUG:{lead.get('slug', '')}")


if __name__ == "__main__":
    main()
