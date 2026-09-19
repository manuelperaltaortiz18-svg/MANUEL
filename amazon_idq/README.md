# amazon-idq — proxy listing-quality auditor

Audits an Amazon listing across seven pillars and produces a 0–100 score, a
list of policy blockers, and a fix list ranked by points recoverable.

## What this is not

**This is not Amazon's IDQ.** Amazon's *Item Data Quality* score (Vendor
Central / retail, measures catalogue attribute completeness and accuracy) and
the Seller Central *Listing Quality Dashboard* are both proprietary. Their
weights are undisclosed and vary by category and over time. Nothing here
reverse-engineers them.

What this produces is an **auditable proxy**: explicit rules, explicit
weights, a full trace of every check. The intended workflow is to recalibrate
`DEFAULT_WEIGHTS` in `amazon_idq/scoring.py` against your own listings once
you can observe their real LQD values. Until then, treat the **pillar
breakdown and the fix list as the product**, and the headline number as a
convenience for sorting a catalogue.

## Pillars and default weights

| Pillar | Weight | Covers |
|---|---:|---|
| content | 22 | title length/case/brand/stuffing, 5 bullets, description, A+ modules, Brand Story |
| attributes | 20 | category-required and recommended attributes, browse node, variation family |
| media | 18 | image count, white-background main, 1000px zoom eligibility, image-type variety, video |
| keywords | 15 | backend search terms (249-byte limit, separators, wasted repetition), target-keyword coverage and placement |
| compliance | 10 | prohibited promotional phrasing, health claims, external links, contact details |
| customer | 10 | review count, star rating, answered questions, return rate |
| advertising | 5 | Sponsored Products/Brands presence, targeting depth, Buy Box |

Category expectations (title bounds, image count, required attributes) live in
`amazon_idq/profiles.py`: `beauty`, `grocery`, `electronics`, `apparel`,
`home`, plus a `default`. Add your own there.

## Usage

```bash
python -m amazon_idq samples/bad_listing.json            # terminal report
python -m amazon_idq samples/good_listing.json --verbose # every check, not just failures
python -m amazon_idq listings.json --json                # machine-readable
python -m amazon_idq listings.json --fail-under 70       # exit 1 below threshold (CI gate)
```

The input is one listing object or a JSON list of them. Fields are documented
in `amazon_idq/models.py`; every field except `asin` and `category` is
optional, and an absent field is scored as *unknown* rather than silently
ignored.

```python
from amazon_idq import Listing, score_listing, render

result = score_listing(Listing.from_dict(payload))
print(result.score, result.grade)
for f in result.top_fixes(5):
    print(f.code, f.fix)
```

## Tests

```bash
cd amazon_idq && python -m pytest tests -q
```

## Adding a rule

Write a function in `amazon_idq/rules.py`, decorate it with `@rule`, return a
list of `Finding`. Each finding names its pillar, earns points out of its own
maximum, and carries a `fix` string. Aggregation and ranking are automatic.

## Known limits

- Rules are static analysis of supplied data. Nothing here scrapes Amazon;
  ingest is your problem (SP-API `getCatalogItem` / `getListingsItem` maps
  cleanly onto `Listing`).
- Prohibited-phrase matching is substring-based and will produce false
  positives (e.g. "treats" in a pet-food listing). Review blockers by hand.
- Review *quality* (recency, verified share, topic of complaints) is not
  analysed — only counts and the aggregate rating.
- The weights are a starting hypothesis, not a measurement.
