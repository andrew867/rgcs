# R13 Phase Receipt

```text
phase_id: 35
phase_title: Raman, RIXS, IXS, and Electron-Scattering Alternatives
status: COMPLETE
start_commit: 8ae9574
end_commit: v7.0.0 (branch v630-r13)
files_added: none (deliverable is the literature ranking recorded in this receipt)
files_modified: none
tests_added: 0
focused_test_result: n/a (no module; deliverable is a literature-based ranking)
full_regression_result: 5638 passed, 8 skipped, 1 deselected, exit 0
source_hashes_used: build_meta source hash over SOURCE_ROOTS incl. r13
claim_classes_emitted: CONVENTIONAL_LITERATURE
private_files_read: false
```

## Work completed

Ranked external validation methods for the candidate quartz modes by mode
accessibility, resolution, cost / access, and sample requirements. No module
is added; the deliverable is the comparison table and ranking below. The
properties are drawn from established literature on each technique; no
measurement is performed.

| Method | Mode access | Resolution | Cost / access | Sample needs |
|---|---|---|---|---|
| **Raman** | Gamma-point optical modes (Raman-active) | sub-cm^-1 | low; benchtop, in-house | small crystal, optical polish |
| **INS** | full dispersion, all `(Q,w)` | ueV-meV | high; licensed reactor / spallation (phase 33) | large / deuterated sample |
| **IXS** | full dispersion, small samples | meV | high; synchrotron beamtime | small crystal |
| **RIXS** | element / edge-selective excitations | 10s meV | high; synchrotron beamtime | thin crystal / film |
| **Electron (EELS)** | local, high-Q | 10s meV (monochromated) | medium; TEM facility | thin lamella |

## Evidence and equations implemented

None. This is a literature-based method comparison, not a computation.

Ranking summary:

- **First / cheapest:** Raman — in-house, cheap, and the natural first
  conventional characterization, but limited to Raman-active zone-centre modes.
- **Full dispersion:** INS and IXS are complementary (INS for large samples and
  light elements; IXS for small crystals) but both need a national facility.
- **Specialized:** RIXS and EELS add element / local selectivity at higher
  complexity.

Recommended sequence: Raman / BVD in-house -> IXS or INS at a facility.

## Negative results

These are literature-based comparisons of techniques, not measurements made
with any of them. No mode has been validated.
`PHYSICAL_VALIDATION_NOT_CLAIMED`.

## Deviations from prompt

None. The prompt asks for a ranked comparison of alternative validation
methods, delivered as a literature-based table and recommended sequence.

## Blocking inputs, when applicable

None for the comparison itself (it is literature-based). Executing any listed
method is blocked on its respective apparatus / facility: Raman on an in-house
bench, INS on a licensed neutron facility (phase 33), IXS/RIXS on a synchrotron,
EELS on a TEM facility.

## Downstream impact

Sets the recommended validation order (Raman / BVD in-house first, then a
facility technique) that phase 34's proposal sequencing and any future bench
plan follow.

## Reopening test

Not a blocked phase. Reopen the ranking if new literature materially changes a
technique's mode access, resolution, or access cost for the candidate modes.

## Acceptance checklist

- [x] Raman / INS / IXS / RIXS / EELS compared on access, resolution, cost,
  and sample needs.
- [x] Ranking summary and recommended sequence stated.
- [x] Properties attributed to established literature; no measurement made.
- [x] Claim class `CONVENTIONAL_LITERATURE`; no physical validation claimed.
