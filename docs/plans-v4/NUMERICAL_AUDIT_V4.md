# Numerical Audit — RGCS v4 core solver

Independent re-derivations (`tools/qa_audit_v4.py`), not test reruns.

| item | method | result |
|---|---|---|
| K symmetry (iso + aniso) | max\|K−Kᵀ\|/max\|K\| | < 1e-12 both |
| M symmetry + positivity | same + diagonal min | symmetric, positive |
| Mass scale (V4-D-001 guard) | uᵀMu on unit-x field vs ρV | rel err < 1e-9 |
| Stiffness nullspace | rigid-translation K-energy | < 1e-12 relative |
| Rigid modes (free aniso body) | solve, count f < 1 Hz | exactly 6 |
| Eigenpair residuals | ‖Ku−ω²Mu‖/‖ω²Mu‖ | max < 1e-6 |
| Orthogonality | max off-diagonal of ΦᵀMΦ−I | < 1e-8 |
| Units end-to-end | thick cantilever f₁ vs EB closed form | within thick-beam envelope (documented Timoshenko deviation) |
| Mesh convergence | 3-level crystal f₁ (bundle mesh_convergence.csv) | monotone, sub-0.1% between medium and fine |
| Boundary conditions | fixed/free/Robin limits (RSCS2-B.1..B.4 tests) + cradle variant in eye run | green |
| Determinism | two identical solves, exact array equality | bit-identical after V4-D-003 fix (was: ~1e-10 ARPACK jitter, registered + fixed) |

Solver-validation anchors (registered tolerances): cantilever EB
converged < 0.5% (G4); thick-beam z-bend +0.03% vs Timoshenko; static
tip deflection vs FL³/3EI (G5, bundle static_deflection.csv); exact
cube Lamé mode +0.03–0.05%, ν-independent (V.5); constrained-bar
P-wave ladder vs frozen Z-speed (V.6, rtol 1e-3).

Conclusion: the CPU float64 path holds its registered tolerances and
is fit to remain the numerical authority (DV4-004, G3).
