# RGCS Workbench Public RC1 Cage Notes

Date: 2026-08-04

## Verdict for this stage

```text
RGCS_WORKBENCH_PUBLIC_RC1_CAGE_READY
NO_PHYSICAL_CLAIM_ADVANCED
TERRA_RC4_PRESERVED
RELEASE_FILTER_CLEAN
```

This is the cage stage, not the full RC1. The cage is the boundary
layer that goes in before any physical hypothesis module is imported.
`RGCS_WORKBENCH_PUBLIC_RC1_READY` and `ALL_TESTS_PASS` are reserved
for the packaged RC1 after the module imports land.

## What this stage is

RGCS Workbench is a public research workbench for reproducible
coordinate parsing, phase and resonance modeling, measurement
planning, and provenance tracking. Physical interpretations remain
hypothesis gated unless backed by bench receipts and independent
validation.

This stage adds, in code with tests:

1. The public module registry for MOD-001 through MOD-008, with exact
   status strings and a mapping from each module to the packages that
   already exist in this repository.
2. The claim firewall. It blocks banned physical-claim phrases in
   public claim text outside refused-claim contexts, and it runs as a
   release-gated test today.
3. The frozen Terra RC4 reference. Metadata is pinned by test and the
   adapter refuses, by raising an exception, any code path that would
   promote the profile to a validated physical endpoint.
4. Release-matrix tests for all sixteen rows of the pack's test
   matrix, every row wired for real. The deeper per-module spec tests
   live beside them in tests/release_cage.
5. Public lane modules in the cage: codec parse receipts and a
   correction ledger over the rgcs_coordinate variable-length codec,
   crystal measurement-record validation with a bench-receipt gate,
   the Phyrll measurement-lane schema that refuses force output
   fields, the append-only craft-path hypothesis registry with the
   public-safe frequency spine, the archive provenance schema with
   the four-step community intake rule, and the release manifest and
   SHA256SUMS builder with completeness validation.

## What this stage is not

This release does not claim propulsion, lift, antigravity, gravity
control, source authentication, free energy, or validated craft
performance. No force, thrust, or power-to-performance calculation
was added anywhere in the cage, and the firewall tests fail the suite
if such a claim enters the gated public text.

## Terra status

RGCS Terra RC4 remains the frozen operational calibrated profile.
The workbench references it read-only.

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
No map screenshot and no manual map verification counts as a receipt.

## Module registry at cage stage

```text
MOD-001 Variable-Length Coordinate Codec   PUBLIC_WORKBENCH                        MAPPED_EXISTING
MOD-002 Terra Public Profile Adapter       OPERATIONAL_CALIBRATED_PROFILE_REFERENCE MAPPED_EXISTING
MOD-003 Crystal Phase Engine               MEASUREMENT_HYPOTHESIS_NOT_VALIDATED    PARTIAL_EXISTING
MOD-004 Phyrll Generator Measurement Lane  BENCH_PROTOCOL                          MAPPED_EXISTING
MOD-005 H-ME-SSP-001 Slow-Wave Hypothesis  PUBLIC_RESEARCH_HYPOTHESIS_NOT_VALIDATED PARTIAL_EXISTING
MOD-006 Craft-Path Hypothesis Registry     HYPOTHESIS_REGISTRY                     CAGE_ONLY_PENDING_IMPORT
MOD-007 Source and Provenance Archive      PUBLIC_ARCHIVE_RECORD                   PARTIAL_EXISTING
MOD-008 Release Filter and Manifest        RELEASE_GATE                            MAPPED_EXISTING
```

The machine-readable copy lives at
`rgcs_workbench/public_cage/module_registry.json` and is validated by
`tests/release_cage/test_cage_module_registry.py` against the live
tree.

## H-ME-SSP-001 boundary statement

H-ME-SSP-001 defines a slow-wave annular measurement hypothesis. It
does not claim thrust, lift, gravity control, or source validation.
Bench measurement and independent replication remain pending.

The derived arithmetic (sector angle 360/37, outer sector pitch from
a 288 mm outer diameter, external resonance 4096 x 411 = 1,683,456
Hz, and the resulting slow phase velocity near 41,000 m/s) is checked
by test as MATHEMATICAL_DERIVATION. Arithmetic is not evidence of a
physical effect.

## Gates that remain open before RC1

```text
craft-path record DATA import (schema and registry are live)
archive record DATA import (schema and intake rule are live)
public RC1 package build with release-time manifest emission
fresh-clone test on the packaged file set
full-package claim scan at packaging time
```

Schemas, validators, and gates are all live and tested. What remains
is data import and the packaging run itself. Nothing is quarantined
silently: the test suite carries zero skipped cage tests.
