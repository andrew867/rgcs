# R10.9 Global Distortion Report — Earth V1 vs V2

Both operators are `CALIBRATED_CANDIDATE_NOT_VALIDATED`. No claim of
independent or physical validation is made anywhere in this report.

## Operators

| | V1 (`EARTH_ALIGNMENT_V1_LEGACY_CALIBRATED`) | V2 (`EARTH_ALIGNMENT_V2_MONTREAL_DIRECT`) |
|---|---|---|
| Anchors | Wilkes, SAA, Stonehenge, Erie, Montréal via superseded transcription `168729543`, Toronto via affine-bridged `1672875493` | Wilkes, SAA, Stonehenge, Erie (V1 recorded sources), Toronto `168930443`, **Montréal DIRECT `165879243`** |
| Family | composed Gaussian RBF on S2, sigma 0.09 + 0.02 | same family, same sigmas |
| Steps | 627 (archived) | 868 (fit here, stop-on-stall) |
| Max anchor residual | 0.0° (archived) | 8.5e-7° |
| **Orientation reversals (level-6 mesh, 81,920 triangles)** | **0** (archived claim REPRODUCED: 0) | **361** |
| Area proxy ratio (min / max) | 0.038 / 5.86 (archived) | 5.8e-5 / 47.3 (level-5) |
| RMS log area proxy | 0.223 | 0.429 |
| Inverse error (200 samples) | mean 2.4e-5°, max 2.6e-3° (archived) | p50 0.0°, mean 1.96°, **max 180.0°** — non-invertible inside folded patches |

## Global displacement V1 -> V2

Level-4 grid (2,562 points): mean 0.257°, p50 0.03°, p90 0.66°,
max ≈ 46° (localized around the face-12 Montréal separation zone).
Away from that zone the two operators are nearly identical.

## Orange-slice plane re-evaluation (V2)

The orange triplet (face 12, exact convention) under V2 sits at
~(48.6, −2.4..−2.7) — dragged ~1.25° south of its V1 positions by the
Montréal separation flow. Body-centred-plane residuals remain small
(~1.2e-5 chord units) — the triplet stays nearly planar but the V1
exact plane constraint is DEGRADED under V2 and is reported as such,
not silently re-imposed.

## Honest interpretation (bounded)

Mapping two cells ~0.3° apart on the pre-warp sphere to targets
~5,000 km apart cannot be done smoothly at the V1 warp scales: V2
achieves the anchor mapping only by folding (361 reversals) and local
area distortion up to ~5 orders of magnitude. Within this warp family
the corrected direct-Montréal packet and the existing V1-style smooth
alignment are **mutually exclusive**. Possible resolutions — a
different T11-informed decoding of the Montréal packet, face-dependent
nonlinear decode stages before projection, or revision of an anchor —
are all OPEN; none is assumed. V1 remains reproducible; V2 documents
the tension.
