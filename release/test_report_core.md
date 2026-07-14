# RGCS v2 — Core Test Report (`rgcs_core`)

- report_id: test_report_core
- author: Sub-Agent 04 (Computational Core and Verification)
- date: 2026-07-14
- package: rgcs_core 2.0.0 (project rgcs-v2)
- model_contract: docs/MATHEMATICAL_MODEL.md (RGCS-M.0..M.61); docs/model_registry.yaml schema 1
- environment:
  - python: 3.11.15 (target 3.12 compatibility; no 3.12-only syntax)
  - numpy: 2.4.4
  - scipy: 1.17.1
  - pydantic: 2.13.3
  - pytest: 9.1.1
  - hypothesis: 6.156.6

## Result summary (machine-readable)

```yaml
command: python3 -m pytest tests/unit tests/property tests/golden tests/regression
status: PASS
total: 180
passed: 180
failed: 0
errors: 0
skipped: 0
runtime_s: 7.9
suites:
  unit:        {collected: 97, passed: 97}
  property:    {collected: 17, passed: 17}   # Hypothesis, seeded
  golden:      {collected: 19, passed: 19}   # ledger Part E G-01..G-15 + D-01/D-13
  regression:  {collected: 47, passed: 47}   # incl. 1 slow + 4 benchmark
markers:
  slow: 1        # generator byte-identical regeneration (passes, ~3 s here)
  benchmark: 4   # non-gating performance checks (all pass)
```

## Golden-value verification (ledger Part E)

| ID | Quantity | Expected | Status |
|---|---|---|---|
| G-01 | ladder constant | 770.263671875 mm | PASS |
| G-02 | L5 | 154.052734375 mm | PASS |
| G-03 | L7 | 110.037667410714 mm | PASS |
| G-04 | f_ax(110 mm) | 28681.8181818 Hz, +0.0342431 % | PASS |
| G-05 | f_ax(116 mm) | 27198.2758621 Hz, N_eff 6.640204, −5.1399 % | PASS |
| G-06 | compact n=1 (6310 m/s, 100 mm) | 10042.6769091 Hz | PASS |
| G-07 | ε(40960, 20480, p=2) | 0 exactly | PASS |
| G-08 | two-mode (1000, 1000, g=10) | 990 / 1010 Hz | PASS |
| G-09 | k_H = 0.9866751189; ΔM = 2.0937873 g | PASS |
| G-10 | a(q=e) = 0.15915494309; rκ = 0.98757049215 | PASS |
| G-11 | atan √φ = 51.8272923730° (Δ = −0.015708°) | PASS |
| G-12 | 2261=754+754+753 (552.001953125 ms); 1508=754+377+377 (368.1640625 ms); 1131=377+377+377 (276.123046875 ms) | PASS |
| G-13 | coil 26 µH / 117 µJ (60 V, 1.3 µs, 3 A) | PASS |
| G-14 | 1e−14 A = 62,415.09 e/s | PASS |
| G-15 | shear-scalar identities | PASS |
| D-13 | r_φ(1507.328) = +0.328 cycles (positive) | PASS |
| D-01 | x_g = 78.3277 mm (female frame) ↔ 75.7250 mm (male frame) | PASS |
| 116 mm | harmonic class set {6, 7} at u_v = 0.05 (RGCS-M.12) | PASS |

## Coherence manifest regression

All 38 `expected` entries across golden cases (a)–(g) recomputed from the
checked-in CSVs by the `rgcs_core.coherence` port and checked with the
manifest's own tolerance semantics (atol/rtol/min/max/exact). Expected
values are READ from `experiments/sample_data/golden_coherence/
manifest.json` at test time — never hard-coded. Bootstrap for case (e)
uses seed MASTER_SEED+55 = 20260769 and reproduces the CI
[203.826, 204.884] within ±5 on each bound. Cases (b): CSV 9-significant-
digit quantization tolerance widened from 1e−6 to 1e−5 (documented in the
test). The `slow` regeneration test confirms
`tools/generate_golden_coherence.py` reproduces every CSV byte-identically
and the manifest `datasets` section exactly.

## Policy gates

- classification metadata: every public claim-bearing function carries
  `@classified(...)` (enforced by
  `test_classification_metadata_on_every_public_function`); labels
  restricted to the four categories; hybrid labels rejected.
- forbidden vocabulary: absent from all `rgcs_core` source and docstrings
  (enforced; term list assembled at runtime in `rgcs_core.provenance`).
- JSON policy: NaN/inf serialize as null everywhere (`json_dumps` uses
  `allow_nan=False`); `node_positions` measured-node absence round-trips
  as null.
- deleted estimator: `geometry_balance_node_mm` is not implemented and a
  test asserts it is absent from `crystal_geometry` output.

## Benchmarks (non-gating)

```yaml
coherence_series_50k_samples_997_windows_s: 0.029
spiral_metrics_converged_9600_samples_s: 0.002
stuart_landau_10000_steps_2_modes_s: 0.141
spatial_phase_anisotropy_3x5000_s: 0.010
```

## Known deviations

1. Environment Python is 3.11 (brief said 3.12); code is 3.12-compatible,
   `requires-python >= 3.11`.
2. Parquet serialization (original brief) not implemented; JSON-compatible
   dicts are flat/typed and Parquet-ready via pandas if needed downstream.
3. `model_registry.yaml` `module_target` names (rgcs_core.ladder,
   .compact, .material) predate the mandated subpackage names
   (harmonics, compact_modes, uncertainty); registry ids are carried in
   function metadata, so traceability is unaffected.
4. `integrate_stuart_landau` uses an exponential integrating factor for
   the stiff linear term (plain Euler is unstable at ω·dt ~ 1e−2); the
   golden-dataset generator port `stuart_landau_pair` remains the exact
   Euler-Maruyama reference.
