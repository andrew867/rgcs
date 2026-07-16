# Limitations (declared)

- STEP export not generated (built-in-kernel geometry; OCC path is
  documented/implemented/untested per DV4-013).
- D9/D10 phase diagnostics apply to damped/driven complex responses;
  the canonical consensus run used undamped real modes (the engine's
  declared degenerate case). Machinery validated synthetically.
- The eye consensus covered the first 4 elastic modes at two mesh
  levels, one boundary variant, three material draws. More modes/
  variants are mechanically supported and remain open work.
- Acceleration results are hardware-specific (Iris Xe fp32 2e-4
  parity band; i5 CPU-CL fp64 1e-10 band); CUDA is INTERFACE_TESTED
  only.
- No accuracy claim beyond supplied tensors and BCs; no eye claim at
  all (verdict: conventional/null family).
