# Restaurant Intelligence

Open, evidence-aware tooling for collecting, structuring, and interpreting public restaurant-market information.

This repository combines a lightweight public interface with documented methodology and governance for restaurant and food-service intelligence. The project is designed to keep **observations**, **derived metrics**, and **interpretation** distinct so that claims remain traceable and uncertainty stays visible.

## What is in this repository

- `index.html`, `app.js`, `styles.css` — public-facing interface.
- `properties.html` — property/location-oriented view.
- `marketplace.js` — browser-side, read-only connector for live Divar and Digikala MCP results.
- `data/equipment-catalog.json` — concept-specific equipment specifications, budget weights and buy/inspect policies.
- `data/` — structured project data.
- `food-intel/` — food-industry intelligence workstream.
- `METHODOLOGY.md` — evidence hierarchy, uncertainty handling, corrections, and responsible-use principles.
- `CONTRIBUTING.md` — contribution guidance.
- `GOVERNANCE.md` — project governance.
- `SECURITY.md` — security reporting and operational guidance.

## Cities

The feasibility wizard covers several cities, chosen with the searchable city picker at the top of the page (or `?city=<id>` in the URL, e.g. `?city=karaj`).

| City | Zones | Quality | Notes |
| --- | --- | --- | --- |
| Nowshahr (`nowshahr`) | 6 | Benchmark | Original benchmark, with saved property leads in `data/properties.json`. |
| Karaj (`karaj`) | 6 | Preliminary | Added September 2026. |
| Mashhad (`mashhad`) | 6 | Preliminary | Added September 2026. Three zones have no rent data yet and are excluded from results. The Haram zone is tagged as a seasonal pilgrim market. |

Preliminary benchmarks are explained in `METHODOLOGY.md`. Live Divar property leads and the equipment market work for every city.

### Cross-city comparison

After the results, a card shows the best option for the same answers in every other city, next to the user's top pick: capital needed, estimated monthly rent and daily orders needed. These are the only figures compared, because each city's demand score is relative to its own zones. If an answer rules out every option in the current city but not elsewhere, the option stays selectable and says which city it works in.

### Adding a city

1. Create `data/cities/<id>.json` (copy an existing file). Main fields:
   - `id`, `name`, `province`, `emoji`
   - `quality` (`benchmark` or `preliminary`) and `quality_label`
   - `notice` — shown under the headline, or `null`
   - `data_note`, `retrieved_at`, `divar_city`, `used_market_cities`, `properties_file` (or `null`), `sources` (`{label, url}` list)
   - `zones`: `id`, `name`, `demand` (0–100), `active`, `reviews`, `rent` and `deposit` (toman per m², or `null` if unmeasured), `confidence` (0–1), `w` (`qsr`, `cafe`, `traditional` whitespace, 0–100), `advice`, and optional `tag` (e.g. a seasonal market).
2. Add `{ "id": "<id>", "file": "<id>.json" }` to `data/cities/index.json`.
3. Document the sources and method in `METHODOLOGY.md`.

Concept economics (setup cost, average check, payroll) are shared across cities and live in `app.js`.

## Methodology principles

Restaurant Intelligence is built around a few explicit rules:

1. Prefer primary and directly observable sources where possible.
2. Record collection context for information that can change over time.
3. Document assumptions behind rankings, scores, classifications, and other derived outputs.
4. Treat missing information as unknown — not as evidence that something does not exist.
5. Preserve traceability for material corrections and methodology changes.
6. Use public-market information only; do not collect private customer data or credentials.

See [`METHODOLOGY.md`](METHODOLOGY.md) for the full methodology.

## Project status

**Active development.** The repository currently contains a working public interface and the project’s methodological/governance foundation. Coverage, automation, and analytical modules are expected to evolve over time.

The feasibility wizard now includes an experimental launch-planning layer: it ranks live commercial-property leads for the selected budget and creates a concept-specific equipment basket. Each equipment card can request current new and used marketplace leads. These results are leads for verification, not appraisals, supplier endorsements or technical inspections.

Shortlisted live properties can also be expanded into a concept-specific readiness review. The review reads public ad details, separates confirmed facts from explicit risks and unknowns, generates a visit checklist, and recalculates capital commitment using that property's advertised deposit and rent.

Because restaurant prices, menus, locations, hours, and ownership details can change, data should always be interpreted together with its collection date and source.

## Local preview

The current interface is static and can be previewed locally with any simple HTTP server, for example:

```bash
python3 -m http.server 8000
```

Then open:

```text
http://localhost:8000
```

## Contributing

Contributions that improve source quality, traceability, methodology, structured data, or the public interface are welcome. Start with [`CONTRIBUTING.md`](CONTRIBUTING.md).

For substantive analytical changes, describe the source, assumptions, and expected impact in the pull request.

## Responsible use

This project is intended for restaurant, food-service, and public-market intelligence. It should not be used to collect or expose private customer information, credentials, or sensitive personal data.

## License

No open-source license is declared in this repository at the moment. Unless and until a license is added, normal copyright rules apply. A future license should be selected deliberately based on the intended reuse model for the project.
