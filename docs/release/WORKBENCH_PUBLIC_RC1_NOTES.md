# RGCS Workbench Public RC1 Release Notes

Date: 2026-08-05
Tag: workbench-v1.0.0-rc1

## Verdict

```text
RGCS_WORKBENCH_PUBLIC_RC1_READY
NO_PHYSICAL_CLAIM_ADVANCED
TERRA_RC4_PRESERVED
RELEASE_FILTER_CLEAN
ALL_TESTS_PASS
```

## What this release is

RGCS Workbench is a public research workbench for reproducible
coordinate parsing, phase and resonance modeling, measurement
planning, and provenance tracking. Physical interpretations remain
hypothesis gated unless backed by bench receipts and independent
validation.

## What this release is not

This release does not claim propulsion, lift, antigravity, gravity
control, source authentication, free energy, or validated craft
performance. The claim firewall runs as a standing release gate over
every tracked markdown file in the repository and over the cage's
own code and data.

## Terra status

RGCS Terra RC4 remains the frozen operational calibrated profile.

```text
repo: andrew867/rgcs-terra
tag: v1.0.0-rc4
commit: 4fdee3e7fbdb416d8e4b32dcb422d0977e6f20af
verdict: GREEN_TERRA_ALIGNMENT_SOLVED_CALIBRATED_V1
B01A=CLOSED
B02A=CLOSED
B01B=VALIDATION_PENDING
B02B=PHYSICAL_VALIDATION_PENDING
B10=OPEN
```

Independent physical endpoint validation remains HOLDOUT_REQUIRED.

## New workbench lanes

```text
variable-length coordinate codec with parse receipts and a
  correction ledger (rgcs_coordinate + public_cage/codec_receipts)
crystal phase engine measurement objects with a bench-receipt gate
Phyrll generator measurement lane schema, force fields refused
H-ME-SSP-001 annular slow-wave measurement hypothesis, protocol and
  derived arithmetic checked by test
craft-path hypothesis registry, append-only, public-safe seed
  records imported
source and provenance archive schema, four-step community intake,
  public-safe seed records imported
claim firewall and full-tree release scan
release manifest and checksums (release/workbench-rc1)
```

## Status language

```text
PUBLIC_WORKBENCH
OPERATIONAL_CALIBRATED_PROFILE
MEASUREMENT_HYPOTHESIS_NOT_VALIDATED
PHYSICAL_VALIDATION_PENDING
HOLDOUT_REQUIRED
NO_PHYSICAL_CLAIM_ADVANCED
```

## Receipts

Test receipts for this release line: baseline 8022 passed before the
cage; 8124 passed after the cage; the record import and packaging
additions raise the count further and the final number is recorded
in the seal commit message. Zero failures at every step. A fresh
clone runs the suite without any private files present; the private
source corpus stays in the private repository.

The machine-readable module registry is
`rgcs_workbench/public_cage/module_registry.json`. The release
manifest and SHA256SUMS live in `release/workbench-rc1/`.
