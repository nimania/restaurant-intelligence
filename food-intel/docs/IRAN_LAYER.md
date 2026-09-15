# Iran Industry Layer — v0.5

The Iran layer extends Food Industry Intelligence with Persian-language and Iran-market coverage while keeping the global radar intact.

## Coverage goals

The layer is designed to capture:

- Iranian food and beverage brands
- restaurant, cafe, QSR and catering businesses
- industrial kitchen and food-processing equipment
- packaging, labels, printing and packaging machinery
- restaurant/cafe interior design and decor
- branding, advertising and visual identity
- food technology, delivery platforms, AI and automation
- ingredients, manufacturing, distribution and cold-chain signals
- food regulation, safety, pricing and market structure

## Source strategy

Three source tiers are used:

1. **Specialist industry sources** — accepted without keyword gating because the whole publication is relevant.
2. **Technology media** — retained only when an article matches food/restaurant/platform keywords.
3. **General Iranian news** — aggressively keyword-filtered so unrelated politics, sports and general economy do not pollute the dataset.

The active Iran registry lives in `config/sources_iran.yml`.

## Active feeds

- IranPack — packaging, design, machinery and materials
- iFoods Magazine — food industry, restaurant, industrial kitchen, equipment and packaging
- Digiato technology feed — filtered for restaurant/food-delivery/food-tech stories
- ISNA — keyword-filtered food-industry radar
- Mehr News — keyword-filtered food-industry radar
- Tasnim Economy — keyword-filtered food-industry radar
- YJC — keyword-filtered food-industry radar
- Tabnak — keyword-filtered food-industry radar

## Discovery queue

High-value sources that need a stable machine-readable endpoint or dedicated adapter:

- Foodna — specialist food-industry source; legacy sectional RSS endpoints are advertised, including machinery and packaging, but stable HTTPS ingestion still needs verification.
- Foodpress / Eghtesade Ghaza — active specialist food/agriculture newsroom; public channel and site are active but a stable feed/adapter is still needed.
- Iranco Magazine — useful factory, brand, FMCG and export coverage; stable RSS endpoint not confirmed.

## Filtering

Broad sources use `include_keywords`. The collector normalizes Persian Yeh/Kaf and zero-width non-joiners before matching, so variants such as `فست فود` / `فست‌فود` and `بسته بندی` / `بسته‌بندی` are handled consistently.

Each source reports:

- `entries_seen`
- `entries_matched`
- feed parsing status

This allows tuning filters based on real collection runs.

## Iran relevance

Each retained item receives `iran_relevance_score` from 0 to 100. The score is boosted by:

- an Iran-market source
- explicit references to Iran
- detected Iranian brands/companies
- high-signal industry terminology

The dedicated dashboard is published at `/food-intel/iran.html`.

## Update cadence

The existing GitHub Actions collector runs every three hours. Iran sources are collected in the same run as global sources, so no separate scheduler is required.
