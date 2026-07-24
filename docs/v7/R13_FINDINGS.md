# R13 — Complete Cross-Domain Discovery and Experiment Architecture

**Authority:** RGCS R13 / v7.0.0 (candidate)
**Scope:** the 32 `r13/` modules, 48 phase receipts under `docs/v7/receipts/`,
and the cross-domain governance carried from R12.
**Baseline:** branch `v630-r13`, cut from `main` at `8ae9574` (v6.3.0
provenance successor).
**Related code / tests:** `r13/*.py`, `tests/v6/test_r13_*.py`.
**Known limitations:** nothing measured; no bench, no DFT force constants, no
neutron facility, no beam time, no specimen, no acquired data.
**Next review trigger:** any bench/observational data, a DFT force-constant
set, an IGRF grid, or R14.

---

## What R13 is

R13 is a **complete software simulation and experiment architecture**: one
common linear-response core, an atomistic → continuum → electrical quartz
chain, the symplectic / Floquet / quasi-phase-matching transform layer, a
full (preregistered, unbuilt) apparatus and detector stack, synthetic neutron
and X-ray predictions, and the finalized coordinate codec with its blinded
decoder holdout. Every phase in the R13 pack (48 of them) carries a complete
receipt; the pack's non-deferral command is met — no phase was reduced to a
backlog note.

Nothing here is a measurement. The strongest claim class any module reaches
from software alone is `REPOSITORY_COMPUTATIONAL_RESULT`, and the governance
core forbids the seven promotions that would turn computation into a physical
claim.

## The three standing rules

1. **Simulation is not measurement; a certificate is not evidence.** A
   cross-domain transfer may be *licensed* by a coupling certificate (nine
   declarations including a falsifying measurement), but until that
   measurement is performed — and none can be here — the certificate is an
   `ENGINEERING_CANDIDATE`, never a bench result.
2. **No promotion.** Seven named refusals (`r13/claimtypes.py`): algebraic
   similarity ↛ physical equivalence; simulation ↛ measurement; numeric match
   ↛ source authentication; unclosed energy ↛ new energy; planar uniformity
   ↛ 3-D isotropy; coordinate alias ↛ decoded destination; exotic-particle
   paper ↛ carrier evidence. The red team (P43, `test_r13_redteam.py`)
   attacks all seven plus the bridge/alias/energy/isotropy governance — 16
   attacks, all refused.
3. **Blocked is stated, not hidden.** Where a phase needs a bench, DFT force
   constants, a neutron facility, or beam time, it carries a complete
   `BLOCKED_MISSING_INPUT` receipt (phases 25–30 preregistered-not-run;
   33 facility; 34 submission; 45 build) and every other phase continues.

## The load-bearing physics results (all model, all falsifiable)

- **Linear-response core** (`response`): Kramers–Kronig consistency,
  S-matrix unitarity, damped-oscillator Green function — reproducing
  textbook identities validates the *code*, not a transfer.
- **Quartz chain** (`crystalframe`, `atomistic`, `homogenize`,
  `piezobridge`): direct/reciprocal frame identity `aᵢ·bⱼ = 2π δᵢⱼ`;
  analytic phonon dispersion with an enforced acoustic sum rule; the k→0
  slope equals the continuum sound speed; a piezo→BVD bridge emitted as a
  certificate `AWAITING_FALSIFICATION`.
- **Transform layer** (`symplectic`, `quadfield`, `qpm`, `floquet`,
  `boundaryenergy`, `heterodyne`): rotation preserves the variance sum while
  squeeze splits it (the discrimination that stops "parametric gain" being
  called "passive rotation"); parametric-resonance tongues; a boundary energy
  ledger whose unclosed residual interval includes zero.
- **Coordinate codec** (`coordfinal`, `holdout`, `magroot`, `shellmap`,
  `epochsolve`, `serialize`): the finalized icosahedral codec is an exact
  bijection at the symbol level but decodes to a **32-member alias set** with
  no field selecting a frame; the magnetic root is a locus, not a place; the
  epoch solver returns a residue class, not a timestamp. The independent-
  vector protocol (P42) is the falsification hook, and against the alias set
  the decoder does not beat chance — evidence *against* a unique decode.

## The headline non-claims

- No cross-domain transfer is **measured**. The three-domain benchmark (P30)
  is a certificated `ENGINEERING_CANDIDATE` path, not a measured transfer.
- No **new energy**. Every ledger that closes does so on synthetic terms;
  every real term is `BLOCKED_MISSING_INPUT`.
- No **isotropic emission**. The six-angle ring samples one plane; six
  samples even alias angular order 6 to 0.
- No **decoded destination** and no **authenticated source**. The codec
  yields alias sets; numeric and hash matches prove range/integrity, not
  identity.
- No **carrier**. No registered paper is treated as evidence for an RGCS
  carrier.

## Verdict

`R13_GREEN_COMPLETE_SOFTWARE_SIMULATION_AND_EXPERIMENT_ARCHITECTURE_NO_BENCH_CLAIM`.

This manuscript agrees with the code: every result above is produced and
tested by a named `r13/` module (`tests/v6/test_r13_*.py`), and every
non-claim is enforced by a refusal that the red-team suite exercises.
