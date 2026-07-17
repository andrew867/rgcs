# RGCS v4.3.0 — release notes

**Post-v4.2 Emergent Resonator and Structured-Wave Expansion.**

All prior tags (v2.0.0 … v4.2.1) are untouched. This release adds the
closed-loop resonator platform, five new-paper reference models, the
Eye census correction, and the supporting policy lanes — with the
coverage contract verified mechanically from day one.

## Read this first

**Nothing in this release is a physical result.** The resonator
platform is a complete software system whose every artifact is
synthetic and flagged so — no board fabricated, no fixture machined,
no laser exists, no instrument connected, no measurement taken. The
reference models are mathematics from five named 2026 papers, kept in
their systems by firewalls that raise.

## Highlights

**Closed-loop resonator platform** (`resonator_platform/`): the full
design → simulate → fixture → measure → identify → trim → verify →
certify loop as guarded software. One synthetic campaign run goes from
a predicted 1030.15 Hz disk to an ACCEPTED 1035.04 Hz certificate in
two trim iterations, with an intact 32-event hash-chained ledger.
Irreversible actions need an approval token AND a registered machine
capability — and no machine is registered, so the physical path
refuses, which is the truth about the lab.

**The Eye, corrected by its own replication agent.** The unbiased
full-domain census (Y03) showed that the v4.1 (z = 102.24 mm) and
v4.2.1 (z = 99.78 mm) coordinates are **two resolution-dependent
estimates of one male-apex feature** — and that the feature has a
symmetric family (a female-apex twin at z ≈ 4 mm and a mid-shaft pair
at z ≈ 58 mm) that no previous nearest-to-candidate analysis could
see. The station comparison stands (5.1–6.7 mm vs ~1.8 mm halfwidth).
Claim card v3 → **v4**, correction trail appended
([EYE_CLAIM_CARD.md](EYE_CLAIM_CARD.md)). Eigenspace tracked across
meshes at < 2.7°: no mode switch. Computational, idealized model;
the physical Eye hypothesis remains open and untested.

**Five papers, five reference models, one firewall discipline**:
spin-electric exchange (tunability-vs-linewidth), triangular
many-body transport (total-change vs redistribution vs
transfer-function — now in the discrimination tree), honeycomb VHS
(spacing tunes bandwidth; symmetric limit exact), geometric
filtration (workflow demo; no benefit claimed yet), neutron OAM
mathematics (parity selection verified > 95%). Sources hashed,
claim cards separate measurement from speculation, the in-press
manuscript carries a drift guard.

**Coverage: 280 fixed IDs + 8 orphans = 288**, all mechanically
verified (symbols import, tests exist, docs exist, status legal for
depth, blockers named). The orphan sweep ran DURING the programme and
registered its own discoveries, including the census findings.

**Policy lanes**: broadcast heritage (discipline transfers, claims do
not), product tiers (targeted ≠ measured; decorative says
decorative), open-commons/assurance boundary for Hydrogenuine,
private-lore ledger (mechanism public, content never), the
intuition-to-hypothesis pipeline with its retrospective baseline
honestly labelled non-evidence, and the versioned claim-card system.

## Development-time defects (fixed, with regressions)

A sign error in the triangular-transport removal rate (caught by the
redistribution test), angular-Nyquist aliasing in partial arrays,
a flat-data NaN in the Lorentzian fit, and — most importantly — the
census correcting the v4.2.1 Eye framing. Details:
[V4X2_QA_VERDICT.md](V4X2_QA_VERDICT.md).

## Blockers (explicit, all human-only)

| Blocker | Affects |
|---|---|
| Fabrication (board house, printer, machining) | R02/R03/R08 physical stages |
| Laser/CNC + enclosure + extraction (S01 hard refusal without) | R05 physical trims |
| Instruments (DAQ, vibrometer, impedance) | R04 physical measurement |
| Foundry/cleanroom | R09 (INTERFACE_ONLY) |
| Compute ≳48 GB or LOBPCG/AMG | Eye below 1.5 mm spacing |
| Ethics | all prior human-facing campaigns, unchanged |

## Verify

```bash
python -m pytest -q --deselect tests/regression/test_generator_determinism.py::test_generator_deterministic
# expect: 857 passed
python tools/v4x2_coverage.py          # 280 IDs, all gates
python tools/v4x2_orphan_sweep.py      # 8 orphans, 0 undisposed
python tools/v4x2_baseline.py --check  # frozen history
python tools/qa_audit_v4.py --fast     # 19/19
```
