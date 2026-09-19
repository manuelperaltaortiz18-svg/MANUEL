"""Rule set. Each rule scores one aspect of a listing and returns Findings.

A rule earns points out of its own maximum; pillars aggregate their rules and
the weighting in ``scoring.py`` turns pillars into the final 0-100 score.
Rules are pure functions of (listing, profile) so they are trivially testable.
"""

from __future__ import annotations

import re
from typing import Callable

from .findings import Finding
from .models import Listing
from .profiles import CategoryProfile

RULES: list[Callable[[Listing, CategoryProfile], list[Finding]]] = []


def rule(fn):
    RULES.append(fn)
    return fn


# Phrases Amazon's style guide bans outright in title/bullets/description.
PROHIBITED_PHRASES = [
    "best seller", "bestseller", "#1", "top rated", "free shipping", "sale",
    "cheap", "money back guarantee", "100% guarantee", "satisfaction guaranteed",
    "eco-friendly", "eco friendly", "non-toxic", "cures", "treats", "prevents",
    "fda approved", "clinically proven", "buy now", "limited time", "discount",
    "new arrival", "on sale", "lowest price",
]

# Claims that trigger restricted-claim review in consumables/beauty.
MEDICAL_CLAIMS = [
    "cures", "cure ", "heals", "treats", "treatment for", "prevents",
    "anti-bacterial", "antibacterial", "antiviral", "fda approved", "kills 99",
]

_WORD = re.compile(r"[a-z0-9áéíóúñü']+")


def tokens(text: str) -> list[str]:
    return _WORD.findall((text or "").lower())


def _f(pillar, code, earned, maximum, severity, message, fix=""):
    return Finding(pillar, code, round(float(earned), 3), float(maximum), severity, message, fix)


# ----------------------------------------------------------------- content
@rule
def title_rules(l: Listing, p: CategoryProfile) -> list[Finding]:
    out = []
    t = l.title or ""
    n = len(t)
    if n == 0:
        out.append(_f("content", "title.present", 0, 6, "critical", "No title.", "Write a title."))
        return out
    out.append(_f("content", "title.present", 6, 6, "pass", "Title present."))

    if n > p.title_max:
        out.append(_f("content", "title.length", 0, 5, "critical",
                      f"Title is {n} chars, over the {p.title_max} limit for {p.name}; Amazon may suppress it.",
                      f"Cut to {p.title_max} characters or fewer."))
    elif n < p.title_min:
        ratio = n / p.title_min
        out.append(_f("content", "title.length", 5 * ratio, 5, "medium",
                      f"Title is {n} chars, short of the {p.title_min} recommended for {p.name}.",
                      "Add qualified detail: brand, key attribute, size/quantity."))
    else:
        out.append(_f("content", "title.length", 5, 5, "pass", f"Title length {n} is in range."))

    if t[:1].islower():
        out.append(_f("content", "title.case", 0, 2, "low", "Title does not start with a capital.",
                      "Use title case; do not use ALL CAPS."))
    elif t.isupper():
        out.append(_f("content", "title.case", 0, 2, "medium", "Title is ALL CAPS, against Amazon style.",
                      "Use title case."))
    else:
        out.append(_f("content", "title.case", 2, 2, "pass", "Title casing looks fine."))

    if l.brand and l.brand.lower() not in t.lower():
        out.append(_f("content", "title.brand", 0, 3, "high", "Brand name missing from the title.",
                      "Lead the title with the brand."))
    else:
        out.append(_f("content", "title.brand", 3, 3, "pass", "Brand present in title."))

    toks = tokens(t)
    dupes = {w for w in toks if toks.count(w) > 2 and len(w) > 3}
    if dupes:
        out.append(_f("content", "title.stuffing", 0, 3, "high",
                      f"Keyword repeated in title: {', '.join(sorted(dupes))}.",
                      "Each keyword once; indexing gains nothing from repetition."))
    else:
        out.append(_f("content", "title.stuffing", 3, 3, "pass", "No keyword stuffing in title."))
    return out


@rule
def bullet_rules(l: Listing, p: CategoryProfile) -> list[Finding]:
    out = []
    bullets = [b for b in l.bullets if b and b.strip()]
    count = len(bullets)
    out.append(_f("content", "bullets.count", min(count, 5) / 5 * 8, 8,
                  "pass" if count >= 5 else ("critical" if count == 0 else "high"),
                  f"{count} of 5 bullet points used.",
                  "" if count >= 5 else "Fill all five bullets; each is indexed and read."))

    if not bullets:
        return out

    short = [b for b in bullets if len(b) < 80]
    long_ = [b for b in bullets if len(b) > 500]
    if long_:
        out.append(_f("content", "bullets.length", 0, 4, "high",
                      f"{len(long_)} bullet(s) exceed 500 chars and get truncated on mobile.",
                      "Keep each bullet between 120 and 250 characters."))
    elif short:
        out.append(_f("content", "bullets.length", 4 * (1 - len(short) / len(bullets)), 4, "medium",
                      f"{len(short)} bullet(s) under 80 chars carry little information.",
                      "Expand thin bullets to 120-250 characters."))
    else:
        out.append(_f("content", "bullets.length", 4, 4, "pass", "Bullet lengths are healthy."))

    leading = sum(1 for b in bullets if b.strip()[:1].isupper())
    out.append(_f("content", "bullets.format", leading / len(bullets) * 3, 3,
                  "pass" if leading == len(bullets) else "low",
                  f"{leading}/{len(bullets)} bullets open with a capitalised benefit label.",
                  "Open each bullet with a short capitalised label, then the benefit."))
    return out


@rule
def description_rules(l: Listing, p: CategoryProfile) -> list[Finding]:
    out = []
    d = (l.description or "").strip()
    if not d:
        out.append(_f("content", "description.present", 0, 5, "high", "No product description.",
                      "Write 1,000-2,000 characters of description (still indexed when A+ is absent)."))
    elif len(d) < 500:
        out.append(_f("content", "description.present", 5 * len(d) / 500, 5, "medium",
                      f"Description is only {len(d)} chars.", "Expand to at least 1,000 characters."))
    else:
        out.append(_f("content", "description.present", 5, 5, "pass", f"Description is {len(d)} chars."))

    if p.a_plus_expected:
        if not l.has_a_plus:
            out.append(_f("content", "description.aplus", 0, 6, "high",
                          "No A+ content. Amazon reports meaningful conversion lift from A+.",
                          "Publish at least 4 A+ modules if brand-registered."))
        else:
            mods = l.a_plus_modules or 1
            out.append(_f("content", "description.aplus", min(mods, 4) / 4 * 6, 6,
                          "pass" if mods >= 4 else "medium",
                          f"A+ content present with {mods} module(s).",
                          "" if mods >= 4 else "Add modules up to at least 4."))
        out.append(_f("content", "description.brandstory", 2 if l.has_brand_story else 0, 2,
                      "pass" if l.has_brand_story else "low",
                      "Brand Story present." if l.has_brand_story else "No Brand Story module.",
                      "" if l.has_brand_story else "Add Brand Story to cross-sell the catalogue."))
    return out


# ------------------------------------------------------------------- media
@rule
def image_rules(l: Listing, p: CategoryProfile) -> list[Finding]:
    out = []
    imgs = l.images
    n = len(imgs)
    out.append(_f("media", "images.count", min(n, p.min_images) / p.min_images * 10, 10,
                  "pass" if n >= p.min_images else ("critical" if n == 0 else "high"),
                  f"{n} image(s); {p.min_images} recommended for {p.name}.",
                  "" if n >= p.min_images else f"Upload at least {p.min_images} images."))
    if not imgs:
        return out

    main = [i for i in imgs if i.is_main] or imgs[:1]
    m = main[0]
    if m.has_white_background is False:
        out.append(_f("media", "images.main_bg", 0, 5, "critical",
                      "Main image is not on pure white (RGB 255,255,255); grounds for suppression.",
                      "Replace the main image with a pure-white-background shot."))
    elif m.has_white_background is None:
        out.append(_f("media", "images.main_bg", 2.5, 5, "medium",
                      "Main image background not verified.", "Confirm the main image is pure white."))
    else:
        out.append(_f("media", "images.main_bg", 5, 5, "pass", "Main image on white background."))

    small = [i for i in imgs if i.width and i.width < 1000 or i.height and i.height < 1000]
    unknown = [i for i in imgs if not i.width or not i.height]
    if small:
        out.append(_f("media", "images.resolution", max(0.0, 5 * (1 - len(small) / n)), 5, "high",
                      f"{len(small)} image(s) under 1000px; zoom will not activate.",
                      "Re-upload at 1600px on the longest side."))
    elif unknown:
        out.append(_f("media", "images.resolution", 3, 5, "low",
                      "Image dimensions unknown for some images.", "Record dimensions during ingest."))
    else:
        out.append(_f("media", "images.resolution", 5, 5, "pass", "All images are zoom-eligible."))

    kinds = {i.kind for i in imgs}
    wanted = {"lifestyle", "infographic", "dimensions"}
    have = kinds & wanted
    out.append(_f("media", "images.variety", len(have) / len(wanted) * 5, 5,
                  "pass" if have == wanted else "medium",
                  f"Image types present: {', '.join(sorted(kinds))}.",
                  "" if have == wanted else f"Add: {', '.join(sorted(wanted - have))}."))
    return out


@rule
def video_rules(l: Listing, p: CategoryProfile) -> list[Finding]:
    if not p.video_expected:
        return [_f("media", "video", 5, 5, "pass", "Video not expected in this category.")]
    if l.has_video:
        return [_f("media", "video", 5, 5, "pass", f"{max(l.video_count, 1)} video(s) present.")]
    return [_f("media", "video", 0, 5, "medium", "No product video.",
               "Add a 30-60s video; it occupies the gallery slot competitors use.")]


# ---------------------------------------------------------------- keywords
@rule
def backend_rules(l: Listing, p: CategoryProfile) -> list[Finding]:
    out = []
    st = l.backend_search_terms or ""
    nbytes = len(st.encode("utf-8"))
    if nbytes == 0:
        out.append(_f("keywords", "backend.present", 0, 8, "critical",
                      "Backend search terms are empty; 249 bytes of free indexing wasted.",
                      "Fill the search-terms field to just under 250 bytes."))
        return out
    if nbytes > 249:
        out.append(_f("keywords", "backend.present", 0, 8, "high",
                      f"Backend search terms are {nbytes} bytes; over 249 the whole field is ignored.",
                      "Trim below 250 bytes."))
    else:
        out.append(_f("keywords", "backend.present", 8 * min(nbytes / 200, 1.0), 8,
                      "pass" if nbytes >= 200 else "medium",
                      f"Backend search terms use {nbytes}/249 bytes.",
                      "" if nbytes >= 200 else "Use the remaining bytes on unranked long-tail terms."))

    if "," in st or ";" in st:
        out.append(_f("keywords", "backend.separators", 0, 3, "medium",
                      "Backend terms use commas/semicolons, which waste bytes.",
                      "Separate with single spaces only."))
    else:
        out.append(_f("keywords", "backend.separators", 3, 3, "pass", "Space-separated backend terms."))

    bt = tokens(st)
    dup = [w for w in set(bt) if bt.count(w) > 1]
    title_tokens = set(tokens(l.title)) | {w for b in l.bullets for w in tokens(b)}
    overlap = sorted(set(bt) & title_tokens - {"de", "the", "and", "para", "con", "for", "with"})
    penalty = 0.0
    msgs = []
    if dup:
        penalty += 2
        msgs.append(f"repeated terms ({', '.join(sorted(dup)[:5])})")
    if len(overlap) > len(set(bt)) * 0.3:
        penalty += 2
        msgs.append(f"{len(overlap)} terms already indexed from the title/bullets")
    out.append(_f("keywords", "backend.efficiency", max(0.0, 4 - penalty), 4,
                  "pass" if not msgs else "medium",
                  "Backend terms are efficient." if not msgs else "Wasted backend bytes: " + "; ".join(msgs),
                  "" if not msgs else "Backend is for terms NOT already in visible copy; never repeat."))

    if l.brand and l.brand.lower() in st.lower():
        out.append(_f("keywords", "backend.brand", 0, 2, "low",
                      "Own brand name repeated in backend terms (already indexed).",
                      "Remove it and reclaim the bytes."))
    else:
        out.append(_f("keywords", "backend.brand", 2, 2, "pass", "No brand repetition in backend."))
    return out


@rule
def keyword_coverage_rules(l: Listing, p: CategoryProfile) -> list[Finding]:
    targets = [k for k in l.target_keywords if k.strip()]
    if not targets:
        return [_f("keywords", "coverage", 4, 8, "low",
                   "No target keywords supplied, so coverage could not be measured.",
                   "Supply the 10-20 terms this ASIN must rank for.")]
    haystack = " ".join([l.title] + list(l.bullets) + [l.description, l.backend_search_terms]).lower()
    front = (l.title + " " + " ".join(l.bullets)).lower()
    covered = [k for k in targets if k.lower() in haystack]
    in_front = [k for k in targets if k.lower() in front]
    missing = [k for k in targets if k not in covered]
    score = 8 * (len(covered) / len(targets)) * (0.7 + 0.3 * (len(in_front) / max(len(targets), 1)))
    sev = "pass" if not missing else ("high" if len(missing) > len(targets) / 2 else "medium")
    return [_f("keywords", "coverage", score, 8, sev,
               f"{len(covered)}/{len(targets)} target keywords indexed, {len(in_front)} in title/bullets."
               + (f" Missing: {', '.join(missing[:6])}." if missing else ""),
               "" if not missing else "Place high-volume missing terms in the title/bullets, the rest in backend.")]


# -------------------------------------------------------------- attributes
@rule
def attribute_rules(l: Listing, p: CategoryProfile) -> list[Finding]:
    out = []
    attrs = {k.lower(): v for k, v in l.attributes.items() if v not in (None, "", [], {})}
    req = p.required_attributes
    missing_req = [a for a in req if a.lower() not in attrs]
    out.append(_f("attributes", "attrs.required",
                  (len(req) - len(missing_req)) / len(req) * 12 if req else 12, 12,
                  "pass" if not missing_req else "critical",
                  f"{len(req) - len(missing_req)}/{len(req)} required {p.name} attributes populated."
                  + (f" Missing: {', '.join(missing_req)}." if missing_req else ""),
                  "" if not missing_req else "Required attributes drive filters and browse placement; fill them."))

    rec = p.recommended_attributes
    missing_rec = [a for a in rec if a.lower() not in attrs]
    out.append(_f("attributes", "attrs.recommended",
                  (len(rec) - len(missing_rec)) / len(rec) * 6 if rec else 6, 6,
                  "pass" if not missing_rec else "medium",
                  f"{len(rec) - len(missing_rec)}/{len(rec)} recommended attributes populated."
                  + (f" Missing: {', '.join(missing_rec)}." if missing_rec else ""),
                  "" if not missing_rec else "Each filled attribute adds a refinement filter you can be found through."))

    out.append(_f("attributes", "attrs.browse_node", 4 if l.browse_node else 0, 4,
                  "pass" if l.browse_node else "high",
                  "Browse node set." if l.browse_node else "No browse node / category assignment recorded.",
                  "" if l.browse_node else "Wrong or missing browse node is the single most common cause of invisibility."))

    if l.variation_parent or l.variation_count:
        out.append(_f("attributes", "attrs.variations", 3, 3, "pass",
                      f"Part of a variation family ({l.variation_count} children)."))
    else:
        out.append(_f("attributes", "attrs.variations", 1.5, 3, "low",
                      "Standalone ASIN with no variation family.",
                      "If sizes/colours exist as separate ASINs, merge them; reviews pool across the family."))
    return out


# -------------------------------------------------------------- compliance
@rule
def compliance_rules(l: Listing, p: CategoryProfile) -> list[Finding]:
    out = []
    copy = " ".join([l.title] + list(l.bullets) + [l.description]).lower()
    hits = sorted({ph for ph in PROHIBITED_PHRASES if ph in copy})
    out.append(_f("compliance", "policy.phrases", 0 if hits else 8, 8,
                  "critical" if hits else "pass",
                  f"Prohibited promotional phrasing found: {', '.join(hits)}." if hits
                  else "No prohibited promotional phrasing.",
                  "Remove these; they are grounds for listing suppression." if hits else ""))

    med = sorted({ph.strip() for ph in MEDICAL_CLAIMS if ph in copy})
    out.append(_f("compliance", "policy.claims", 0 if med else 6, 6,
                  "critical" if med else "pass",
                  f"Unsubstantiated health/medical claims: {', '.join(med)}." if med
                  else "No restricted health claims detected.",
                  "Remove or substantiate with documentation Amazon accepts." if med else ""))

    if re.search(r"https?://|www\.", copy):
        out.append(_f("compliance", "policy.links", 0, 3, "critical",
                      "External URL in listing copy.", "Remove; off-Amazon links are prohibited."))
    else:
        out.append(_f("compliance", "policy.links", 3, 3, "pass", "No external links."))

    if re.search(r"\b[\w.]+@[\w.]+\.\w+\b|\+?\d[\d\s().-]{7,}\d", copy):
        out.append(_f("compliance", "policy.contact", 0, 3, "critical",
                      "Contact details (email/phone) in listing copy.",
                      "Remove; buyer-seller contact outside Amazon is prohibited."))
    else:
        out.append(_f("compliance", "policy.contact", 3, 3, "pass", "No contact details in copy."))
    return out


# ------------------------------------------------------------- advertising
@rule
def advertising_rules(l: Listing, p: CategoryProfile) -> list[Finding]:
    out = []
    if l.sponsored_products:
        out.append(_f("advertising", "ads.sp", 6, 6, "pass", "Sponsored Products running."))
    else:
        out.append(_f("advertising", "ads.sp", 0, 6, "high", "No Sponsored Products campaign on this ASIN.",
                      "Organic rank on Amazon is partly bought; an unadvertised new ASIN rarely ranks."))
    out.append(_f("advertising", "ads.sb", 3 if l.sponsored_brands else 1, 3,
                  "pass" if l.sponsored_brands else "low",
                  "Sponsored Brands running." if l.sponsored_brands else "No Sponsored Brands coverage.",
                  "" if l.sponsored_brands else "Optional; only worth it with a multi-ASIN catalogue."))

    if l.sponsored_products:
        n = l.ad_keyword_count
        out.append(_f("advertising", "ads.keywords", min(n, 30) / 30 * 4, 4,
                      "pass" if n >= 30 else "medium",
                      f"{n} targeted ad keyword(s).",
                      "" if n >= 30 else "Thin targeting; run broad/auto discovery to harvest terms."))
    else:
        out.append(_f("advertising", "ads.keywords", 0, 4, "medium", "No ad targeting (no campaign).", ""))

    if l.buybox_won is False:
        out.append(_f("advertising", "ads.buybox", 0, 4, "critical",
                      "Buy Box not won; ads and organic traffic convert far worse without it.",
                      "Fix price/fulfilment/seller metrics before spending on ads."))
    elif l.buybox_won is None:
        out.append(_f("advertising", "ads.buybox", 2, 4, "low", "Buy Box status unknown.", "Record it during ingest."))
    else:
        out.append(_f("advertising", "ads.buybox", 4, 4, "pass", "Buy Box won."))
    return out


# ---------------------------------------------------------------- customer
@rule
def customer_rules(l: Listing, p: CategoryProfile) -> list[Finding]:
    out = []
    n = l.review_count
    out.append(_f("customer", "reviews.count", min(n, 50) / 50 * 7, 7,
                  "pass" if n >= 50 else ("critical" if n < 5 else "medium"),
                  f"{n} review(s); conversion flattens out around 50.",
                  "" if n >= 50 else "Enrol in Vine and enable Request a Review automation."))

    r = l.rating
    if r is None:
        out.append(_f("customer", "reviews.rating", 3.5, 7, "low", "Star rating unknown.", "Record it during ingest."))
    elif r < 3.5:
        out.append(_f("customer", "reviews.rating", 0, 7, "critical",
                      f"Rating {r:.1f} is below the 3.5 threshold where traffic collapses.",
                      "Read 1-2 star reviews for the defect pattern; fix the product or the expectation set by the copy."))
    else:
        out.append(_f("customer", "reviews.rating", (r - 3.5) / 1.5 * 7, 7,
                      "pass" if r >= 4.3 else "medium", f"Rating {r:.1f}.",
                      "" if r >= 4.3 else "Below 4.3 costs conversion against category peers."))

    q = l.answered_questions
    out.append(_f("customer", "reviews.qa", min(q, 10) / 10 * 3, 3,
                  "pass" if q >= 10 else "low", f"{q} answered customer question(s).",
                  "" if q >= 10 else "Unanswered questions are objections left standing on the page."))

    if l.return_rate is None:
        out.append(_f("customer", "reviews.returns", 1.5, 3, "low", "Return rate unknown.", ""))
    elif l.return_rate > 0.10:
        out.append(_f("customer", "reviews.returns", 0, 3, "high",
                      f"Return rate {l.return_rate:.1%} exceeds the 10% NCX warning band.",
                      "High returns trigger the 'frequently returned' badge, which halves conversion."))
    else:
        out.append(_f("customer", "reviews.returns", 3, 3, "pass", f"Return rate {l.return_rate:.1%}."))
    return out


def run_rules(listing: Listing, profile: CategoryProfile) -> list[Finding]:
    findings: list[Finding] = []
    for fn in RULES:
        findings.extend(fn(listing, profile))
    return findings
