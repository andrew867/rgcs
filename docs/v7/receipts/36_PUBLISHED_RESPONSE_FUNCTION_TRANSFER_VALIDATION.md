# R13 Phase Receipt

```text
phase_id: 36
phase_title: Published Response-Function Transfer Validation
status: COMPLETE
start_commit: 8ae9574
end_commit: v7.0.0 (branch v630-r13)
files_added: r13/response.py, tests/v6/test_r13_response.py
files_modified: none
tests_added: tests/v6/test_r13_response.py (15 tests)
focused_test_result: .venv/Scripts/python.exe -m pytest tests/v6/test_r13_response.py -q -> 15 passed
full_regression_result: 5638 passed, 8 skipped, 1 deselected, exit 0
source_hashes_used: build_meta source hash over SOURCE_ROOTS incl. r13
claim_classes_emitted: ANALYTIC_MODEL
private_files_read: false
```

## Work completed

Demonstrated that the common response interface reproduces textbook,
source-supported cross-domain calculations. `r13/response.py` (tests
`tests/v6/test_r13_response.py`), verdict **`LINEAR_RESPONSE_CORE_IMPLEMENTED`**.
The mechanical / electrical-BVD / optical adapters each build the same
response with their own units.

## Evidence and equations implemented

- **Damped-oscillator Green function** `G(w) = 1/(w0^2 - w^2 - i g w)` peaks at
  resonance with the expected FWHM.
- **Kramers-Kronig consistency** — the real part reconstructed from the
  imaginary part via the Hilbert transform matches the analytic Lorentzian
  real part (the load-bearing identity).
- **S-matrix unitarity** — a lossless beamsplitter satisfies `S_dagger S = I`
  and conserves energy exactly.
- **State-space -> transfer function** matches the single-pole hand case.
- `refuse_cross_domain_without_certificate` and
  `refuse_simulation_as_measurement` raise.

## Negative results

Reproducing a published identity validates the implementation, not a physical
transfer. A shared response function is not a shared mechanism, and none of
this is a measurement. `PHYSICAL_VALIDATION_NOT_CLAIMED`.

## Deviations from prompt

None. The prompt asks to reproduce source-supported cross-domain calculations;
the governance rule is enforced that reproduction validates the code, not a
shared physical mechanism.

## Blocking inputs, when applicable

None. This phase validates code against established identities and requires no
external input. Any claim of a shared physical mechanism remains blocked by
`refuse_cross_domain_without_certificate`.

## Downstream impact

Confirms the common linear-response core (phase 5) that the domain adapters
and coupling certificates rest on, so later phases can rely on the shared
interface being numerically correct without treating it as evidence of
transfer.

## Reopening test

Not a blocked phase. Regression on `tests/v6/test_r13_response.py` re-verifies
the Kramers-Kronig / unitarity / Green-function identities; a failure reopens
the interface.

## Acceptance checklist

- [x] Damped-oscillator Green function peaks with expected FWHM.
- [x] Kramers-Kronig real part reconstructed via Hilbert transform matches
  the analytic Lorentzian.
- [x] Lossless S-matrix unitary and energy-conserving.
- [x] State-space -> transfer function matches single-pole case.
- [x] Cross-domain-without-certificate and simulation-as-measurement refused.
- [x] Focused suite passes (15 passed).
- [x] Claim class `ANALYTIC_MODEL`; no physical validation claimed.
