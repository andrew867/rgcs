# Screenshot and Layout Audit (Agent 13 Role B)

Claim audited (G24): every public image is generated from actual
solver output — no mock screenshots.

| item | method | result |
|---|---|---|
| Bundle figures | 17+ PNGs in proof_bundle_110mm/figures: PNG magic bytes, non-trivial size, regenerated on every build by the same script that runs the solves | PASS (audit check) |
| Vector twins | every bundle figure also emitted as PDF (spec: vector where practical) | present |
| Data lineage | each figure's data is produced in the SAME build_bundle call: mode scatter plots index sol_i arrays; eye overlays plot res.candidates; coil plot uses the Biot-Savart phasor; reference bar chart uses the just-computed errors | verified by construction (no image is loaded from outside the build, except none) |
| Evidence figures | agent04/05/07/08/09/10 PNGs in evidence/v4 are produced by committed/preserved scripts from real runs (e.g. GPU parity plot from the live benchmark CSVs) | provenance in each agent's report |
| Demo screenshots | tools/demo_v4.py renders offscreen from the in-memory diagnostic fields; hashes recorded in demo_run_record.json | PASS |
| Offscreen rendering test | tests/v4/test_rscs2_cli.py::test_offscreen_screenshot_render builds a figure from a REAL solve and validates the PNG | green |
| Layout | figures carry axis labels/units and titles naming the data source (mode index, frequency, tolerance lines); parity plot shows the REGISTERED tolerance lines | spot-checked |

No mock or fabricated imagery found; no defects.
