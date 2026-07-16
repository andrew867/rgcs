# V4 Adaptive Calibration and Inverse Design (Agent M8)

`rscs2_core/calibration.py` (gates I1-I5, all tested):

- Observation records are frozen dataclasses in an append-only
  HASH-CHAINED ledger (no update/delete API; tampering is detected by
  verify()).
- fit_parameters: deterministic weighted least squares; covariance,
  correlation, condition number; NON-IDENTIFIABILITY is flagged with
  NaN sigmas and an explicit note, never hidden (I2).
- track_drift: windowed re-fits + residual jump alerts; raw ledger
  provably intact (I3).
- inverse_design: deterministic multi-start; DIVERSE candidate set
  (both wells of a symmetric objective found), nonuniqueness report,
  honest infeasibility record for NaN/unbounded objectives.
- guarded_update: optimizers can write ONLY calibration.* keys;
  touching classification/evidence/sources/equations raises
  PolicyViolation (I4).
- rl_control_adapter: disabled by default (raises), simulation-only
  bandit with a fixed-arm baseline, classification ENG; cannot gate
  any core result (I5). Control-architecture precedent only
  (SRC-V4-08) - no QEC physics claims.
