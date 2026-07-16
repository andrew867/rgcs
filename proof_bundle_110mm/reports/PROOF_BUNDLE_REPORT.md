# Proof Bundle Report — Canonical 110 mm Crystal

**VERDICT: CONVENTIONAL_NODE_FOUND** (engine status: CONVENTIONAL_NODE_EXPLAINS_RESULT; the verdict was
not forced — a null or conventional outcome passes).

Configurations: ideal N=7 (110.03766741071429 mm =
770.263671875/7, arithmetic) and nominal (110.0 mm). Frozen alpha-
quartz constants (Bechmann 1958) throughout; CPU float64 is the
numerical authority (DV4-004).

## Key numbers (this run)

- ideal first elastic modes (medium mesh):
  [13779.3, 13779.7, 26044.8, 31882.4] Hz
- nominal first elastic modes:
  [13784.0, 13784.8, 26059.0, 31894.6] Hz
- orthonormality error: ideal 1.55e-15,
  nominal 2.00e-15
- mass patch rel err: 8.84e-16
- cavity max rel err vs exact: 2.39e-04
- Christoffel Z-axis vs frozen v3: 0.00e+00
- scrambled-field null control: NO_STABLE_CANDIDATE

## Eye

CONVENTIONAL_NODE_EXPLAINS_RESULT: see eye/consensus.json and
docs/plans-v4/EYE_DIAGNOSTIC_REPORT_110MM.md. eye_coordinate is null.

## Provenance

See PROVENANCE.json. Acceleration results are copied from
evidence/v4/agent07 (hardware-dependent); the tuning-fork V.9 CSV is
copied from evidence/v4/agent10; everything else regenerated live.
