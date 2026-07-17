# RGCS V4X — Master Research Expansion Programme report

Baseline: RGCS v4.1.1 (v4.1.0 scientific baseline + documentation patch).
Current release: **v4.2.1** (completeness-audited).

Coverage contract: [V4X_COVERAGE_LEDGER.md](V4X_COVERAGE_LEDGER.md) +
`V4X_COVERAGE_LEDGER_STRICT.json` — **268 items** (248 fixed ledger IDs
+ 20 orphans), gates **G42A–G42G** all PASS, enforced by
`tests/v4/test_v4x_coverage_gates.py`.

> **Audit note (v4.2.1).** An earlier version of this report led with
> "248/248 ledger IDs disposed, gate G42 PASS". That statement was true
> and hollow: the gate verified that each ID had an owner *string* and
> an artifact *string*, which any nonempty text satisfies. The
> completeness audit replaced it with gates that check that the paths
> exist, the symbols import, the tests and documents exist, and the
> status is legal for the depth actually delivered — then found that two
> workstreams were registries wearing an implementation's status and
> that the orphan sweep had never run. See
> [V4X_QA_FINAL_VERDICT.md](V4X_QA_FINAL_VERDICT.md) and
> [V4X_DEFECT_REGISTER.md](V4X_DEFECT_REGISTER.md).

This programme translates the full post-v4.1 backlog into equations,
observables, controls, uncertainty, failure conditions, and an honest
status per item. It does not claim that the preserved ideas are true.
Nothing in this release is an experimental result.

## Lanes and status

| Lane | Coverage | Outcome |
|---|---|---|
| Computational (A01–A18) | polaritons, Eye, family, keys, BVD, apparatus, interfaces | implemented; statuses below |
| Frequencies (F001–F052) | `rscs2_core/frequency_keys.py` | registry + look-elsewhere null model |
| Geometry/specimens (G001–G030) | `rscs2_core/harmonic_family.py` | prospective registry, CANDIDATE_NEW_COUPLING |
| Spiral/cymatic (S001–S024) | `spiral_cone.py`, `cymatic_disk.py` | validated mathematics + ENG prototypes |
| Apparatus/experiments (E001–E027) | `protocols_v4x.py` | PROTOCOL_READY_HARDWARE_REQUIRED |
| Water (W001–W017) | E05 campaign | PROTOCOL_READY_HARDWARE_REQUIRED |
| Human loading (H001–H017) | E06/E07 campaigns | ETHICS_APPROVAL_REQUIRED |
| Consciousness (C001–C052) | `consciousness_lane/` | quarantined; SOURCE_HYPOTHESIS / REDUCED_ORDER / ENG |
| Future interfaces (I001–I011) | `interfaces_future.py` | INTERFACE_ONLY, refuse to compute |

## Computational lane

**Polaritons (A01–A06)** — REDUCED_ORDER_VALIDATED. Hopfield 2×2 and 3×3
(magnon + B field), cavity and polariton dispersion, polarization
channels; analytic limits tested (gate G06). The quantum transduction
path is INTERFACE_ONLY. These are reference systems: an analogy in a
polaritonic material is **not** evidence that the same mechanism occurs
in alpha quartz, and no such mechanism has been imported.

**Eye refinement (A07–A10)** — **RESOLVED**:
`NEAR_CONVENTIONAL_NODE_BUT_DISTINCT`. See
[EYE_REFINEMENT_V5.md](EYE_REFINEMENT_V5.md). The v4.2.1 ladder
(3.0/2.0/1.5 mm, 30 816 dof) puts the halfwidth (1.803 mm) below the
separation (6.298 mm) by 3.5×, so the comparison finally carries
information and the conventional model **does not explain** the
candidate. The candidate does **not** converge on the v4.1 coordinate:
its distance from it grows with resolution (1.375 → 2.270 → 2.476 mm),
settling near (−0.048, −0.020, 99.78) mm. The canonical record is
preserved unchanged (G07) and is now understood as resolution-limited
rather than converged. Computational only; no measurement exists. The
v4.2.0 preliminary ladder (mis-titled "sub-millimetre" at 4.5 mm) is
retained at
[V4X_EYE_SUBMM_REFINEMENT.md](V4X_EYE_SUBMM_REFINEMENT.md).

**Harmonic family (A11, A12)** — CANDIDATE_NEW_COUPLING. L_N = 770.263671875/N
mm for N = 5…12, with tolerance sensitivity and a prospective specimen
generator. Prospective means predicted-and-unbuilt, not confirmed.

**Frequency keys (A13)** — REDUCED_ORDER_VALIDATED. All F001–F052 with a
look-elsewhere null model (gate G11). Exact misses are recorded as
misses: 21 × 195 = 4095 Hz is 1 Hz away from 4096 Hz and is reported that
way, not rounded into a match.

**BVD (A14, A15)** — REDUCED_ORDER_VALIDATED. fs/fp/Q/k_eff² extraction
with synthetic recovery and an explicit INSUFFICIENT_RESOLUTION path when
the sweep cannot identify the parameters.

**Apparatus (A16)** and **calibration/inverse design (A17)** —
REDUCED_ORDER_VALIDATED, including the ordinary-artifact budget (gate
G14) that any future measurement must beat before anything unusual is
claimed.

**Microscopic interfaces (A18, I001–I011)** — INTERFACE_ONLY. DFT/BSE/
ab-initio/QFT paths are typed contracts that raise on invocation. A
missing implementation is not evidence of physical nonexistence, and it
is not permission to emit a fabricated number (gate G15).

## Geometry lane

Spiral-cone mathematics is validated where it is mathematics: the
curvature invariant κ·r = 1/√(1+a²), stable-focus eigenvalues −a ± i, the
per-turn ratio e^(−2πa), clamped-plate Bessel roots, Mohan spiral
inductance. The pinched twisted-cone variant generates (gate G17), and
structural resonance is separated from electrical resonance (gate G19).
Merit functionals are declared ENG ranking constructs and carry no
physical significance.

## Experimental lane

Nine campaigns with channels, control matrices, randomization, blinding,
preregistration records, analysis plans, and safety-gate evaluation. No
hardware was operated.

- **PROTOCOL_READY_HARDWARE_REQUIRED**: E01 acoustic, E02 electrode
  pulse, E03 coil/field mapping, E04 material comparison, E05 water,
  E08 apparatus integration, E09 staged bench execution.
- **ETHICS_APPROVAL_REQUIRED**: E06 human loading, E07 operator state.
  These are blocked on ethics approval regardless of engineering safety,
  and the safety gate enforces that in code.

The water programme carries a no-ingestion and no-therapeutic-claims
acknowledgement as a gate condition (G26). The synthetic DAQ pipeline is
validated on planted ring-down fixtures (G29); the record schema refuses
to label synthetic data as measured (G30).

## Consciousness lane

A separate, quarantined research lane (`consciousness_lane/`). All 52
entries carry a layer (metaphor / mathematical model / established
cognitive evidence / speculative biological / speculative external field
/ first-person phenomenology / private myth / engineering analogy), a
status, an evidence tag, and a falsification condition. The package
contract forbids importing quartz solvers, and a test enforces it.

Boundaries held explicitly:

- THz and superheterodyne items are **analogies only** — the existence of
  6G instrumentation is not evidence that the brain is a receiver (G34).
- Quantum-probability models of decisions are **not** evidence of quantum
  processes in neurons (G37).
- The microtubule causal threshold (τ_c · η_φ · K_cross > θ) is defined so
  the claim is testable; at the reference 310 K decoherence estimate it
  does not clear the threshold, and the status never upgrades on a
  favourable parameter guess (G33).
- Hydrogenuine engineering items make no consciousness claim (G39).
- First-person and private-myth layers are retained verbatim, marked
  non-public, and are neither endorsed nor refuted (G38).
- "Coherence is not truth" is implemented as a control: two oscillator
  populations both reach r ≈ 1 while encoding contradictory states.

No consciousness record is usable as evidence in quartz computation.

## Limitations

- The Eye result is **computational**: an ideal geometry, the first
  elastic mode, an assumed orientation (no XRD exists), a final
  convergence shift of 0.207 mm, and a hardware ceiling at 1.5 mm
  spacing (cl=1.25 projects to ~45–71 GB against 31.6 GB of RAM). A
  resolvable cluster in a model is a property of the model.
- Every experimental campaign is a protocol. None has been executed.
  There is no measured data anywhere in this programme.
- Reference-system models (polaritons, magnons) are mathematics about
  other materials, retained for comparison only.
- Source-derived items remain at SRC/HYP and cannot be promoted by
  repetition, optimization, resemblance, or preference.
