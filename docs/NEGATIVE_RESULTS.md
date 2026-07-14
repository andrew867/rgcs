# Negative Results Register — RGCS v3 / RSCS 1.0

Append-only record of things that did NOT work, failed reproductions,
null results, and dead ends. Nothing here is deleted or softened
(Quality Gate 12).

| ID | Date | What was attempted | Result | Consequence |
|---|---|---|---|---|
| NR3-001 | 2026-07-14 | Byte-identical regeneration of golden CSV `case_e_coupled_oscillators.csv` on Windows/Py3.13/numpy 2.5.1 | Failed: one low-order digit differs from the Linux/numpy 2.4.4 checked-in copy | v3 policy: new determinism tests use tolerance-aware comparison with a pinned-environment byte-equality tier (MIG-TEST-02). |
| NR3-002 | 2026-07-14 | v2 reproducibility-bundle round-trip (`export_bundle`→`verify_bundle`) on Windows | Failed: KeyError from backslash arcnames (V2-WIN-01) | Windows portability work item MIG-CODE-07; v2 Linux-only claim stands. |
