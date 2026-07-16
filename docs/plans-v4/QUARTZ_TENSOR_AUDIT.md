# Quartz Tensor Audit (Agent 13 Role B)

Scope: stiffness/piezo/dielectric tensor plumbing between the frozen
v3 constants and the v4 solvers. Independent re-derivations in
`tools/qa_audit_v4.py` unless noted.

| item | method | result |
|---|---|---|
| Voigt→full ordering | all minor+major symmetries; C11 at [0,0,0,0]; C44 at [1,2,1,2] | exact |
| Trigonal class-32 symmetry | 120° Z rotation leaves C invariant | atol 1e-3·max\|C\| (float roundtrip) |
| Frame invariance (Bond) | random ZXZ rotation: Christoffel eigenvalue sets invariant under co-rotated directions | rel < 1e-9 |
| Frozen speed anchors | X/Y/Z quasi-longitudinal vs frozen `rgcs_core.anisotropy.wave_speeds` (5718.734781 / 5992.675993 / 6329.927000 m/s) | rel < 1e-9 each |
| 180° X invariance | class-32 second diad (tested in test_rscs2_quartz) | green |
| Rotation group sanity | R identity/inverse/composition; proper-rotation guard rejects improper matrices | green |
| Piezo constants | e11 = 0.171, e14 = −0.0406 C/m² slots in the rank-3 tensor; symmetry e_ijk = e_ikj | exact |
| Dielectric | ε11/ε0 = 4.428, ε33/ε0 = 4.634; SPD guard | exact / enforced |
| Density | 2648 kg/m³ (frozen, Bechmann) | matches |
| Orientation sweep | Christoffel sweep vs frozen v3 on 200-direction batch (V.6 conservative-extension anchor) | green (Agent 04 evidence) |

Known declared limitation: handbook third-decimal dependence on
reference/wavelength/temperature (D6-002) — declared, not hidden.

No defects. Tensor ordering and rotation conventions are pinned by
tests strong enough to catch index transposition (the single-element
piezo energy patch at 1e-9 pins e-tensor sign AND index order).
