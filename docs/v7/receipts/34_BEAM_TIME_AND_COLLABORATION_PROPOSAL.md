# R13 Phase Receipt

```text
phase_id: 34
phase_title: Beam-Time and Collaboration Proposal
status: BLOCKED_MISSING_INPUT
start_commit: 8ae9574
end_commit: v7.0.0 (branch v630-r13)
files_added: none (deliverable is a proposal draft recorded in this receipt)
files_modified: none
tests_added: 0
focused_test_result: n/a (no module; deliverable is a receipt / draft)
full_regression_result: 5638 passed, 8 skipped, 1 deselected, exit 0
source_hashes_used: build_meta source hash over SOURCE_ROOTS incl. r13
claim_classes_emitted: BLOCKED_MISSING_INPUT
private_files_read: false
```

## Work completed

Produced a complete proposal **draft structure** for a neutron or synchrotron
beam-time request, resting on the phase 31/32 simulations. **No proposal is
submitted and no beamtime is granted or requested.** No module is added; the
deliverable is the recorded draft below.

Draft proposal structure (recorded, not submitted):

1. **Scientific case.** The candidate quartz phonon modes and putative
   couplings, framed in conventional lattice-dynamics terms.
2. **Feasibility from simulation.** The synthetic `S(Q,w)` from
   `r13/scattering.py` and the dispersion / DOS from `r13/euphonic.py`,
   labelled `PROSPECTIVE_PREDICTION` — showing which modes fall in an
   accessible `(Q,w)` window for a named spectrometer class.
3. **Preliminary data.** *Required and absent.* A real proposal needs
   conventional bench characterization (Raman / BVD / ring-down) first.
4. **Beamtime request.** Instrument class, sample environment, and hours —
   left as a template, not a submission.
5. **Safety.** Per phase 33: licensed facility only; no home neutron work.

## Evidence and equations implemented

None new. The feasibility section cites the phase-32 synthetic `S(Q,w)` and
the phase-31 analytic dispersion / DOS; no measurement is performed here.

## Negative results

A drafted proposal is not a submitted or accepted one, and simulated
feasibility is not preliminary data. No beamtime exists.
`PHYSICAL_VALIDATION_NOT_CLAIMED`.

## Deviations from prompt

The prompt asks for a credible proposal supported by simulation **and**
conventional preliminary data. The simulation support exists; the conventional
preliminary data do not (no apparatus — see phases 20, 33), so the proposal is
a draft only and submission is blocked.

## Blocking inputs, when applicable

Submission is `BLOCKED_MISSING_INPUT` over an `ANALYTIC_MODEL` /
`PROSPECTIVE_PREDICTION` simulation basis. The eight required elements:

1. **Exact missing input:** conventional preliminary bench data
   (Raman / BVD / ring-down) proving the sample and the candidate modes, which
   a real beam-time panel requires — no apparatus exists to produce them.
2. **Sources / files / modules / tests searched:** `r13/scattering.py` and
   `r13/euphonic.py` (simulation basis, present); the phase-20 apparatus
   receipt and phase-21 QCM/BVD/ring-down stack (no built bench); phase-33
   facility determination; no private files read.
3. **Work completed without it:** the full proposal draft structure above,
   with the simulation-backed feasibility section written.
4. **Safe fallback implemented:** the proposal draft rests on the phase 31/32
   simulations and is held unsubmitted; no facility contact is made.
5. **Modules or claims still unavailable:** a submitted / accepted proposal;
   any beam-time award; any preliminary or facility data.
6. **Machine-testable reopening condition:** real preliminary Raman / BVD data
   files exist for the sample (a recorded bench dataset the feasibility section
   can cite in place of the placeholder).
7. **Responsible owner / source class:** the experimental collaboration
   operating a conventional characterization bench (Raman / BVD / ring-down).
8. **Confirmation other phases continued:** phases 35-48 proceeded; the full
   regression (5638 passed, 8 skipped, 1 deselected, exit 0) was unaffected.

## Downstream impact

Records the proposal skeleton so that, once preliminary bench data exist, a
submission can be assembled without re-deriving the scientific case; keeps the
submission gated until real data are available.

## Reopening test

Reopen when real preliminary Raman / BVD data for the sample exist and can
replace the placeholder preliminary-data section; until then submission stays
blocked.

## Acceptance checklist

- [x] Complete proposal draft structure recorded, unsubmitted.
- [x] Feasibility rests on labelled phase 31/32 simulations.
- [x] Preliminary-data section marked required and absent.
- [x] Safety section defers to phase 33 (licensed facility only).
- [x] All eight BLOCKED_MISSING_INPUT elements addressed.
- [x] Other phases confirmed to have continued; regression unaffected.
- [x] Claim class `BLOCKED_MISSING_INPUT`; no physical validation claimed.
