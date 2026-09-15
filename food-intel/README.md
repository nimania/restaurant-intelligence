# Food Industry Intelligence

A GitHub-native intelligence pipeline for food, restaurant, QSR, fast-casual, food-tech, operations, supply-chain, equipment, food-safety and food-manufacturing news.

## Current status — v0.4 Persian signals

- Collect RSS/Atom feeds automatically
- Normalize and deduplicate articles
- Classify industry categories and high-signal topics
- Score relevance from 0–100
- Detect known restaurant, food-tech, equipment and CPG brands
- Build 24h vs previous-6-day trend signals
- Publish a Persian-first dashboard while preserving publisher text in its original language
- Run collection and deployment with GitHub Actions

The source registry currently contains **28 registered sources, including 18 active feeds**.

## Persian layer

The Persian layer is intentionally metadata-only. It localizes:

- interface labels
- category names
- brand display names
- trend/signal labels
- aggregate counts and acceleration metrics

It does **not** translate or paraphrase publisher headlines, summaries or article bodies. Article text remains in the source language and links point to the original publisher.

## Directory

```text
food-intel/
├── config/
│   ├── brands.yml
│   └── sources.yml
├── data/
│   ├── news.json
│   └── signals.json
├── docs/
│   ├── PUBLISHING_POLICY.md
│   ├── SCHEMA.md
│   └── SOURCES.md
├── src/
│   ├── classify.py
│   ├── collect.py
│   ├── entities.py
│   ├── score.py
│   └── signals.py
├── tests/
│   ├── test_core.py
│   ├── test_entities_signals.py
│   └── test_sources.py
├── index.html
├── requirements.txt
└── README.md
```

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

Active sources cover restaurant/QSR, fast casual, operations, restaurant technology, food-tech, equipment, food manufacturing, food safety, cold chain, logistics and regulatory signals.

See `docs/SOURCES.md` for source tiers and `docs/PUBLISHING_POLICY.md` for publication rules.

## Current intelligence outputs

- relevance score per article
- detected brands per article
- Persian category labels
- trending topics in the last 24 hours
- trending brands in the last 24 hours
- acceleration compared with the previous six-day daily average
- searchable and filterable GitHub Pages dashboard

## Next milestones

1. Improve entity precision and expand the brand catalog.
2. Add 7-day and 30-day trend windows.
3. Add an Iran-relevance score without translating publisher content.
4. Add Persian/Iranian industry sources.
5. Add dedicated brand/topic views.
6. Add content-opportunity scoring for restaurant-industry creators and operators.
7. Feed selected signals into the broader Restaurant Intelligence project.

## Content policy

The project stores publisher metadata, URLs and short feed-provided descriptions. It does not mirror full article bodies and does not publish Persian translations of publisher article text.
