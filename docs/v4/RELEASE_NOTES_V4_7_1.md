# RGCS v4.7.1 — R3: Root-Space Resolver, Phase Lens, Optical Spin, HAL Memory, Nested Atlas

**SOFTWARE_VERIFIED, PHYSICAL_UNTESTED.** No apparatus, no data, no
detected residual, no transport. All prior tags untouched.

Full account: [R3 findings](pmwr/R3_FINDINGS.md) · manuscript §14.

## The R3 correction

A root is **not** "the first place where the phase residual is zero":
`wrap(φ) = 0` admits integer-cycle aliases — **4 097 zero-residual
candidates per second** of search window at 4096 Hz. R3 defines a root
as a typed, calibrated, alias-resolved, gauge-declared,
uncertainty-bounded **relational** reference state, in six typed
classes with six forbidden collapses enforced as refusals. The
strongest certificate any pipeline can emit is `ROOT_LOCK_BOUNDED`;
`ABSOLUTE_VACUUM_ROOT_UNSUPPORTED` and
`NONLOCAL_REFERENCE_FRAME_UNSUPPORTED` are standing statuses.

## Highlights

- **Root-space resolver** (`r3/root_space.py`): dual-lattice alias
  thinning, gauge orbits requiring declared representative rules,
  GPS-style emission-coordinate localization from ≥4 reference
  worldlines (relational frame by construction; 3 worldlines →
  `ROOT_PARTIALLY_IDENTIFIED`), and a root-lock certificate that
  evaluates every criterion or fails with the honest status.
- **Anisotropic phase lens**: calibrated forward operator, computed
  observability, Tikhonov inversion (unregularized inversion
  refused), adjoint verified to 1e-12, declared discrepancy floor.
  L ≠ Lᵀ is anisotropy, not one-way physics.
- **Tetrahedral addressing**: exact 8^d hierarchy (1→8→64→512→4096),
  round-trip-tested base-8 codec, five declared K semantics, and a
  destination certificate requiring frame/epoch/metric/ephemeris/
  uncertainty/calibration — an address alone is bookkeeping.
- **Spin/torsion + metric boundary**: seven categories that never
  merge; Einstein–Cartan torsion from a fully polarized solid is
  ~6×10⁻²⁵ m⁻¹ (unmeasurable, stated); the inverse Einstein
  calculator prices a part-per-billion metric wish at **6.7×10¹⁷ kg**
  — `REFUSED_BY_ARITHMETIC`.
- **Optical spin**: SAM/OAM never merge; voxel dose ceiling-checked;
  quartz spin transfer stays `OPERATIONAL_HYPOTHESIS`; relaxation
  refuses infinite memory and T2 > 2T1.
- **HAL memory**: synthetic-only records on tetrahedral addresses;
  personal data refused at the constructor; consent audit proves the
  invariant.
- **Nested atlas**: an Earth tetrahedral grid is a
  `REPRESENTATION_ARTIFACT`; the null-rotation campaign rejects
  orientations that don't beat seeded random rotations (planted
  vertices detected as positive control); nodal-point claims have
  no supported physical rung; cross-frame addresses need ordered
  frame chains.
- **L'ou source log** preserved verbatim and sha256-pinned in the
  pack, with the append-only ingest policy honoured.
- **Governance:** `enforce_admins` on main is now **ON** (operator
  action) — the R2 gap is closed technically, and Gate Zero
  re-verified v4.7.0 by object ID and fresh download before any work.
- Workbook: 26 sheets (2 new R3 sheets from the canonical store).

## Verify

```bash
python -m pytest -q --deselect tests/regression/test_generator_determinism.py::test_generator_deterministic
# expect: 1153 passed
python -m pytest tests/v4/test_r3_all.py -q     # the R3 suite (40)
python tools/qa_audit_v4.py --fast              # 19/19
```

## Boundary

Nothing here is evidence of a vacuum origin, a preferred frame, a
grid in the Earth, any nodal-point mechanism, spacetime torsion
from a lab source,
metric actuation, spin storage in quartz, or any residual. Bounded
relational root lock against declared references is the ceiling, and
even that is demonstrated on synthetic channels only.
