# RGCS Workbench Public RC2 Release Notes

Date: 2026-08-05
Tag: workbench-v1.0.0-rc2
Supersedes: workbench-v1.0.0-rc1

## Verdict

```text
RGCS_WORKBENCH_PUBLIC_RC2_READY
NO_PHYSICAL_CLAIM_ADVANCED
TERRA_RC4_PRESERVED
RELEASE_FILTER_CLEAN
ALL_TESTS_PASS
CI_GREEN_ON_MAIN
```

## What changed since RC1

RC1 shipped with a locally green suite; the first public CI run then
failed on three platform and hygiene defects. RC2 is RC1 plus those
fixes, cut from a tree that is green locally AND on CI.

1. A test comment and skip reason named the private repository
   literally. The r10 privacy firewall flagged both lines on the
   committed tree. The wording now says "the private archive" and the
   firewall passes. The old literal remains only in git history,
   where it is a declared, non-blocking residual by policy; history
   is not rewritten.
2. The manifest tamper test mutated the checksum text with a
   replacement that was a no-op on CI, because checkout line endings
   change file hashes per platform. The tamper is now a deterministic
   digit flip and the test detects it everywhere.
3. The diatomic Gamma-point check held an eigensolver zero to 1e-9,
   tighter than BLAS noise across platforms. The eigensolver assert
   now allows 1e-7, still eight decades below the optical branch;
   the closed-form assert keeps 1e-12.

## What this release is

RGCS Workbench is a public research workbench for reproducible
coordinate parsing, phase and resonance modeling, measurement
planning, and provenance tracking. Physical interpretations remain
hypothesis gated unless backed by bench receipts and independent
validation.

## What this release is not

This release does not claim propulsion, lift, antigravity, gravity
control, source authentication, free energy, or validated craft
performance. The claim firewall scans every tracked markdown file
and the cage's own code and data as a standing release gate.

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

## Workbench lanes

Unchanged from RC1: variable-length codec parse receipts and
correction ledger, crystal measurement objects with a bench-receipt
gate, Phyrll measurement lane with force fields refused, H-ME-SSP-001
protocol and derived arithmetic, craft-path hypothesis registry and
archive schema with public-safe seed records, claim firewall, and
the release manifest and checksums (release/workbench-rc2).

## Receipts

Suite at the RC2 content commit: recorded in the seal commit
message, zero failures required. CI run on the same fixes: green
(run 31028439454 on commit 7040b96). A fresh clone runs the suite
without any private files present.
