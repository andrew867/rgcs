# R15 P29 — Real-Time Mode Tracker

Follows a resonant mode's frequency as a control parameter varies, keeping a bounded-window peak lock and staying on the correct adiabatic branch through an avoided crossing (minimum gap 2|g|, from r13.avoided). A branch hop is a tracking error, not a new mode; a lock loss is an instrument condition, not a signal. The trajectory is a SYNTHETIC_OBSERVATION.

- **Module:** `r15/mode_tracker.py`
- **Tests:** `tests/v8/test_mode_tracker.py`
- **Claim cap:** nothing measured; `PHYSICAL_VALIDATION_NOT_CLAIMED`.
