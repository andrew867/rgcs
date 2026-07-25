# R15 P30 — Laser-Trim Planning Simulator

Plans conservative mass removal (Sauerbrey Delta f = -Cf*Delta m) to tune a resonator to a target frequency, approaching from the safe side without overshoot (ablation is irreversible), within a laser safety envelope and electrode/mount keep-out zones. It is a PLANNING SIMULATOR: no laser is fired and a real trim is BLOCKED_MISSING_INPUT.

- **Module:** `r15/trim_planner.py`
- **Tests:** `tests/v8/test_trim_planner.py`
- **Claim cap:** nothing measured; `PHYSICAL_VALIDATION_NOT_CLAIMED`.
