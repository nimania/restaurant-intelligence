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


## Rent benchmark method (all cities, 2026-09-26)

Nowshahr, Karaj and Mashhad zone rents were re-measured on 2026-09-26 with one method:

- **Sample:** all `shop-rent` ads on Divar for the zone's districts, 25–200 m², with rent and deposit of at least 1 million toman (full-rahn, placeholder and "agreed" prices are dropped). Each ad is assigned to a zone by the district Divar records on the ad itself, because Divar pads thin district pages with nearby ads. Nowshahr has no Divar districts, so ads are assigned by the street named in the ad's location, then its title and description; ads that name no zone street are left out.
- **Main street vs. side street:** an ad counts as main-street when its title or description says so (حاشیه, بر خیابان/بلوار, نبش, دونبش, تابلوخور, خیابان اصلی, پرتردد …). Sellers rarely say "side street", so the other group is "not stated as main street" (side streets, malls and unclear ads).
- **Zone rent (`rent`, `deposit`):** median asking rent and deposit per m² of main-street ads when there are at least 6, because a restaurant usually needs frontage; otherwise the median of all ads (`rent_basis`). `rent_other` is the median of the other group.
- **Confidence:** `0.5 + 0.25 × min(1, n / 20) + 0.2 × clamp(1.5 − relative IQR, 0, 1)`, where `n` is the number of ads behind the rent and relative IQR is (Q3 − Q1) / median of their rent per m². With fewer than 12 ads the confidence is capped at 0.70, so a small sample never reaches the 0.75 low-risk threshold. Zones with fewer than 3 ads keep their previous rent and get at most 0.55.
- **Demand index:** 0.6 × review-volume index + 0.4 × rent index (both scaled to the city's top zone = 100).
- These are asking prices, not contract rents, and have not been checked on the ground.

### Samples (ads behind the rent / all ads)

| City | Zone | Basis | Ads |
|---|---|---|---|
| Mashhad | M01 Sajjad–Baharestan | main street | 35 / 49 |
| Mashhad | M02 Ahmadabad–Kuhsangi–Rezashahr | main street | 47 / 75 |
| Mashhad | M03 Vakilabad–Kowsar | main street | 50 / 69 |
| Mashhad | M04 Haram–Imam Reza | main street | 15 / 43 |
| Mashhad | M05 Ghasemabad–Shahed | main street | 34 / 49 |
| Mashhad | M06 Tollab–Tabarsi | main street | 9 / 16 |
| Karaj | K01 Azimieh | main street | 27 / 65 |
| Karaj | K02 Jahanshahr | main street | 8 / 17 |
| Karaj | K03 Gohardasht | main street | 68 / 120 |
| Karaj | K04 Mehrshahr (all phases) | main street | 24 / 53 |
| Karaj | K05 Baghestan–Shahinvilla | main street | 32 / 96 |
| Karaj | K06 Golshahr–Mehrvilla | main street | 58 / 115 |
| Nowshahr | Z01 15 Khordad | previous value | 1 |
| Nowshahr | Z02 Karimi | main street | 6 / 9 |
| Nowshahr | Z03 Ferdowsi–Saadi | previous value | 2 |
| Nowshahr | Z04 Imam Reza–Daryasar | all ads | 7 |
| Nowshahr | Z05 Haft-e Tir–Kargar | all ads | 5 |
| Nowshahr | Z06 Airport–Amirrud | all ads | 6 |

Mashhad Haram (M04) is tagged «بازار زائر · فصلی»: pilgrim demand peaks in holidays and religious occasions and is only partly reflected in local review volume. Active-venue counts, review volumes and concept whitespace (`w`) still come from the earlier Google Maps samples. Concept setup cost, average check and payroll are shared across cities.

Next steps: field checks of a few main-street rents per zone, more Nowshahr sources, and local average-check and wage data.

## Cross-city comparison

Demand and whitespace scores are relative to each city's own zones, so they are **not** compared across cities. The cross-city card compares only absolute figures from the same model: capital needed, estimated monthly rent and daily orders needed to break even. Concept economics are shared across cities, so differences come from rent, deposit and zone mix. They do not come from local prices or wages.
