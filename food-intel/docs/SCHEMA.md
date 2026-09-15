# News record schema — v0.4

Each article in `data/news.json` is normalized to the following logical schema.

| Field | Type | Description |
|---|---|---|
| `id` | string | Deterministic 20-character SHA-256 prefix |
| `title` | string | Publisher/feed title in the original source language |
| `url` | string | Canonicalized publisher URL with common tracking parameters removed |
| `source` | object | Source id, name, homepage, class and priority |
| `author` | string/null | Feed-provided author when available |
| `published_at` | ISO-8601 string | UTC publication/update time |
| `collected_at` | ISO-8601 string | UTC first-seen time |
| `language` | string | Source language |
| `region` | string/null | Geographic focus of source |
| `summary` | string | Short feed-provided description in the original source language, capped at 1,200 chars |
| `categories` | string[] | Rule-based industry categories |
| `topics` | string[] | High-signal topic tags |
| `brands` | object[] | Detected brand id, canonical name and Persian display label |
| `relevance_score` | number | Deterministic 0–100 ranking score |

There is intentionally no translated-title or Persian-summary field in v0.4.

## News dataset envelope

```json
{
  "schema_version": "0.4",
  "generated_at": "2026-09-15T00:00:00Z",
  "count": 0,
  "active_sources": 0,
  "entries_processed_this_run": 0,
  "source_status": [],
  "items": []
}
```

## Signal dataset

`data/signals.json` contains aggregate metadata only:

```json
{
  "schema_version": "0.4",
  "generated_at": "2026-09-15T00:00:00Z",
  "articles_24h": 0,
  "articles_previous_6d": 0,
  "trending_topics": [],
  "trending_brands": [],
  "radar_fa": ""
}
```

Trend entries contain a Persian display label, current 24-hour mention count, the previous six-day daily average and an acceleration ratio.

## Design rules

- Do not store full publisher article bodies.
- Do not translate or paraphrase publisher article text for publication.
- Persian labels are limited to taxonomy/entity metadata and aggregate intelligence signals.
- Prefer stable canonical publisher URLs.
- Preserve first-seen `collected_at` across subsequent collection runs.
- Deduplicate on deterministic article ID derived primarily from canonical URL.
- Cap the rolling repository dataset at 5,000 articles.
