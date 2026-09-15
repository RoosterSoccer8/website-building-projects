"""Central configuration for the South Philly lead pipeline."""

# ---- Geography -------------------------------------------------------------
# South Philadelphia zip codes used to filter search results.
TARGET_ZIPS = {"19145", "19146", "19147", "19148"}

# Query areas. Each category is searched against each area.
# More areas = better coverage but more billed Text Search calls.
AREAS = [
    "South Philadelphia, Philadelphia, PA",
    "East Passyunk, Philadelphia, PA",
    "Point Breeze, Philadelphia, PA",
]

# ---- Rotating category schedule (Mon=0 ... Sun=6) --------------------------
# Each weekday scans a different slice so the daily run stays cheap and the
# lead drip stays fresh instead of re-searching the same queries.
CATEGORY_ROTATION = {
    0: ["restaurants", "pizza restaurants", "delis"],
    1: ["barber shops", "hair salons", "nail salons"],
    2: ["general contractors", "plumbers", "electricians"],
    3: ["auto repair shops", "car detailing"],
    4: ["bakeries", "cafes", "corner stores"],
    5: ["gyms", "cleaning services", "florists"],
    6: ["tattoo shops", "pet groomers", "laundromats"],
}

# ---- Website audit ---------------------------------------------------------
# A site is only marked OUTDATED_WEBSITE if the audit finds real problems.
STALE_COPYRIGHT_BEFORE = 2023  # copyright year older than this = stale signal
AUDIT_TIMEOUT_SECONDS = 12

# Hosts that mean "this business has no real website, just a profile page".
SOCIAL_ONLY_HOSTS = (
    "facebook.com", "instagram.com", "linktr.ee", "yelp.com",
    "doordash.com", "grubhub.com", "ubereats.com", "squareup.com",
    "business.site",  # dead Google Business sites product
)

PARKED_PHRASES = (
    "this domain is for sale", "buy this domain", "domain parking",
    "parked free", "godaddy.com/domains", "is parked",
)

# ---- Generation ------------------------------------------------------------
# Model for site generation. Override with env var CLAUDE_MODEL.
DEFAULT_CLAUDE_MODEL = "claude-sonnet-5"
MAX_TOKENS = 16000
MAX_BUILDS_PER_RUN = 10  # cost guard: cap Claude builds per workflow run

# Creative direction. Every build gets a fresh random seed so no two sites
# come out looking like the same template; the business's own photos then
# pull that direction toward what the place actually looks like.
SEED_LENGTH = 48
REFERENCE_PHOTOS = 3          # Google photos shown to the model (design input only)
REFERENCE_PHOTO_WIDTH = 800   # px; bigger costs more tokens for no design benefit

PREVIEW_RIBBON_NAME = "Connor"  # who the ribbon credits

# ---- Files -----------------------------------------------------------------
LEDGER_PATH = "leads.json"
SITES_DIR = "docs/sites"
DASHBOARD_PATH = "docs/index.html"
PROMPT_PATH = "prompts/site_prompt.txt"
