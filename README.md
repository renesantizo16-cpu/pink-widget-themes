# Pink Widget Themes

Remote content foundation for Pink Widget Studio v5. Static JSON and PNG files;
no backend, client dependencies, credentials, telemetry, or deployment workflow.

- [`widget-themes.json`](widget-themes.json): unchanged schema-1 feed with all 13 original themes.
- [`content/v1/manifest.json`](content/v1/manifest.json): v5 entry point; selects an immutable release by path, SHA-256 and byte length.
- [`schemas/`](schemas): JSON Schema 2020-12 contracts for legacy, manifest and catalog.
- [`docs/CONTENT.md`](docs/CONTENT.md): types, seven families / 21 palettes, and banner rules.
- [`docs/MAC-INTEGRATION.md`](docs/MAC-INTEGRATION.md): work required in the Mac app, caching and resource budgets.
- [`docs/PUBLISHING.md`](docs/PUBLISHING.md): authoring, validation, review, release and rollback.

The checked-in releases **1.0.0** and **1.0.1** are examples, not a deployment.
Each includes all 13 original theme packs, five individual sample items, one
composite pack, static sample artwork, a scheduled banner, and a default banner.
1.0.1 changes only the fallback message. The three palettes for each family are
available as catalog metadata; examples do not claim to provide finished artwork
or complete individual collections for every palette.

## Validate locally

Publisher tooling uses Python 3.11+ (install separately on Monterey if needed).
The Mac app consumes JSON and PNG natively and does not need Python.

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.txt
python scripts/validate_content.py
python -m unittest discover -s tests -v
```

Validation runs offline after installing the development dependency. CI validates
branches and pull requests with read-only permissions; it never publishes content.
Merging or deploying requires owner approval.
