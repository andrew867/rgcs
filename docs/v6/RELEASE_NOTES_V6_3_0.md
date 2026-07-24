# RGCS v6.3.0 — Release Notes

**Status:** `SOFTWARE_VERIFIED_PHYSICAL_UNTESTED`
**Baseline:** v6.2.0
**Licence:** MIT, unchanged. No relicensing.

R12: a new `r12` package — the icosahedral packet grammar, quaternary
refinement, eight shells, a South-referenced body frame, an IGRF-14
magnetic-root certificate, isotopic/astronomical epoch candidates, a
reciprocal-space crystal model, typed cross-domain coupling certificates,
and home-lab experiment plans. Nine modules, additive.

**Final verdict:
`R12_GREEN_ICOSAHEDRAL_AND_BRIDGE_ARCHITECTURE_IMPLEMENTED_NO_UNIQUE_DECODE`**

---

## The grammar — valid, and not a decoder

A 30-bit word parses as **F5 | Q22 | S3**: 5 face bits, 22
quaternary-refinement bits (11 levels × 2), 3 shell bits. All five
registered vectors decode exactly as the pack specifies (face 4, shared
`3301` path prefix).

**Headline null (R10.6 lesson, six tranches on):** the shared 13-bit binary
prefix is a fact about numeric **range**, not content — 14 bits are
*expected* from the values' span, band-clustering **p = 1.0** (random
same-band draws share a longer prefix on average) → `EXPLAINED_BY_RANGE`,
with a power control that catches a planted 24-bit prefix. Geographic
decoding is refused until face numbering, body orientation, magnetic root,
handedness and shell projection are all frozen — and even then the result
is `GRAMMAR_ONLY_NO_GEOGRAPHIC_CLAIM`.

## The cross-domain rule changed

R11.1 refused **every** transfer between physical domains. R12 supersedes
that (does not delete it):

```
NO_AUTOMATIC_EQUIVALENCE
TRANSFER_ALLOWED_WITH_EXPLICIT_COUPLING_CERTIFICATE
```

A transfer may now be licensed — by a certificate declaring all nine of:
domains; state variables and units; coupling operator; overlap; detuning
and damping; phase matching and symmetry; energy accounting; uncertainty
and null model; **and a falsifying measurement**. A complete certificate is
only `ENGINEERING_CANDIDATE` until measured, and nothing here can be
measured, so every certificate is `AWAITING_FALSIFICATION`. Certificates
are directional and do not compose. The default is still refusal.

## The rest of the mission

- **`bodylock`** — South-referenced frame **without a forced hemisphere
  inversion**; the double-inversion audit fires only when an improper op
  and a latitude flip cancel to net +1 while claiming to invert.
- **`shells8`** — 8 shells; four spacing laws give different radii for the
  same index, so the radial projection is `UNRESOLVED`; atomic-shell
  physics refused.
- **`igrf14root`** — IGRF-14 root, **epoch mandatory**, coefficient grid
  `BLOCKED_MISSING_DATA`, identification always refused.
- **`epochcand`** — Ba-130 / Cs-137 / Cs-133 / astronomical clocks span
  **38.5 orders of magnitude**; ~8.7×10¹⁸ aliases; no unique epoch.
- **`reciprocal`** — standard crystallography; `aᵢ·bⱼ = 2π δᵢⱼ` exact;
  reciprocal/Q-space **is not a place**.
- **`homelab`** — mode/phase/ringdown/isotropy experiments preregistered,
  **not run**; anisotropy in anisotropic quartz is the null, not an anomaly.

## Red team

Twelve attack families, each failing with a typed reason. The privacy guard
now recognises this pack's `private_do_not_commit/`.

## Verification

```bash
git clone https://github.com/andrew867/rgcs && cd rgcs
pip install -e ".[dev]"
pytest -q --deselect tests/regression/test_generator_determinism.py::test_generator_deterministic
# expect: 5175 passed
```

> **CI note.** Free-tier GitHub Actions minutes are exhausted; the
> verification of record is the full local suite on the exact commit.

## Scope

The pack ships **38 agent prompts**. This release implements the master
orchestrator's 10-item mission; the neutron/phonon theory, chiral-phonon
INS, beamtime, Floquet-QPM converter, response-function and related
sub-prompts are a **recorded R13 seed backlog**, deferred rather than
dropped.

## What this release does not claim

No externally transmitted address, no identified craft, no creation epoch,
no artificial geomagnetic structure, no novel particle, no anomalous energy
transfer. Mathematics, models and an experiment plan — nothing measured.

See [R12_FINDINGS.md](R12_FINDINGS.md) for the full analysis.
