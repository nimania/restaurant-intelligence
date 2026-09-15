# News record schema — v0.1

Each article in `data/news.json` is normalized to the following logical schema.

| Field | Type | Description |
|---|---|---|
| `id` | string | Deterministic 20-character SHA-256 prefix |
| `title` | string | Publisher/feed title |
| `url` | string | Canonicalized publisher URL with common tracking parameters removed |
| `source` | object | Source id, name, homepage and source class |
| `author` | string/null | Feed-provided author when available |
| `published_at` | ISO-8601 string | UTC publication/update time |
| `collected_at` | ISO-8601 string | UTC first-seen time |
| `language` | string | Source language |
| `region` | string/null | Geographic focus of source |
| `summary` | string | Short feed-provided description, capped at 1,200 chars |
| `categories` | string[] | Rule-based industry categories |
| `topics` | string[] | High-signal topic tags |
| `brands` | string[] | Reserved for entity extraction in v0.2 |
| `relevance_score` | number/null | Reserved for ranking in v0.2 |
| `summary_fa` | string/null | Reserved for Persian AI summary in v0.2 |

## Dataset envelope

```json
{
  "schema_version": "0.1",
  "generated_at": "2026-09-15T00:00:00Z",
  "count": 0,
  "active_sources": 0,
  "entries_processed_this_run": 0,
  "source_status": [],
  "items": []
}
```

## Design rules

- Do not store full publisher article bodies.
- Prefer stable canonical publisher URLs.
- Preserve first-seen `collected_at` across subsequent collection runs.
- Deduplicate on deterministic article ID derived primarily from canonical URL.
- Cap the rolling repository dataset at 5,000 articles in v0.1.
