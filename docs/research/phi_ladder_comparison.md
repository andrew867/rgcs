# Phi Ladders Against the RGCS Frequency Spine

Status: PUBLIC_RESEARCH. SOURCE_REPORTED_ARITHMETIC. NOT_RGCS_VALIDATION.

## Purpose

Record three phi-power ladders extracted from a source paper on
golden-ratio fractality and from the Dan Winter phi-Schumann
cascade, and compare them against the RGCS frequency spine without
merging the families. The source paper's physical interpretation,
that phi fractality and phase conjugation cause gravity through
perfected compression, stays source language. RGCS reproduces the
arithmetic and compares numbers; the claim is not advanced.

## External anchors

The uploaded gravity-paper review (source ledger in the private
archive; arithmetic preserved here), the Dan Winter phi-Schumann
cascade table, and the RGCS frequency spine
(`rgcs_workbench/public_cage/physics_spine_entries.json`).

## RGCS operator

```text
phi = (1 + sqrt(5)) / 2
PHI_SCHUMANN:           freq_n = 7.83 * phi^n
PHI_PLANCK_TIME:        freq_n = 1 / (t_p * phi^n)
PHI_PLANCK_LENGTH:      length_n = L_p * phi^n
```

Source-paper constants are preserved verbatim for reproduction
(t_p = 1.35125e-43 s, L_p = 1.616252e-35 m); they are the paper's
values, deliberately not CODATA updates. Reproduced checkpoints,
all SOURCE_REPORTED_ARITHMETIC:

```text
L_p * phi^116 = 0.282537 Angstrom
L_p * phi^117 = 0.457154 Angstrom
L_p * phi^118 = 0.739691 Angstrom
1 / (t_p * phi^171) = 13.563688 MHz
7.83 * phi^13 = 4079.445 Hz
7.83 * phi^16 = 17280.806 Hz
```

## Near-neighbor separation rule

The phi ladder and the RGCS octave ladder are different families.
Near neighbors stay distinct; a pairing is a CANDIDATE_BRIDGE with a
recorded offset, never a merge, and no merge happens without an
explicit correction rule.

```text
4079.44 Hz is not 4096 Hz          (offset -0.40 percent)
20.4992 Hz is not 20.48 Hz         (offset +0.09 percent)
13.563688 MHz is not 13.18359375 MHz (offset +2.88 percent)
```

## Bench observables

None directly; this is a comparison lane. It feeds the crystal
triage lane, where estimated mechanical modes are compared to both
families and then measured.

## Claim boundary

This lane claims reproducible arithmetic and recorded offsets. It
does not claim that phi ladders cause gravity, select crystals, or
validate any physical effect. Source language and RGCS conclusions
stay separated by classification labels.

## Next tests

1. Keep the ladder tables regenerating from the formulas by test.
2. Hold the near-neighbor separations by test.
3. Compare measured crystal modes, when they exist, to both families
   with the same offset arithmetic.
