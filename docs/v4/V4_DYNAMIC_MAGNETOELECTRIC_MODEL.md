# V4 Dynamic Magnetoelectric Model (Agent M5)

`rscs2_core/refmodels/dynamic_me.py` (RGCS-V4-EQ-011): complex
Lorentz-form tensor alpha_ij(w) = a_ij w0^2/(w0^2 - w^2 - i w gamma),
SI units s/m (P [C/m^2] per H [A/m]), declared coordinate frame,
symmetry mask (forbidden components raise), reciprocity as DECLARED
metadata (never inferred from tensor shape), handedness reversal.

Validated limits (8 tests, gate E4): zero tensor/drive nulls; resonant
amplitude peak with quadrature phase and DC in-phase limit;
off-resonance decay; handedness sign flip; Kramers-Kronig consistency
of the Lorentz form (<5% Hilbert residual on broad coverage) with an
INSUFFICIENT_SPECTRAL_SUPPORT / INTERFACE_ONLY refusal on sparse grids
(no invented dispersion); optical rotation (dispersive) vs ellipticity
(absorptive) channels kept separate and crossing over at resonance;
alpha quartz -> typed NOT_APPLICABLE (E5). Amplitude and quadrature
are never collapsed into an unsigned score.

Materials: reference.dynamic_magnetoelectric (SRC-V4-12 topic) and
reference.linipo4 (SRC-V4-01) both pass the capability gate;
electromagnon/chiral-multiferroic hooks consume the same METensor.
