# Developer guide — Recursive Infrastructure Lab

## Ownership

Cursor owns `rgcs_lab/`, `static/hub/`, API wiring, browser tests, and packaging extras.
Codex owns pure domain cores (`rgcs_golay`, `rgcs_frames`, …) when those packages land.
Adapters under `rgcs_lab/adapters/` prefer installed Codex packages and otherwise use
`rgcs_lab/reference/` demos.

## Layout

```text
rgcs_lab/
  common/     status, receipts, privacy
  adapters/   domain API wrappers
  reference/  temporary deterministic demos
  api/        FastAPI app
  cli.py
static/hub/   nine-module public hub + fixtures + receipts
tools/lab/build_static_hub.py
tests/rgcs_lab/
```

## Receipts

Every adapter returns a `ModuleResult` with a receipt matching the canonical
packaged schema `rgcs_lab/common/receipt_schema.json` (module, version,
source_commit, status, claim_class, inputs, models, result, tests,
receipt_sha256); `schemas/lab/receipt.schema.json` is a byte-identical
distribution mirror for external tooling. Both builders validate through
`rgcs_lab.common.status_schema.validate_receipt` before returning.

## Privacy

`PrivacyDefaults` bind `127.0.0.1:8765`, disable telemetry, and refuse remote
binds unless `--allow-remote` is passed.

## Tests

```bash
python -m pytest tests/rgcs_lab -q
python tools/lab/build_static_hub.py
```
