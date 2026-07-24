# R12 — Icosahedral Packet Grammar, Reciprocal Bridge, Cross-Domain Certificates

**Authority:** RGCS R12 / v6.3.0 (candidate)
**Scope:** the nine `r12/` modules, the F5|Q22|S3 grammar, and the cross-domain rule change.
**Last verified commit:** v6.2.0 baseline (branch `v620-r12`)
**Prerequisites:** [R11_1_FINDINGS.md](R11_1_FINDINGS.md), [R11_FINDINGS_AND_NONCLAIMS.md](R11_FINDINGS_AND_NONCLAIMS.md)
**Related code / tests:** `r12/*.py`, `tests/v6/test_r12_*.py`
**Known limitations:** nothing measured; no bench, no IGRF coefficient grid, no diffraction pattern, no specimen. A large sub-prompt backlog is deferred (see Scope).
**Next review trigger:** any bench/observational data, an IGRF-14 coefficient set, or R13.

---

## Gate Zero

`main` = `13f52bc`, tag `v6.2.0` = `a6f8c94`, worktree clean, packaging
parity + privacy guards green, `private_do_not_commit/` guarded and never
read, 20 references hashed. The declared **tag/main provenance split** was
verified benign: **count 4936 in both**, only `exit_code` differs (tag 1
stale, main 0 real) — not a mismatch, so not a stop condition. R10/R11/R11.1
verdicts reconcile.

**Scope.** The pack ships **38 agent prompts**. This tranche implements the
**master orchestrator's explicit 10-item mission** as the `r12/` package.
The remaining sub-prompts — neutron/phonon theory, chiral-phonon INS,
neutron-facility safety, Euphonic simulation, beamtime proposal, home-lab
phonon detector, Floquet/QPM converter, response-function S-matrix, the
six-angle bench, and the R13 discovery handoff — are a **deferred R13 seed
backlog**, recorded rather than silently dropped.

## The icosahedral packet grammar — `…VALID_NOT_A_GEOGRAPHIC_DECODER`

A 30-bit word parses as **F5 | Q22 | S3**: 5 face bits (20 faces), 22
quaternary-refinement bits (11 levels × 2), 3 shell bits. All five
registered vectors decode exactly as the pack specifies (all face 4, shared
`3301` quaternary path prefix), with an exact encode/decode round-trip and
an injective collision scan.

**The headline null.** The five vectors share a 13-bit binary prefix. That
is a fact about their numeric **range**, not evidence of shared content:

- observed shared prefix: **13 bits**
- expected from the values' span (S ≈ 49,491): **14 bits**
- band-clustering **p = 1.0** — random draws from the same band share a
  *longer* prefix on average (null mean ≈ 13.56 bits)

→ `EXPLAINED_BY_RANGE`, with a power control that correctly flags a planted
24-bit prefix. This is the R10.6 band-clustering result holding six tranches
later. `refuse_geographic_decode()` always raises; a location requires face
numbering, body orientation, magnetic root, handedness **and** shell
projection all frozen — and even then the result is
`GRAMMAR_ONLY_NO_GEOGRAPHIC_CLAIM`.

Refinement geometry (`icosarefine`) is exact: `4¹¹` cells per face,
`20·4¹¹ = 83,886,080` fits 27 bits with ~50M codes of slack, cells are
genuinely **unequal-area** on the sphere, and the solid angle sums to 4π.

## The cross-domain rule change — `bridge`

R11.1 refused **every** transfer between physical domains. R12 supersedes
that (does not delete it):

```
NO_AUTOMATIC_EQUIVALENCE
TRANSFER_ALLOWED_WITH_EXPLICIT_COUPLING_CERTIFICATE
```

A transfer may now be *licensed* — but only by a certificate declaring all
nine of: source/target domains; state variables and units; coupling
operator; overlap/participation; detuning and damping; phase matching and
symmetry; energy accounting; uncertainty and null model; **and a falsifying
measurement**. A certificate missing any one is not weak — it is not a
certificate. Crucially, **a complete certificate is only
`ENGINEERING_CANDIDATE` until its falsifying measurement is performed**, and
no measurement can be performed here, so every certificate is
`AWAITING_FALSIFICATION`. Certificates license one direction and do not
compose. The default is still refusal (reusing the R11.1 reasoning).

## The rest of the mission

- **`bodylock`** — a South-referenced body frame **without a forced
  hemisphere inversion**. The double-inversion audit fires only when an
  improper operation *and* a latitude sign-flip cancel to net +1 while
  claiming to have inverted; a single honest reflection is allowed.
- **`shells8`** — exactly 8 shells (2³). Four spacing laws (linear,
  geometric, hydrogenic n², logarithmic) give **different radii for the same
  index**, so the projection is `UNRESOLVED`; the atomic-shell reading is an
  analogy only and is refused as physics.
- **`igrf14root`** — an IGRF-14 magnetic-root certificate with a
  **mandatory epoch** (the field drifts; secular variation is nonzero). The
  coefficient grid is `BLOCKED_MISSING_DATA` and identification is always
  refused (reusing the R11 planetroot validator; Earth legitimately uses the
  dynamo method).
- **`epochcand`** — Ba-130, Cs-137, Cs-133 and astronomical time scales
  span **38.5 orders of magnitude** in characteristic time. Combining them
  leaves ~8.7×10¹⁸ integer-cycle aliases; no unique epoch. Cs-133 is a
  frequency standard, not a dating clock.
- **`reciprocal`** — standard crystallography: `aᵢ·bⱼ = 2π δᵢⱼ` exact, the
  quartz cell, hexagonal d-spacing, structure-factor extinctions.
  Reciprocal/Q-space **is not a place** — `refuse_qspace_as_geographic()`.
- **`homelab`** — mode/phase/ringdown/isotropy experiments, preregistered
  and **not run**. Ringdown Q recovered from synthetic decay (a computation,
  not a measurement); isotropy null p ≈ 0.47, planted-anisotropy power
  p ≈ 0.0005. Anisotropy in an anisotropic crystal is the **null**, not an
  anomaly.

## Red team

Twelve attack families, each failing with a typed reason: grammar-as-decoder,
prefix-as-content, single-layout, decimal-as-octal, forced hemisphere
inversion, radius-from-bare-index, eight-shells-as-atomic, root-without-epoch,
root-identification, unique-epoch, reciprocal-space-as-a-place,
anisotropy-as-anomaly, uncertified transfer, certificate-as-evidence, and a
private-provenance leak (the guard now recognises this pack's
`private_do_not_commit/`).

## Final verdict

```
R12_GREEN_ICOSAHEDRAL_AND_BRIDGE_ARCHITECTURE_IMPLEMENTED_NO_UNIQUE_DECODE
```

No externally transmitted address, no identified craft, no creation epoch,
no artificial geomagnetic structure, no novel particle, no anomalous energy
transfer. Mathematics, models and an experiment plan — nothing measured.

`PHYSICAL_VALIDATION_NOT_CLAIMED`
