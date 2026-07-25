# R15 P27 — Automated Sweep Controller

Orchestrates a parameter sweep (frequency, drive, temperature, orientation) across measurement lanes driving a frozen protocol, with pre-declared adaptive refinement, settling dwell, and safety bounds. The plan is hash-sealed before it runs; every point (including failed / settling / safety-aborted) is recorded — none dropped. A real sweep is PREREGISTERED_NOT_RUN.

- **Module:** `r15/sweeps.py`
- **Tests:** `tests/v8/test_sweeps.py`
- **Claim cap:** nothing measured; `PHYSICAL_VALIDATION_NOT_CLAIMED`.
