# RCW phase receipts — P02 through P06 (EOD structural slice)

Common: branch `rcw-public-workbench` (from
`r1084-recursive-coordinate-recovery` @ `3235f05`); START_COMMIT
`1c70b36` (P01). Python 3.13.2 repo venv. All commands below were
executed, not proposed.

## P02 — Freeze packet authority and public schemas

* Implementation: `rgcs_coordinate/codecs/federation_terra_30.py` —
  typed, pure-stdlib public adapter of the frozen F5|Q22|S3 parser;
  trace schema `rgcs.structural-trace.v1`; exact encode/decode/
  round-trip; reserved faces labelled, never folded; out-of-family
  words refused, never truncated. `export_trace`/`load_trace` verify
  every stored field against the arithmetic (tamper-evident).
* The frozen parser (`r12/icosapacket.py`) and Q22 child operator
  (`r12/icosarefine.py`) are UNTOUCHED. Parity is enforced by test:
  golden vectors + 5003-word deterministic sweep agree bit-for-bit;
  the one declared reporting difference (frozen parser REFUSES
  reserved faces; public codec labels them `reserved`) is itself
  locked by test.
* Tests: `tests/rgcs_coordinate/test_rcw_codec_parity.py`,
  `test_rcw_trace_and_static.py`.
* AUTHORITY_CHECK: no reinterpretation of decimal digits; Morton
  indices refuse coordinate readings; no rejected decoder revived.

## P03 — Authority registry and claim classes

* Implementation: `rgcs_coordinate/domain/claims.py` — machine-
  readable `ClaimClass` (EXACT_STRUCTURAL, TRAINING_EQUALITY, HOLDOUT,
  DERIVED_CANDIDATE, CONVENTIONAL_MODEL, OPERATOR_CORRECTION,
  SOURCE_CLAIM, UNDERDETERMINED, BLOCKED_MISSING_DATA), the standing
  claims block, `BA_130` as sole active long-origin epoch reference,
  and `refuse_promotion` (validation is never a relabel).
* Visibility: claims embedded in every trace (`claims` key), CLI
  badges + `version --full`, static demo badges/footer, docs
  (CONCEPTS_AND_CLAIM_BOUNDARIES.md).
* Tests: `test_rcw_claims_corpus_projection.py`.

## P04 — Source inventory and packaging parity

* Coordinate-module inventory (adapters, no duplication):
  - frozen authority: `r12/icosapacket.py`, `r12/icosarefine.py`
  - sealed calibration: `cwatlas/r1082/` (geocode freeze, rejected
    decoder registry — preserved verbatim)
  - rejected-experiment receipt: `cwatlas/r1084/` (retained)
  - active projection: `cwatlas/r1085a/` (R10.8.5A)
  - NEW public surface: `rgcs_coordinate/` (domain, codecs,
    provenance+fixtures, projection, cli)
  - shadow imports: none added; the public codec is arithmetic-
    parallel by test, not a duplicate import path of r12 internals.
* Packaging: `pyproject.toml` gains `rgcs_coordinate*` in
  packages.find, package-data on BOTH the top-level key
  (`rgcs_coordinate = ["fixtures/*.json"]`) and the dotted key —
  the R10.8.2 right-anchored-match lesson applied.
* Guard: `python -m pytest tests/v52/test_r9_packaging.py -q` →
  **4 passed**.
* Wheel audit: `rgcs-8.2.0-py3-none-any.whl` contains 11
  rgcs_coordinate files incl. `fixtures/golden_vectors.json` and the
  `rgcs-coordinate` entry point (verified by zip inspection).

## P05 — Corpus and provenance registry

* Implementation: `rgcs_coordinate/fixtures/golden_vectors.json`
  (public-safe; chronology metadata only; "private operator provenance
  excluded by policy"; holdouts: none published, kept separate) +
  `rgcs_coordinate/provenance/corpus.py` (frozen records, training
  labels, the registered orange-slice correction raw 3 -> active 7,
  `validate_corpus` checking every declared field against the
  arithmetic).
* CLI: `rgcs-coordinate corpus validate [fixture.json]` (exit 2 on
  invalid fixtures — exercised in tests and in the clean venv).
* Tests: `test_rcw_claims_corpus_projection.py`, `test_rcw_cli.py`.

## P06 — Release branch, versioning, build matrix

* Branch: `rcw-public-workbench` (bounded workstream). **No tag
  created** — premature tags refused; v8.1.0/v8.2.0 remain local-only
  and unpushed pending separate authorization.
* Versioning: monorepo distribution stays `rgcs 8.2.0`; the workbench
  package carries its own `__version__ = "0.1.0.dev0"`
  (`rgcs-coordinate` 0.1.0 is the first public target; the `.dev0`
  suffix drops only at the release decision, P35/P36 equivalent).
* Compatibility matrix (declared; executed cells marked):
  | python | platform | structural | clean install |
  |--------|----------|-----------|---------------|
  | 3.13.2 | win11    | EXECUTED (30 tests) | EXECUTED (wheel -> fresh venv -> smoke) |
  | 3.11/3.12 | win/linux | declared target, CI cell (Day 3) | pending |
* Artifacts: wheel built OUTSIDE OneDrive (scratchpad `dist/`,
  OneDrive-lock hazard honoured); clean venv created in scratchpad;
  installed console script exercised: `version --full`, `decode`,
  `corpus validate` (4 vectors, 0 failures), `roundtrip` (EXACT),
  `doctor` (backend importable).

## EOD slice evidence (Delivery Contract, Day 0)

* importable package: `import rgcs_coordinate` — used by 30 passing
  tests and the installed wheel;
* structural decoder + encoder + trace JSON: above;
* CLI: `rgcs-coordinate` with exit-code contract (0/2/3/4/5/70), no
  mocked `serve` (absent until the web slice is real);
* static single-file demo: `workbench/index.html` — opened from
  `file://` in a real browser; on-load decode of the Stonehenge
  fixture matched the Python codec field-for-field (badges:
  STRUCTURAL CODEC / PHYSICAL PROJECTION UNDERDETERMINED / STONEHENGE
  IS A TRAINING EQUALITY); no external requests (locked by test);
* docs: INSTALLATION.md, QUICKSTART.md,
  CONCEPTS_AND_CLAIM_BOUNDARIES.md under `docs/workbench/` — commands
  executed as documented;
* golden-vector tests: `tests/rgcs_coordinate/` → **30 passed**;
* honest projection status: `project` exits 4 with
  `UNDERDETERMINED` + full assumption list; profile verdict verbatim
  `RGCS_R10_8_5A_YELLOW_PACKET_AUTHORITY_HELD_PROJECTION_UNDERDETERMINED`.

KNOWN_LIMITATIONS (explicit YELLOW lanes):

* physical projection underdetermined (see R10.8.5A receipt; radial
  misfit ≥ 6.7 km best-config; roll DOF undetermined);
* FastAPI workbench, map UI, plugin devkit, CI matrix, SBOM: Day 1–3;
* broad-suite byte-determinism tier (D-V3-04) fails outside the
  archived v2 environment — drift investigation spun off;
* no second anchor requested (locked: corrected projection profile
  must be exhausted first).

VERDICT (slice): STRUCTURAL_CODEC_GREEN; STATIC_DEMO_GREEN;
PACKAGING_GREEN; PROJECTION_YELLOW_ALLOWED.
