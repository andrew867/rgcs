# RGCS R10.7 — Rooted Routing, Solar/Slate Roots, Phase-Conjugate Return, Field Reconstruction: Findings

**Status:** `SOFTWARE_VERIFIED` · `PHYSICAL_VALIDATION_NOT_CLAIMED`
**Baseline:** v5.6.0 (`95cd750`)
**Evidence class:** `DERIVED_MATHEMATICS` and typed source/observation records.
**Hardware:** deferred. **No apparatus built, no signal sent, no return refocused on a bench, no observation identified.**

---

## Gate Zero

Repository truth at v5.6.0 / `95cd750`, tree clean, clean-clone count
3014, both package lists equal. Private corpus and delta: **no remote,
outside the public worktree, firewall zero findings.** The five preserved
private files (CW vector registry, Vortex Opening Key, The L's delta,
base-10 delta, frozen mathematics) re-hash **byte-for-byte identical** to
their R10.6 SHA-256 receipts.

## Source authority (private, carried forward)

`SRC_JH` (Jen Han) and `SRC_LS` (The L's) remain **distinct Tier-A
private sources**, each with the single public alias
`OMEGA_REGION_SOURCE`. The record classes stay distinct (two IDs, one
alias). Tier A means faithful attribution, chronology, wording, and
uncertainty — **not** scientific verification. The names, the twelve-word
Vortex Opening Key, and the five twelve-digit CW vectors stay private;
the public tree sees only the region-level alias and the anonymized
mathematics.

---

## The corrected numerical record is append-only (P01)

**Module:** [`r10/received.py`](../../r10/received.py)

The source correction `8300 → 8.300` and `1876 → 1.876` is recorded as a
**transcription correction, appended, never overwriting** the raw values.
The correction is deliberately **scale-invariant**:

```
8.300 / 1.876 = 8300 / 1876 = 2075 / 469   (exactly)
```

so the ratio, and therefore the residual against the phase-frame value,
is **unchanged** by the correction:

```
4096/925 − 2075/469 = 1649/433825 ≈ 0.086%   (exact, not rounded)
```

The verdict stays `APPROXIMATE_NOT_EXACT`. `refuse_unit_invention()` and
`refuse_overwrite()` hold the line: no unit is inferred for either
quantity, every scale model offered is invertible, and the physical
mapping status remains `PhysicalMappingUnresolved`. Correcting a
transcription does not license inventing a physics.

---

## Roots-first frames, and why one direction is not a frame (P06)

**Module:** [`r10/rootframe.py`](../../r10/rootframe.py)

A body frame is built **roots-first**: a `RootFrame` carries a primary
and a secondary direction, and `orientation_from_two_directions()`
Gram-Schmidt–orthonormalizes them into a proper rotation
(`R Rᵀ = I`, `det R = +1`; `LEFT` handedness flips the determinant to
−1). The matrix ↔ quaternion conversion round-trips to 1e-9.

**The load-bearing refusal:** a single direction underdetermines the
frame. `RootUnderdetermined` is raised for a single-direction root, for
two parallel directions, and for a missing secondary. A latitude and a
longitude are *calibration on a known frame*, not a frame — and the
module says so by name. Verdict `ROOT_UNDERDETERMINED` until a second,
non-parallel direction exists.

## Rooted interbody routing respects the light-time floor (P07)

**Module:** [`r10/route.py`](../../r10/route.py)

The route compiler assembles hops between **rooted cells** (e.g.
`EARTH_CELL → EARTH_ROOT → EARTH_MOON_ROOT → MOON_ROOT → MOON_CELL`),
checks connectivity and epoch compatibility, and only permits edges in a
declared supported set. A rooted Earth–Moon route compiles
(`ROUTE_SOFTWARE_VALID`) and carries a **light-time floor of ≈ 1.28 s**.

The causality firewall is not decorative: a hop that claims zero transit
time across a nonzero distance raises `CausalityViolation`; local
(zero-distance) hops are `INSTANTANEOUS_LOCAL`, spatial hops are
`CAUSAL_DELAY_REQUIRED`. **No route beats the light-time floor**, and the
report disclaims any "gateway." The software is valid; the physical edges
are unsupported.

## The solar root is a candidate, and the real catalog is blocked (P04)

**Module:** [`r10/solarroot.py`](../../r10/solarroot.py)

A dynamic solar root is estimated as the **weighted centroid of emission
directions** on the sphere; the roll about it needs an independent axis
and is refused when that axis is parallel (`ROOT_UNDERDETERMINED`
otherwise). The engine has **demonstrated power**: a planted centroid is
recovered to a median error under 10° (≈1.2° in the reference run). The
control is honest too — with equal weights, weight-shuffling changes
nothing (`WEIGHTING_NOT_INFORMATIVE`, p > 0.5).

**The real solar catalog is declared `BLOCKED_NO_DATA_SOURCE`, not
faked.** No centroid over real emission data is reported, because no such
data feed is available here. Verdict `ROOT_CANDIDATE_ONLY`.

## Sky observations are unidentified by default (P03)

**Module:** [`r10/skytrack.py`](../../r10/skytrack.py)

The anonymized public engine ranks the *ordinary* candidates a kinematic
description is consistent with — speed sets which candidates are in play,
steadiness/silence break ties — and **never converts a ranking into an
identification.** A ~40°/9 s steady, silent, constant-speed transit makes
`SATELLITE_CANDIDATE` the leading ordinary hypothesis; blinking shifts
toward aircraft, near-zero speed toward astronomical, a fast brief streak
toward meteor. But the terminal verdict is `UNIDENTIFIED_OBSERVATION` (or
`INSUFFICIENT_GEOMETRY` with no angular span), and
`refuse_identity_without_catalog()` refuses any identity — ordinary or
exotic — without a reconstructed geometry and a catalog match. The engine
holds **no specific observation**; the one field record lives privately.

## Phase-conjugate return works, and it is conventional DSP (P09)

**Module:** [`r10/phaseconj.py`](../../r10/phaseconj.py)

A "returned" signal that undoes the distortion it picked up is not
exotic: it is **phase conjugation / time reversal**, the operating
principle of phase-conjugate and time-reversal mirrors, a century-old
piece of linear-systems engineering. In a **reciprocal** channel the
round trip multiplies the spectrum by `H·conj(H) = |H|²`, which is real,
so the phase distortion cancels and a smeared pulse comes back compact.
The simulation refocuses **exactly** (crest factor recovered to the
original) and sits far above an energy-matched random-return null
(z ≫ 10).

Four firewalls are quantitative, not rhetorical:

- **Conjugation is a specific operation.** The refocusing mirror is
  *spectral* conjugation (= conjugate **and** time-reverse). A pointwise
  conjugate, a bare time reversal, and a sign flip each **fail** to
  refocus. Conjugation is a distinct, load-bearing step.
- **Reciprocity is the control.** Swap the return channel for a
  nonreciprocal one and the same operation buys nothing —
  `RECIPROCITY_REQUIRED`.
- **Causality holds.** Fold the propagation delay into the conjugated
  phase and the algebra cancels it, putting the peak at *t = 0* — a
  superluminal return. `refuse_superluminal_return()` rejects it and
  `causal_round_trip()` books the full round-trip delay as a real shift
  conjugation cannot touch — `CAUSAL_DELAY_REQUIRED`.
- **Roles stay separate.** Carrier (4096 Hz), key (925 Hz), local
  oscillator, and message clock are four typed roles;
  `refuse_role_collapse()` refuses to merge any two without an experiment
  that discriminates them. Sharing a frequency is a coincidence of
  numbers, not an identity of roles.

Nothing is measured; no apparatus exists.

---

## Private records (never public)

Two records were written to the **private repository only** (0 remotes,
outside the public worktree, OneDrive-synchronized):

- **San Antonio provenance trail** — the particulars are recorded
  verbatim (the date window, the locale, the address *as given* with no
  "Blvd" invented, and the named person *as given*). **Every item after
  the source message is a lead, not a fact.** No independent verification
  was performed, and none was fabricated — this environment has no
  authorized archive access. Prior exposure is left `UNKNOWN`, chronology
  tension is preserved rather than smoothed, and **no claim is made about
  any real person.** Overall verdict `ASSOCIATIVE_TRAIL / UNRESOLVED`.
- **Field-observation record** — the raw narrative (≈2 am, a steady bright
  light, 8–10 s, silent) is immutable. With no estimable angular span the
  engine returns `INSUFFICIENT_GEOMETRY`; the classification is withheld,
  neither ordinary nor exotic asserted or excluded. Status
  `UNIDENTIFIED_OBSERVATION`.

---

## What R10.7 does not claim

- No apparatus was built, no signal sent, no channel measured, no return
  refocused on a bench, no crystal driven.
- **No root, frame, or route was physically realized**; the frames are
  underdetermined without a second direction, the solar catalog is
  blocked, and no interbody edge is physically supported.
- **No decoder was found** and none was attempted anew; the base-10 clue
  remains `NO_DECODER_IDENTIFIED` from R10.6.
- **No observation was identified** — not called a craft, not called
  nothing.
- The corrected numbers change no physics: the ratio is scale-invariant,
  the residual is unchanged, the mapping stays unresolved, and no unit is
  invented.
- No named person and no source text enters the public tree; the Tier-A
  names, the Vortex key, and the five CW vectors stay private.

## Not executed (deferred / blocked)

- **P05 slate photogrammetry — real-image ingestion:** the 15° = 360°/24
  division is exact arithmetic, but no real slate image was ingested;
  the 24-fold division is *tested as arithmetic, not assumed as fact*.
- **P08 density-layer routing:** not implemented this tranche.
- **P11 apparatus / field solver, spectral-pure / mechanical source:** no
  apparatus, no field solve, no mechanical generation.
- **P12 prospective / blinded harness:** the harness design stands; no
  blinded run was executed (no future vector, slate angle, or emission
  interval exists yet to reveal against).
- **P13 private narrative archive:** deferred.
- **Real solar catalog (P04):** `BLOCKED_NO_DATA_SOURCE`.

Hardware and future-data phases remain deferred. Where a phase could be
completed as software with an honest blocked receipt, it was; where it
required hardware or data that does not exist here, it was not, and this
document does not imply otherwise.
