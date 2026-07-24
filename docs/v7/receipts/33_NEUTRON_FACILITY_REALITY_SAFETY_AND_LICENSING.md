# R13 Phase Receipt

```text
phase_id: 33
phase_title: Neutron Facility Reality, Safety, and Licensing
status: BLOCKED_MISSING_INPUT
start_commit: 8ae9574
end_commit: v7.0.0 (branch v630-r13)
files_added: none (deliverable is this receipt / safety determination)
files_modified: none
tests_added: 0
focused_test_result: n/a (no module; deliverable is a receipt)
full_regression_result: 5638 passed, 8 skipped, 1 deselected, exit 0
source_hashes_used: build_meta source hash over SOURCE_ROOTS incl. r13
claim_classes_emitted: BLOCKED_MISSING_INPUT
private_files_read: false
```

## Work completed

Recorded the facility requirements for an inelastic-neutron-scattering
validation of the phase-32 phonon predictions, and issued a firm safety
determination prohibiting home / DIY neutron work. No module is added; the
deliverable is this receipt.

**Safety determination (firm).** No neutron generation or neutron scattering
is done, designed for home use, or endorsed here. Any INS validation requires
a **licensed national user facility** — a research reactor or a spallation
source — operated under professional health-physics control. This is not
achievable, and must not be attempted, outside such a facility.

Prohibited: any home, garage, or amateur neutron source (sealed isotope
sources, D-D / D-T generators, accelerator targets, or "fusor"-type devices);
any attempt to produce, moderate, or detect neutrons outside a licensed,
supervised facility.

## Evidence and equations implemented

None. This is a facility-reality and safety receipt, not a computation. The
scientific basis it would support is the synthetic `S(Q,w)` from phase 32 and
the dispersion / DOS from phase 31.

## Negative results

No facility, no beam, no data. Nothing here authorizes or describes how to
build a neutron source. The absence of data is stated, not worked around.
`PHYSICAL_VALIDATION_NOT_CLAIMED`.

## Deviations from prompt

None. The prompt asks to complete the facility requirements and prohibit
unsafe home neutron work; both are delivered, with the method held prohibitive
and the data held blocked.

## Blocking inputs, when applicable

This is a `BLOCKED_MISSING_INPUT` receipt; the eight required elements:

1. **Exact missing input:** access to a licensed neutron facility (a research
   reactor or spallation source) with an appropriate spectrometer (triple-axis
   or time-of-flight) and institutional safety approval.
2. **Sources / files / modules / tests searched:** the `r13` package (no
   neutron-source or facility module exists or was created);
   `r13/scattering.py` (phase 32, synthetic INS/IXS only) and `r13/euphonic.py`
   (phase 31, analytic dispersion only); the phase-20 apparatus receipt (no
   bench); no private files read.
3. **Work completed without it:** facility-only requirements recorded below;
   firm prohibition of home / amateur neutron work issued.
4. **Safe fallback implemented:** the only safe work is the phase-31 / 32
   simulations, which stand as `ANALYTIC_MODEL` / `PROSPECTIVE_PREDICTION`;
   facility requirements captured for a real collaboration only.
5. **Modules or claims still unavailable:** any measured `S(Q,w)`; any INS
   detection; any facility data. No RGCS carrier is validated.
6. **Machine-testable reopening condition:** a documented access grant to a
   licensed reactor / spallation facility with institutional safety-committee
   approval on file (beam-time award identifier recorded).
7. **Responsible owner / source class:** a national neutron user facility
   (its safety, licensing, and health-physics organization).
8. **Confirmation other phases continued:** phases 34-48 proceeded; the full
   regression (5638 passed, 8 skipped, 1 deselected, exit 0) was unaffected by
   this block.

Facility requirements recorded for a real collaboration only: a licensed
reactor or spallation source with an appropriate spectrometer; biological
shielding, interlocks, and radiation-area controls; personal dosimetry and
trained radiation workers; facility licensing and institutional review /
safety-committee approval; a sample-safety and activation-disposal plan.

## Downstream impact

Gates any physical neutron validation of phases 31/32 behind a licensed
facility and forecloses the unsafe home path; phase 34's proposal draft rests
on this determination for its safety section.

## Reopening test

Reopen when there is access to a licensed reactor / spallation facility with
institutional safety approval (a recorded beam-time award); until then the
method stays prohibitive and the data stays blocked.

## Acceptance checklist

- [x] Firm prohibition of home / amateur neutron work issued.
- [x] Facility-only requirements recorded for a real collaboration.
- [x] All eight BLOCKED_MISSING_INPUT elements addressed.
- [x] No neutron-source method described or endorsed.
- [x] Other phases confirmed to have continued; regression unaffected.
- [x] Claim class `BLOCKED_MISSING_INPUT`; no physical validation claimed.
