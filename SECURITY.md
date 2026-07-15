# Security Policy

## Supported versions

| Version | Supported |
|---|---|
| v3.0.0-rc1 (and later 3.x) | yes |
| v2.0.0 (frozen baseline) | archival only — no fixes will be applied (immutability guarantee) |

## Reporting a vulnerability

Email **me@andrewgreen.ca** with a description, reproduction steps, and
impact assessment. Please do not open a public issue for an unpatched
vulnerability. You can expect an acknowledgement within a week.

## Scope notes

- This is research software: it processes local files (workspaces,
  experiment manifests, crystal databases) and does no network I/O in the
  core libraries. The most security-relevant surfaces are the JSON/YAML
  loaders — all use safe loaders (`yaml.safe_load`, `json.loads`) and
  fail loudly on malformed input (fuzz-tested; see
  `docs/QA_REPORT_V3.md`).
- Reproducibility bundles embed SHA-256 checksums; verification failures
  are errors, never warnings.
- **Physical safety is handled separately and is binding:** the D7-003
  envelope (voltage/current/pulse-energy/laser-class limits,
  dummy-load-first, no human exposure) is enforced in schemas and code.
  A change that weakens it is treated as a vulnerability.
