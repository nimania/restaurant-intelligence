# Methodology

Restaurant Intelligence is intended to distinguish between collected observations, derived metrics, and interpretation.

## Evidence hierarchy

When possible, prefer sources in roughly this order:

1. Primary sources such as official restaurant websites, menus, filings, or first-party announcements.
2. Directly observable public information such as published prices, locations, and opening hours.
3. Reputable secondary reporting or industry sources.
4. User-generated or community sources, clearly identified as such.

## Collection context

For information that can change over time, record or expose the collection date where practical. Historical values should not be presented as current without qualification.

## Derived information

Calculated values, rankings, scores, and classifications should be documented sufficiently for another contributor to understand the inputs and assumptions.

## Launch planner: properties and equipment

The launch planner combines three different kinds of information and keeps their roles separate:

1. The existing feasibility model estimates a viable concept, location zone, setup cost and operating threshold.
2. Divar MCP supplies current public asking-price leads for commercial properties and used equipment.
3. Digikala MCP supplies current public product offers when its retail catalogue contains a sufficiently relevant match.

The equipment catalogue in `data/equipment-catalog.json` is a planning template. Its weights divide the existing setup estimate; they do not add a second equipment cost on top of that estimate. Specifications are minimum planning prompts and must be confirmed against the final menu, expected peak throughput, utilities and selected property.

### Property lead score

Live property leads are ranked client-side using observable inputs only:

- deposit plus three months of advertised rent relative to the user's capital;
- area parsed from the ad title when explicitly present;
- concept-relevant words in the title;
- photo count;
- exclusion of prices flagged as placeholders by the source.

The score is a search-priority score, not a valuation or a prediction of restaurant success. Missing area is treated as unknown. The app does not claim that a removed ad was sold.

### Property-readiness analysis

For a shortlisted property, the planner can request the full public Divar ad record and compare only the text and fields actually present against concept-specific launch requirements. Every requirement is labelled as **confirmed in the ad**, **explicit risk**, or **unknown and requiring a visit question**.

The readiness percentage measures evidence coverage in the ad. It is not an engineering inspection, permit approval or prediction of success. Unknown information is not treated as proof that an amenity is absent. The capital check combines the advertised deposit and three months of advertised rent with the existing concept setup estimate; construction, repair and compliance work still require separate quotes after a site visit.

### Equipment policy

Each equipment item carries one of four planning policies: new-priority, used-inspected, used-friendly or hybrid. These are risk-management defaults, not endorsements of a particular listing. Gas, electrical, refrigeration, pressure-bearing and high-temperature equipment require qualified inspection before purchase.

Live marketplace results are deliberately presented as leads. The app exposes their source and links back to the original listing or product page. A Digikala result that looks consumer-grade is explicitly warned about because retail search may only partially match an industrial query.

### Source and freshness limits

Both marketplace connectors read undocumented public upstream APIs that can change. Results are fetched in the browser when the user reaches the recommendation or requests offers. Asking prices can change and are not transaction prices. The application does not collect phone numbers, credentials or private seller information.

## Uncertainty

Missing information is not evidence of absence. When coverage is incomplete or a source cannot be verified, the project should say so rather than silently infer a fact.

## Corrections

Corrections should preserve traceability when practical. Source changes, methodology changes, and material corrections should be described in commits or pull requests.

## Privacy and responsible use

The project is intended for public-market and restaurant intelligence. It should not collect or expose private customer data, credentials, or sensitive personal information.


## Karaj benchmark (preliminary, 2026-09-26)

Karaj zone inputs in `app.js` (`KARAJ_ZONES`) come from a desk sample, not a field survey:

- **Rent and deposit per m²:** median asking prices of 25–150 m² shop ads on Divar neighbourhood pages for Azimieh, Jahanshahr, Gohardasht, Mehrshahr (phase 4), Baghestan and Golshahr, retrieved 2026-09-26. Samples are small (4–11 ads per zone). These are asking prices, not contract rents.
- **Active venues and review volume:** a Google Maps sample of about 115 food-service venues found by zone-specific searches. Search results are capped, so counts show relative presence, not a full census.
- **Demand index:** 0.6 × review-volume index + 0.4 × rent index (both scaled to the top zone = 100).
- **Concept whitespace (`w`):** how much each concept family (fast food, café, traditional) is under-represented in a zone compared with the Karaj-wide sample mix.
- **Confidence:** 0.58–0.72, scaled by rent-sample size. All values are below the 0.75 threshold, so **the low-risk mode shows no Karaj options** until the benchmark is checked on the ground.
- **Shared assumptions:** concept setup cost, average check and payroll are the same as in Nowshahr. Karaj-specific check sizes and wages have not been measured yet.

Next steps to raise confidence: a larger ad sample per zone, main-street versus side-street rent split, field counts of active venues, and Karaj average-check data.


## Mashhad benchmark (preliminary, re-measured 2026-09-26)

- **Rent and deposit per m²:** median asking rent and deposit per m² of 25–200 m² `shop-rent` ads on Divar, retrieved 2026-09-26. Each ad was assigned to a zone by the district Divar records on the ad itself, not by the search page it appeared on (Divar pads thin neighbourhood pages with nearby ads). Ads with rent or deposit under 1 million toman (full-rahn, placeholder or "agreed" prices) were dropped. Districts and sample sizes:
  - M01 Sajjad–Baharestan: Sajjadshahr, Shahrak-e Baharestan — 49 ads
  - M02 Ahmadabad–Kuhsangi–Rezashahr: Ahmadabad, Rezashahr, Kuhsangi — 75 ads
  - M03 Vakilabad–Kowsar: Kuy-e Kowsar, Vakilabad — 63 ads (Hashemiyeh could not be queried separately)
  - M04 Haram–Imam Reza: Imam Reza (AS) St, Onsori, Bala-Khiaban, Charbagh, Payin-Khiaban, Holy Shrine, Noghan — 43 ads
  - M05 Ghasemabad–Shahrak-e Gharb–Shahed: Shahed, Shahrak-e Emam Hadi, Ghasemabad — 49 ads
  - M06 Tollab–Tabarsi: North Tabarsi, Tollab, Tabarsi — 16 ads
- These are asking prices, not contract rents. Spread inside each zone is wide (for example, Sajjad's interquartile range is roughly 0.6–4 million toman per m²), because main-street and side-street shops are still mixed.
- This pass replaced the earlier Mashhad figures, which were several times lower than the current Divar medians and covered only three zones.
- **Active venues and review volume:** a Google Maps sample of about 94 food-service venues found by zone-specific searches.
- **Demand index:** 0.6 × review-volume index + 0.4 × rent index (both scaled to the top zone = 100).
- **Pilgrim market:** the Haram zone is tagged «بازار زائر · فصلی». Pilgrim demand is concentrated in holidays and religious occasions and is only partly reflected in local review volume.
- **Confidence:** 0.62 at 6 ads, rising linearly to a cap of 0.72 at 18+ ads (Tollab–Tabarsi: 0.70). All are below the 0.75 threshold, so the low-risk mode still shows no Mashhad options until main-street versus side-street rents are split and checked on the ground.

## Cross-city comparison

Demand and whitespace scores are relative to each city's own zones, so they are **not** compared across cities. The cross-city card compares only absolute figures from the same model: capital needed, estimated monthly rent and daily orders needed to break even. Concept economics are shared across cities, so differences come from rent, deposit and zone mix. They do not come from local prices or wages.
