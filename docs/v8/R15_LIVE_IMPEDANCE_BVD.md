# R15 P28 — Live Impedance and BVD Fitting

Incrementally updates a Butterworth-Van-Dyke fit (f_s, f_p, Q, R, L, C, C0) as impedance samples stream in, with a running uncertainty, outlier rejection (Hampel), and a convergence gate. An unconverged fit is refused as a result. A live fit on synthetic data is a SYNTHETIC_OBSERVATION, never a measured crystal; a real analyzer stream is BLOCKED.

- **Module:** `r15/live_bvd.py`
- **Tests:** `tests/v8/test_live_bvd.py`
- **Claim cap:** nothing measured; `PHYSICAL_VALIDATION_NOT_CLAIMED`.
