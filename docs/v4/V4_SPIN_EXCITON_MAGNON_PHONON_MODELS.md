# V4 Spin / Exciton / Magnon / Phonon Reference Models (Agent M4)

All REDUCED_ORDER_VALIDATED reference systems, capability-gated, never
alpha-quartz mechanisms (quartz requests return typed NOT_APPLICABLE —
tested). No microscopic (DFT/BSE/ab-initio) content anywhere.

## Exciton-magnon modulation (`refmodels/exciton_magnon.py`, EQ-004)

E_x(t) = E0 + A·cos²(θ(t)/2), θ driven by a damped magnon coordinate.
Validated limits: zero modulation → constant; second-order small-angle
expansion (O(x³) remainder verified); Jacobi-Anger sideband amplitudes
(odd harmonics ∝ sin θ0 — vanish at θ0=0 where the second harmonic
leads, tested); damping → linewidth broadening (>2× at the fixture).
Material: reference.exciton_magnon (topic source SRC-V4-06;
paper-value comparison pending local source, DV4C-003).

## Avoided crossing (`refmodels/avoided_crossing.py`, EQ-005)

Two/N-mode complex-pole solver: lossless two-mode case reproduces the
FROZEN v3 `coupled_two_mode` to 1e-12 (conservative-extension anchor);
on-resonance splitting exactly 2g; hybrid linewidths average bare ones
on resonance; participation → pure modes at large detuning; splitting
never below 2g; first-order uncertainty propagation (∂S/∂g = 2 on
resonance, verified). Linewidths are explicit complex poles — never
hidden in real eigenfrequencies.

## Block Hamiltonian (`refmodels/block_hamiltonian.py`)

Typed magnon/exciton/phonon/spin blocks; adding a block itself passes
the M2 coupling-graph capability gate (quartz cannot even construct a
magnon block — tested); Hermitian variant has real eigenvalues;
dissipative variant enforces pole stability (growing poles raise);
`export_interface()` is INTERFACE_ONLY for future microscopic solvers.

## Mechanically dressed spin (`refmodels/dressed_spin.py`)

Classical Bloch reduced model, seeded OU dephasing noise. Dressing
(Ω ≫ σ_δ) extends the coherence proxy vs the undriven case only in
the declared regime; bit-deterministic under a fixed seed. Explicit
exclusion carried in every envelope: NOT a claim of a spin qubit in
the macroscopic quartz specimen.

Chiral-phonon Zeeman integration lives in `chiral_phonon.py` (M3) and
is consumed here unchanged (field/phase reversal signs tested there).
