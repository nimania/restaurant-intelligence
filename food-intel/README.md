# Food Industry Intelligence

A lightweight, GitHub-native news intelligence pipeline for the food, restaurant, QSR, fast-casual, diner, food-tech, operations, supply-chain and food-manufacturing sectors.

## Current status — v0.2 source expansion

- Collect RSS/Atom feeds on a schedule
- Normalize articles into one schema
- Deduplicate by canonical URL and deterministic ID
- Apply rule-based industry categories and topic tags
- Store a compact JSON dataset in Git
- Run automatically with GitHub Actions
- Maintain a curated source registry with verification metadata and priority tiers
- Keep the architecture ready for AI summarization, Persian output, trend detection and a public dashboard

The v0.2 registry currently contains **28 sources: 18 active feeds and 10 discovery targets**.

## Directory

```text
food-intel/
├── config/
│   └── sources.yml
├── data/
│   └── news.json
├── docs/
│   ├── SCHEMA.md
│   └── SOURCES.md
├── src/
│   ├── classify.py
│   └── collect.py
├── tests/
│   ├── test_core.py
│   └── test_sources.py
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
python -m unittest discover -s tests -p "test_*.py"
python src/collect.py
```

## Source coverage

Active sources now cover:

- Restaurant / QSR / fast casual
- Restaurant operations and management
- Restaurant technology and AI
- Food-tech and kitchen automation
- Foodservice equipment and kitchen design
- Food manufacturing and processing
- Food safety, recalls and outbreaks
- Cold-chain and logistics
- Regulatory signals

See `docs/SOURCES.md` for the source policy, priority tiers and discovery queue.

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

1. Add source-quality and relevance scoring using the new priority metadata.
2. Add named-entity extraction for brands, people and companies.
3. Add AI summaries and Persian summaries.
4. Add trend/signal detection over 24h, 7d and 30d windows.
5. Add Persian/Iranian industry sources and a separate corporate-announcement source class.
6. Build a searchable GitHub Pages dashboard.
7. Feed selected signals into the broader Restaurant Intelligence project.

## Content policy

The dataset stores publisher metadata, URLs and short feed-provided summaries. It is not intended to mirror or republish full copyrighted articles.
