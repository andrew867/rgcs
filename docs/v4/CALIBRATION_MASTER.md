# Calibration master (Agent C08)

Coverage: **A17**. Status: `REDUCED_ORDER_VALIDATED`.
Implementation: [`rscs2_core/calibration.py`](../../rscs2_core/calibration.py)
(v4.1 authority, extended by the v4.2 lanes).

## Scope

Deterministic calibration across specimens, apparatus, spiral bodies,
and cymatic disks. The v4.1 module supplies the machinery:
`ObservationLedger` (immutable observations), `fit_parameters`,
`track_drift`, `inverse_design`, `guarded_update`.

**Audit note (v4.2.1).** The v4.2.0 ledger satisfied A17 by pointing at
the existing v4.1 calibration module. Pointing at a prior module is not
evidence that the *new* lanes were integrated with it. The integration
status of each new lane is stated explicitly below rather than implied.

## Integration status per lane

| Lane | Calibration target | Status |
|---|---|---|
| Scanned specimen geometry | ideal vs scanned deviation | `INTERFACE_ONLY` — `metrology.scan_to_mesh` exists; **no scan data** |
| Harmonic family | L_N vs measured fundamental | `PROTOCOL_READY_HARDWARE_REQUIRED` — no specimens |
| BVD fitting | C0/R1/L1/C1 from admittance | `REDUCED_ORDER_VALIDATED` on synthetic sweeps only |
| Eye localization | candidate coordinate vs mesh level | `INSUFFICIENT_RESOLUTION` (see the Eye docs) |
| Spiral-cone design | geometry merit (ENG) | `ENGINEERING_PROTOTYPE` |
| Cymatic PCB targets | design_for_target radius | `ENGINEERING_PROTOTYPE` |
| Apparatus transfer functions | coil/transducer/cable | `REDUCED_ORDER_VALIDATED`, unmeasured |
| Manufacturing tolerances | dL/L sensitivity | `REDUCED_ORDER_VALIDATED` |
| Water nuisance variables | T/pH/conductivity covariates | `PROTOCOL_READY_HARDWARE_REQUIRED` |
| Human-loading nuisance | grip force, capacitance | `ETHICS_APPROVAL_REQUIRED` |

**Nothing in this table has been calibrated against measured data**,
because no measured data exists. Every row is either synthetic-validated
or blocked.

## Binding rules (enforced)

- **Immutable observations.** `ObservationLedger` refuses mutation of a
  recorded observation. Raw data cannot be edited to improve a fit.
- **Train/validation separation.** Fits report held-out validation;
  reusing validation data for fitting is a defect, not a technique.
- **Preregistered objectives.** The objective is declared before the
  optimizer runs. Changing the target after seeing the result is
  post-hoc target selection.
- **Optimizers cannot alter evidence status.** This is the one that
  matters most: a fit that lands beautifully does not promote a
  `SOURCE_HYPOTHESIS` to `DER`. `guarded_update` enforces the
  classification ceiling.
- **Non-identifiability is reported.** Broad parameter correlations are
  published, not hidden. A parameter that the data does not constrain
  is reported as unconstrained.

## Failure conditions

- Synthetic recovery fails → the fitter is wrong.
- A drift monitor shows the calibration moving between sessions → the
  apparatus is not stable and the data are not comparable.
- The optimizer returns a candidate that no manufacturing tolerance can
  hold → the design is not realizable and says so.

## Boundary

Do not optimize until an attractive result appears. Do not reuse
validation data. Do not hide correlations. The C08 prompt names all
three; the module's guards exist because they are the natural failure
modes of exactly this kind of work.
