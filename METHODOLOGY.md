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
