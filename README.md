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
