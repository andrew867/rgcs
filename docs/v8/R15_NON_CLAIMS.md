# R15 P34 — Negative Results and Non-Claims

R15 advances no physical claim; every non-claim is enforced by a raising refusal.

- **Module:** `r15/nonclaims.py`
- **Tests:** `tests/v8/test_nonclaims.py`
- **Claim cap:** nothing measured; `PHYSICAL_VALIDATION_NOT_CLAIMED`.

## Negative results

- Every registered non-claim maps to a refusal in r15.claims that raises; there is no PHRYLL_DETECTED state.
- Asserting any registered non-claim is refused.
- The residual ceiling is UNEXPLAINED_INSTRUMENT_RESIDUAL.
