# Food Industry Intelligence

A lightweight, GitHub-native news intelligence pipeline for the food, restaurant, QSR, fast-casual, diner, food-tech, operations, supply-chain and food-manufacturing sectors.

## v0.1 scope

- Collect RSS/Atom feeds on a schedule
- Normalize articles into one schema
- Deduplicate by canonical URL and deterministic ID
- Apply rule-based industry categories and topic tags
- Store a compact JSON dataset in Git
- Run automatically with GitHub Actions
- Keep the architecture ready for AI summarization, Persian output, trend detection and a public dashboard

## Directory

```text
food-intel/
├── config/
│   └── sources.yml
├── data/
│   └── news.json
├── docs/
│   └── SCHEMA.md
├── src/
│   ├── classify.py
│   └── collect.py
├── requirements.txt
└── README.md
```

The scheduled workflow lives at `.github/workflows/food-intel-collect.yml`.

## Run locally

```bash
cd food-intel
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/collect.py
```

## Initial sources

The first working feeds are Restaurant Dive and Food Dive. Additional publishers are recorded as discovery targets in `config/sources.yml` and will be activated only after their feed endpoints are verified.

## Categories

The rule engine currently recognizes:

- QSR / Fast Food
- Fast Casual
- Restaurant Operations
- Menu & Product Innovation
- Restaurant Technology / AI
- Equipment & Automation
- Food Cost & Pricing
- Supply Chain
- Food Safety
- Labor & Management
- Franchising
- Delivery / Drive-Thru
- Consumer Behavior
- Marketing & Branding
- Beverage
- Food Manufacturing
- Ingredients & R&D
- Retail Food
- Regulation
- Sustainability

## Next milestones

1. Expand to 20–30 verified sources.
2. Add source-quality and relevance scoring.
3. Add named-entity extraction for brands, people and companies.
4. Add AI summaries and Persian summaries.
5. Add trend/signal detection over 24h, 7d and 30d windows.
6. Build a searchable GitHub Pages dashboard.
7. Feed selected signals into the broader Restaurant Intelligence project.

## Content policy

The dataset stores publisher metadata, URLs and short feed-provided summaries. It is not intended to mirror or republish full copyrighted articles.