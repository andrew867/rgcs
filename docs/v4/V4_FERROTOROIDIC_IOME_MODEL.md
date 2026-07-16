# V4 Ferrotoroidic IOME Model (Agent M11)

`rscs2_core/refmodels/iome_linipo4.py` (EQ-001/002/003; material
reference.linipo4; primary SRC-V4-01 Toyoda et al., Nature Materials
2026, 10.1038/s41563-026-02608-4 — METADATA-ONLY locally, so every
envelope carries SOURCE_VALUE_COMPARISON_PENDING_LOCAL_SOURCE and the
registered presets come from the pack: transition ~20.8 K, d-d bands
1300/1400/1670 nm, pump/probe 1700/1450 nm).

Validated behavior (9 tests, gates H1-H5): toroidal moment P- and
T-odd, PT-even; two time-reversed domains; populations always
normalize; k-reversal and T-reversal flip the writing sign EXACTLY;
IOME alignment is polarization-INVARIANT while the inverse-Faraday
comparator responds only to helicity and the MnF2-style thermal
comparator only to polarization angle (the channel-ablation triad);
lambda=0 / mixed-domain / off-resonance nulls; directional complex
index with Re/Im serialized separately (the Re channel is a registered
PREDICTION partner, not observed data) and the optical-diode Im-sign
reversal under k-flip; three bounded saturation laws compared by
HELD-OUT residual (never aesthetics); nonvolatile retention below the
transition, thermal erasure above; scanned-beam spatial writing with
sign-cancelling overlap; alpha quartz NOT_APPLICABLE.

# V4 Nonlinear Spin Trajectory + Phonon-Controlled Exchange (M12)

`rscs2_core/refmodels/nonlinear_spin.py` (EQ-006/007; materials
reference.nonlinear_afm [SRC-V4-03 Schlauderer, Nature 569] and
reference.phonon_exchange [SRC-V4-04 Afanasiev, Nat. Mater. 2021]).

A: multi-minimum W(phi), RK4 deterministic; equilibrium/small-
oscillation nulls; bisected switching threshold (bracket ~2e-5);
~pi phase slip just above threshold; damped settling; strong overdrive
reported honestly as multi-well k*pi slips; Faraday projection
sin(phi); declared FIR waveform transfer.
B: driven phonon envelope modulates J(Q); Q=0 and off-resonance
nulls; c1 sign sets red/blue shift; transient chirp; the mechanism
CLASSIFIER (gate H7) labels persistent-gap two-branch data
direct_hybridization and envelope-tracking single-branch data
indirect_parameter_modulation — the exchange model itself classifies
as INDIRECT (never mislabeled an avoided crossing).
