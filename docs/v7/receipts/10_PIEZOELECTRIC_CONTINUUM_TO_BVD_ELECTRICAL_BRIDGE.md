# R13 Phase Receipt

```text
phase_id: 10
phase_title: Piezoelectric Continuum to BVD Electrical Bridge
status: COMPLETE
start_commit: 8ae9574
end_commit: v7.0.0 (branch v630-r13)
files_added: r13/piezobridge.py, tests/v6/test_r13_piezobridge.py
files_modified: none
tests_added: 11
focused_test_result: 11 passed
full_regression_result: 5638 passed, 8 skipped, 1 deselected, exit 0
source_hashes_used: build_meta source hash over SOURCE_ROOTS (incl. r13); references hashed by srcregistry
claim_classes_emitted: ENGINEERING_CANDIDATE
private_files_read: false
```

## Work completed

Derived the measurable electrical response from continuum quartz modes via the
piezoelectric constitutive equations. Verdict
**`PIEZO_TO_BVD_CERTIFICATE_ENGINEERING_CANDIDATE`**. The mechanical→electrical
transfer is gated by an R12 `CouplingCertificate` (`certificate()`), source
`MACROSCOPIC_ELASTIC`, target `ELECTRICAL_BVD`, declaring all nine items
including a falsifying measurement — because none exists here,
`measurement_performed=False`, the certificate is `AWAITING_FALSIFICATION` with
class `ENGINEERING_CANDIDATE`. `refuse_bvd_as_measured_crystal` and
`refuse_coupling_without_certificate` hold the line.

## Evidence and equations implemented

- Linear piezoelectric constitutive pair `T = c^E S − e^t E`, `D = e S + ε^S E`.
- Electromechanical coupling factor `k² = e²/(c^E ε^S)`, bounded in `[0,1)` and
  exactly zero when `e = 0` (no polar term, no bridge).
- Butterworth-Van Dyke reduction near resonance: a motional `R,L,C` branch in
  parallel with static capacitance `C0`, with series resonance
  `f_s = 1/(2π√(LC))` and parallel resonance `f_p = f_s√(1 + C/C0) > f_s`,
  where `C/C0` tracks `k²` — coupling factor and resonance split are the same
  physics two ways.
- `bvd_from_piezo` reduces a thickness-mode resonator to its four numbers;
  `bvd_impedance` exhibits the dip at `f_s` and peak at `f_p`.

## Negative results

No crystal exists, was cut, electroded, mounted or swept; no resonance,
motional parameter or impedance was measured. The mechanical→electrical bridge
is licensed by a certificate that is `AWAITING_FALSIFICATION` — a licence to
model, never evidence that the coupling is real. When `e = 0` the coupling
vanishes and there is no bridge at all.

## Deviations from prompt

None.

## Blocking inputs, when applicable

None — software/architecture phase. The certificate names the falsifying
measurement that would be required; no bench measurement exists in this
environment, which is why the certificate stays `AWAITING_FALSIFICATION`.

## Downstream impact

The BVD reduction is the electrical model consumed by the QCM/BVD ringdown
stack (21) and the cross-domain transfer benchmark (30); the certificate is
one edge in the coupling graph (06).

## Reopening test

Re-run `tests/v6/test_r13_piezobridge.py`; reopen if the verdict string
changes, if `k²` leaves `[0,1)` or is nonzero when `e=0`, if `f_p > f_s` fails,
if the certificate is emitted at a class above `ENGINEERING_CANDIDATE`, or if
either refusal stops raising.

## Acceptance checklist
- [x] focused tests pass
- [x] receipt written
- [x] claim classes recorded
- [x] no private files read
- [x] PHYSICAL_VALIDATION_NOT_CLAIMED
