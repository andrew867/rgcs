# R11 Delta — Exact Timing, Dynamic Boundaries, Detectors, Mars Pilot

**Authority:** RGCS R11 delta / v6.1.0 (candidate)
**Scope:** the seven delta modules, the mandatory corrections, and the paper ingest.
**Last verified commit:** v6.0.0 baseline (branch `v600-r11-delta`)
**Prerequisites:** [R11_SPEC.md](R11_SPEC.md), [R11_FINDINGS_AND_NONCLAIMS.md](R11_FINDINGS_AND_NONCLAIMS.md)
**Related code / tests:** `r11/{exacttiming,mechboundary,photonadapter,rotor,geominverse,marspilot,detectors}.py`, `tests/v6/`
**Known limitations:** nothing is measured; no apparatus, no QFT solver, no MAG/ER grid, no spun rotor.
**Next review trigger:** acquisition of a numerical Mars field grid, a QFT solver, or any bench hardware.

---

## Mandatory corrections

**1. The "0.03 Hz below" figure is resolved.** It never belonged to
13788 Hz. Computed exactly:

```
13772.28 - 13772.25 = 0.03      exactly   <- the real 0.03-below candidate
13788.00 - 13772.28 = 15.72     exactly   <- what 13788 actually is
```

`NEAR_MODE_CANDIDATE_HZ = 13772.25` is registered; 13788 remains refuted
and **above** the computed mode. `pack_discrepancy_status =
RESOLVED_CORRECTED_CANDIDATE_REGISTERED`. Both facts are carried. This is
registered as **arithmetic only** — a 0.03 Hz step away from a computed
mode is a statement about rounding, not a physical carrier.

**2. `NO_DECODER_IDENTIFIED` preserved.** No held-out validation changed
it.

**3. The historical-name exposure remains a `DECLARED_RESIDUAL_EXPOSURE`.**
No history was rewritten.

## Paper ingest — and a provenance catch

The request named **arXiv:2510.21636v2**, *"A truncated photon"* (Rukan,
Gulla & Skaar, University of Oslo), with a SHA-256. The file actually
**attached** was a *different* paper: **arXiv:2306.05929v2**, *"Efficient
operator method for modelling mode mixing in misaligned optical
cavities"* (Hughes et al.).

Both were located and hashed:

| Paper | Digest | Status |
|---|---|---|
| 2510.21636v2 (named) | `b9e54ac8…` | **VERIFIED MATCH** — equations registered |
| 2306.05929v2 (attached) | `e6cf5323…` | registered separately as conventional cavity optics |

Recorded as `ATTACHMENT_DISCREPANCY / RESOLVED_BOTH_REGISTERED`. The
truncated-photon paper moved from `BLOCKED_MISSING_DATA` to
`ESTABLISHED_SOURCE` — it was read and hash-verified. That means its
equations are **registered, not re-derived**.

## Exact timing — `EXACT_TIMING_REGISTERED`

```
552.001953125 ms = 2261/4096 s   exactly
                 = 2261 cycles at 4096 Hz, residue 0
```
4096 Hz is the only registered carrier that closes; 925 Hz gives
`2091425/4096` cycles and 20.48 Hz gives exactly `2261/200`.

**The registered −1/125 cycle residue is provably unrealisable.** Since
`gcd(2261, 4096) = 1`, the map `f ↦ f·2261/4096 mod 1` runs over exactly
the multiples of `1/4096`, so an integer-hertz carrier realises residue
`r` **iff `4096·r` is an integer**. For `r = −1/125`, `4096/125 = 32.768`
— not an integer. Confirmed by exhaustive search over all 4096 lattice
sites. The residue is **retained as a supplied datum, not fitted**: the
macrocycle was not rescaled and the residue was not rounded to the
nearest 1/4096.

## Classical dynamic boundary — `CLASSICAL_DYNAMIC_BOUNDARY_MODEL_IMPLEMENTED`

Sudden vs gradual changes in stiffness, damping, support impedance and
electrode loading on a mass-spring-damper chain, with before/after modal
projection and a closing energy ledger.

Mode-0 energy participation (stiffness factor 1 → 4):

| parameter | SUDDEN | τ=1 | τ=5 | τ=80 |
|---|---|---|---|---|
| stiffness | 0.626 | 0.657 | 0.890 | 1.000 |
| support impedance | 0.632 | 0.657 | 0.872 | 1.000 |
| electrode loading | 0.483 | 0.544 | 0.927 | 0.999 |

A sudden change scatters **37–52%** of the mode's energy into other
modes; a long ramp recovers the adiabatic limit.

**Damping is an honest null.** `C` does not enter `K v = ω² M v`, so the
modal basis never moves and its mixing matrix is exactly the identity —
verdict `BASIS_UNMOVED_NO_MODAL_SCATTERING`, reported rather than dressed
up as a trend. Electrode softening does **negative** boundary work and
the ledger still closes; omitting the boundary-work term leaves a
residual exactly equal to that work.

## Photon adapter — `QUANTUM_TRUNCATION_NOT_BENCH_VALIDATED`

Registered source equations (ESTABLISHED_SOURCE, each carrying the
verified digest): Eq. 21 fidelity definition, Eq. 22 expected photon
number, **Eq. 28** `F_ξ = |∫dx θ(−x) ξ̄*(x) ξ(x)|` (the fidelity is the
fraction of the photon at `x < 0`), **Eq. 29** `⟨n⟩ ≤ κ₀/(4T) + κ₀²/(16T²)`,
Eq. 30 `|T(ω)|² = 1/(1+(ωκ₀)²/4)`, Eq. 31 `1/ω₀ ≪ κ₀ ≲ T`.

The paper's optical example **reproduces**: solving Eq. 30 for
`|T(ω₀)|² = 10⁻⁴` at `ω₀ = 2π×10¹⁵` gives `κ₀ = 3.183×10⁻¹⁴ s`, and
Eq. 29 at `T = 10⁻¹⁴ s` gives `⟨n⟩ ≤ 1.43` — order unity, as stated.

**One honest wrinkle, reported not smoothed:** at that same example point
Eq. 31's upper inequality `κ₀ ≲ T` is *not* cleanly satisfied
(`κ₀/T = 3.18`), so `validity_condition()` returns
`upper_inequality_marginal: True`.

Only a **classical reduced-order analogue** is implemented. There is no
QFT solver in this repository, so no quantum result is reproduced or
bench-validated.

## Hybrid rotor — `HYBRID_ROTOR_MODEL_IMPLEMENTED`

`192 × 1280 / 60 = 4096` tooth passages per second, **exactly**.
Quadrature needs **two signed channels** — a single channel cannot give
direction, and a rectified/intensity-only pair is refused. Conductive
tabs (eddy-current) and ferromagnetic inserts (variable-reluctance) are
separate transduction paths and neither implies the other.
`refuse_spin_authorization()` raises **unconditionally**, even when every
balance and containment margin is satisfied: nothing here is built.

## Geometry inverse — `CENTROID_INVERSE_UNDERDETERMINED`

`atan(√φ)` computed to 60 digits = **51.8272923729877525…°**. The
supplied **51.843°** is *not* that angle:

```
51.843 - 51.827292372987752 = 0.015707627…°  = 56.55 arcsec
```

They agree to **one** decimal place. Verdict `APPROXIMATE_NOT_EXACT`; the
gap is not rounded away.

The constrained inverse (centroid `(0,0,100 mm)` + one frequency) yields a
**solution family**, not an answer: 6+ distinct parameter sets spanning
height 205–348 mm and taper 0.07–0.87 all satisfy both constraints to
1e-9. The Jacobian is **2×5, rank 2, deficiency 3** — `NON_IDENTIFIABLE`,
with one structurally zero column. The power control recovers a body
meeting the constraints that is demonstrably **not** the planted one.

## Mars pilot — `MARS_FRAME_PILOT_COMPLETE_MAGNETIC_ROOT_NOT_IDENTIFIED`

The **frame completes**: IAU Mars ellipsoid (3396.19 / 3376.20 km), the
same South-Up proper rotation and the **same frozen icosahedron reused by
identity** from the Earth pipeline, set-valued faces on edges and
vertices, and seven real landing sites (Viking 1/2, Pathfinder,
Opportunity, Curiosity, InSight, Perseverance) as **controls** — never
targets.

The **root does not**. Mars is `CRUSTAL_REMANENT_FIELD`, with no global
dynamo. A magnetic root requires all five of {numerical MAG/ER vector
grid, altitude, epoch, gradient scalar, sign rule} frozen first; even
with all five frozen the result is `ROOT_CANDIDATE_REQUIRES_REAL_GRID`,
because the grid is `BLOCKED_MISSING_DATA`.

## Detector matrix — `CCD_PHONON_DETECTION_REFUSED`

Sensitivity domains for piezoelectric, capacitive, Hall, optical and CCD,
each with an explicit `couples_to` **and** `cannot_detect`, together
covering every observable so no pairing goes unclassified.

A CCD integrates optical intensity over an exposure at ~Hz–kHz frame
rates and has no mechanical coupling: it cannot resolve a 4096 Hz
waveform per cycle and cannot detect phonons.
`refuse_ccd_phonon_claim()` always raises.

**And the refusal does not lean on an overclaim elsewhere:** *no*
detector in the matrix couples to `PHONON` — not even the piezo, which
transduces strain/acoustic amplitude (a many-mode continuum), not an
individual quantum of lattice vibration.

---

## What the delta does not claim

No ship, no external transmission, no new particle, no decoded location,
no unique epoch, no planetary terraforming system, no physical crystal
effect. No apparatus was built, no rotor spun, no field measured, no
quantum state prepared. The truncated-photon equations are registered
from a hash-verified source, not re-derived or validated here.

`PHYSICAL_VALIDATION_NOT_CLAIMED`
