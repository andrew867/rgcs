# RGCS v7.0.0 — R13 Complete Discovery and Experiment Architecture

**Release date:** 2026-07-24
**Predecessor:** v6.3.0 (R12)
**Final verdict:**
`R13_GREEN_COMPLETE_SOFTWARE_SIMULATION_AND_EXPERIMENT_ARCHITECTURE_NO_BENCH_CLAIM`

---

## What R13 adds

R13 executes the full 48-phase discovery-and-experiment pack as the new
`r13/` package — **32 modules, 32 test files, and 48 phase receipts**
(`docs/v7/receipts/`). Nothing here is a measurement; the strongest claim
class any module reaches from software alone is
`REPOSITORY_COMPUTATIONAL_RESULT`.

### The architecture

- **Governance core** (`claimtypes`): the claim ladder and the seven
  forbidden promotions, enforced as typed refusals.
- **Common linear-response core** (`response`, `bridgegraph`, `srcregistry`):
  Green functions, Kramers–Kronig consistency, S-matrix unitarity, and a
  certificate-gated coupling-graph search that extends R12's bridge rule.
- **Quartz chain** (`crystalframe`, `atomistic`, `homogenize`,
  `piezobridge`): direct/reciprocal frame, an analytic phonon model with an
  enforced acoustic sum rule, homogenization to continuum elasticity, and a
  piezo→BVD bridge emitted as a certificate `AWAITING_FALSIFICATION`.
- **Transform layer** (`symplectic`, `quadfield`, `qpm`, `floquet`,
  `avoided`, `chiral`, `boundaryenergy`, `heterodyne`): the rotation-vs-squeeze
  discrimination, quasi-phase-matching, Floquet tongues, avoided crossings,
  chiral phonons, and a boundary energy ledger that closes with no new energy.
- **Apparatus & detector stack** (`apparatus`, `qcmstack`, `sixangle`,
  `imaging`, `daq`, `diskdrive`): all preregistered designs — **nothing is
  built** — with the six-angle ring's planar-uniformity-is-not-isotropy rule.
- **External validation** (`euphonic`, `scattering`): a force-constant
  interface (real DFT `BLOCKED_MISSING_INPUT`) and synthetic INS/IXS
  predictions.
- **Coordinate codec** (`coordfinal`, `holdout`, `magroot`, `shellmap`,
  `epochsolve`, `serialize`): the finalized icosahedral codec that decodes
  only to a 32-member alias set, with a blinded decoder holdout.
- **Prospective experiments & controls** (`experiments`, `preregister`): six
  preregistered, not-run bench experiments and the sealing/blinding protocol.

### The red team

`tests/v6/test_r13_redteam.py` attacks all seven promotions plus the bridge,
alias, energy, and isotropy governance — **16 attacks, all refused**.

## Non-claims (unchanged discipline)

No cross-domain transfer is measured; no new energy; no isotropic emission;
no decoded destination; no authenticated source; no carrier. Bench, DFT
force constants, neutron facility, and beam time are all
`BLOCKED_MISSING_INPUT`, stated explicitly in phases 25–30, 33, 34, 45.

## Provenance

Additive: no prior work reset, no public history rewritten.
`PHYSICAL_VALIDATION_NOT_CLAIMED`.

# expect: 5638 passed (1 archived-environment byte test deselected by
policy D-V3-04)
