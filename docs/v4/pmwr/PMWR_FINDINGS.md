# RGCS v4.7 — Phase Memory, Worldline Channel Recovery, Phryll Translation: findings

**Status: SOFTWARE_VERIFIED, PHYSICAL_UNTESTED.** No apparatus was
built, no data collected. Every physical hypothesis — including the
entire crystal-translation lane — is a `SOURCE_CLAIM` with an
engineering plan around it. No Phryll-detected state exists in v4.7,
by construction.

## Scientific centre

> A coherent signal carries measurable timing and phase history. A
> synchronized, calibrated receiver can estimate portions of that
> history **only when the observation and model make the inverse
> problem identifiable.**

## Gate Zero (P00)

v4.6 was re-verified independently rather than trusted from the
operator report: object IDs compared across local/remote refs, the
published portable ZIP re-downloaded, hash-matched, and the downloaded
binary executed (reports 4.6.0 @ `a04b910`, 13 panels). `v4.7-pmwr`
was branched from verified `origin/main`, not a local ref.

**Governance (A01):** `enforce_admins` on `main` is still OFF — the
permission system correctly refused to let the agent change repository
settings. Closing it needs the operator:
`gh api -X POST repos/andrew867/rgcs/branches/main/protection/enforce_admins`.
The practiced rule (only CI-verified commits reach main) held for
every v4.7 push.

## What was built (pmwr/)

- **Phase authority** (A11/A16): frequency + epoch + timescale +
  sync-state machine (9 states, no force flag) + cycle count that only
  a `PHASE_LOCKED` authority may assert and every lock loss surrenders.
  Two authorities without a synchronization method are incomparable —
  *regardless of Q*.
- **Finite-Q memory** (A17): ringdown `exp(-πft/Q)`; the phase-memory
  horizon is the earlier of amplitude death and phase diffusion
  (accumulated error ≥ π ⇒ `CYCLE_COUNT_UNKNOWN`). Infinite Q and
  beyond-horizon memory claims are refusals, not warnings.
- **Six signal stages** (A12): ideal → commanded → realized →
  propagated → observed → reconstructed as distinct types with no
  implicit conversion. Propagation always loses the cycle count — that
  loss *is* the inverse problem.
- **Causal firewall** (A32): arrival reordering is computed and named
  ordinary delay geometry; the audit's output cannot represent "causal
  reversal", and a prose lint refuses reversal language.
- **Worldline channel** (A30/A31): weak-field proper-rate offsets on
  the validated v4.6 fixtures (LEO net-negative, GPS +38.5 µs/day).
  Two receivers on different worldlines accumulate different proper
  phase — metrology, not travel.
- **Closure as alias** (A21): the exact 1/4096 s closure window of the
  4096/20480/40960 family is an alias grid — 4097 indistinguishable
  delays per second. **Exact closure is simultaneously the v4.6
  synchronization feature and the v4.7 ambiguity.** A dual coprime
  lattice (adding a 4375 Hz family) extends the unambiguous range
  ×4096 (CRT).
- **Recovery with refusal** (A33-A42): least-squares path recovery
  runs only behind an identifiability gate reporting rank, condition
  number, and posterior width; underdetermined and ill-conditioned
  cases return `REFUSED` with reasons — never a best guess. Unwrapping
  returns candidate lists. Aliased path sets are detected as
  spoof-indistinguishable.
- **Crystal translation lane** (A43-A54): geometry schema with a
  mandatory reversed-orientation control; excitation registry where
  self-oscillation requires a closed loop *and* a declared energy
  source; translation-matrix entries are hypotheses with named
  ordinary mechanisms; the energy ledger flags output>input as
  `ACCOUNTING_ERROR`, never free energy.
- **Pyramid-ratio audit** (A44): at 51.843°, h/a = 1.2727376334 and
  2a/h = 1.5714157792 (pack values reproduced exactly); 2a/h sits
  within ~5×10⁻⁴ of π/2. That is a `GEOMETRY_IDENTITY` about a chosen
  angle. The Great Pyramid is an `ANTHROPOGENIC_STRUCTURE`; its slope
  is a design choice, not a physics constant, and the mechanism
  reading is refused in code.
- **Phryll operationalization** (A52): the five-rung ladder
  `SOURCE_CLAIM → … → CANDIDATE_NEW_MECHANISM`, one arrow at a time.
  A residual cannot be registered until **all eleven** ordinary output
  channels are measured *and* the sham-drive control has run — the
  source narrative itself records an effect reported while output
  power was not engaged, and that episode is preserved as the
  expectation-effect warning. `DETECTED_PHRYLL` does not exist; a test
  greps the package to keep it that way.
- **Benches** (A55-A68): three preregistrations (directional transfer
  with both orientations, self-oscillation containment with loop-open
  control, double-blind sham drive) plus the thirteen-item null set
  from the source claims. Apparatus `NOT BUILT`; hardware absence
  blocks every physical row (R29).

## Frozen before use

- Operator note preserved verbatim, sha256-pinned
  (`fff2f47e…`); it may be narrowed or rejected, never rewritten as a
  post-hoc prediction.
- Evaluation contract (refusal correctness, RMSE on seeded holdouts,
  alias disclosure) frozen and hash-pinned before estimator tuning.
- Novelty boundary: PLLs, ringdown, multipath estimation,
  multi-wavelength ambiguity resolution and GPS-style relativity are
  textbook and claimed as such; only the closure-alias analysis, dual
  coprime lattices, refusal semantics, and the guarded Phryll ladder
  are programme-specific.

## Adversarial campaign (A76-A78)

Attacks that fail to get through, by test: perfect memory (infinite Q,
beyond-horizon claims), universal key (privileged 4096), free energy
(over-unity ledger), Phryll-by-sensor-change (unmeasured channels,
missing sham control), pyramid-as-mechanism, rung-skipping promotion,
reversal language, physical-evidence emission from software.

## Public story labelling (A75 / R33)

Any public retelling of the source narrative must carry the METAPHOR /
SOURCE_CLAIM labels it carries here: "Phryll", the pyramid angle, and
the harvesting story are source terms under investigation-by-refusal,
not findings. The release notes' Boundary section is the public form
of this statement, and no v4.7 artifact presents a source term as a
result.

## Security, privacy, dual-use (A79 / R35)

- **Privacy:** the release processes no personal data; workbook
  exports are public-safe filtered as before.
- **Security:** the recovery lane's spoof check documents the real
  attack surface of phase-based ranging — aliased path sets are
  provably indistinguishable, so any downstream use of these
  techniques for authentication or localisation must treat closure
  aliases as spoofable. That disclosure is deliberate.
- **Dual-use:** multipath estimation, phase unwrapping, and integer
  ambiguity resolution are textbook GNSS/comms techniques; nothing in
  v4.7 extends adversary capability beyond the published state of the
  art, and no RF transmission capability is included (the v4.6 no-open-
  radiator gate stands).

## What would change any of this

Calibrated bench evidence under the preregistered protocols with
independent replication — and nothing else.
