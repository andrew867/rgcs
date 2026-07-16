# V4 Dynamic Boundary and Symmetry Models (Agent M6)

`rscs2_core/dynamic_boundary.py`. CLASSICAL throughout; the F5 rails
(no photon-creation wording, tunnelling INTERFACE_ONLY, continuum
sweeps ground no tunnelling claims) are enforced in outputs and tests.

- Typed BoundarySchedule (mechanical/electrical/optical x
  sudden/ramp/sinusoid/event) with validation and a dimensionless
  switching-rate measure (modal period / switch duration) (F1).
- Modal projection: M-weighted mixing matrix between before/after
  bases; identity for no change; weak-spring (adiabatic proxy) mixing
  <5% off-diagonal vs strong-spring sudden mixing >5x larger; state
  projection bounded by completeness; degenerate pairs handled via
  rotation-invariant SUBSPACE overlap (=1.0 under arbitrary pair
  rotation while individual overlaps are basis-arbitrary) (F2).
- Work-energy ledger on the analytic oscillator x'' = -w(t)^2 x:
  closure |dE - W_boundary| < 1e-3 rel for both regimes; sudden switch
  at max displacement reproduces E2/E1 = (w2/w1)^2 exactly; slow ramp
  conserves the adiabatic invariant E/w within 2% (F3).
- Symmetry lowering: geometric section asymmetry splits the bending
  pair monotonically and ~linearly in eps; participation ratio
  bounded; mode continuation correlated across the sweep (F4).
- tunnelling_interface_record: INTERFACE_ONLY schema hook (F5).
