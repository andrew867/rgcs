# Optical / Nonreciprocal Reference-Mechanism Comparison

**GENERATED FILE — do not edit.** Regenerate with
`python tools/generate_optical_comparison.py`. Source of truth:
`references/source_registry.yaml` + `references/equation_provenance.yaml`
(frozen, Agent 02). Compiled by Agent 06.

Every mechanism below achieves nonreciprocity or mode conversion via
an ACTIVE ingredient (bias field, drive, nonlinearity, magneto-optic
material) that alpha-quartz is **not** claimed to have. The
`forbidden transfer` column is binding (EXCLUSION_MATRIX): only the
`reusable math` crosses into RSCS, always re-derived and re-tested.
The pre-registered null for quartz directional tests is NO asymmetry
(DECISION_LOG D6-003).

## SRC-3-01 — Electrically driven linear optical isolation through phonon mediated Autler-Townes splitting

| EP id | Mechanism / equation | Reusable math (adapted) | Forbidden transfer (binding) | RSCS home |
|---|---|---|---|---|
| EP-01-01 | Two-mode coupled equations of motion (WGR + waveguide), driven | driven two-mode complex dynamics with anti-Hermitian off-diagonal coupling and modal decay k_j; time-dependent (parametric) coupling e^{±iΩt} | no claim that quartz hosts acousto-optic ATS, WGR modes, or the reported 39 dB isolation; device numbers stay with the paper | RSCS coupling operator (two-mode); consistency-tested against rgcs_core.coupled_modes (RGCS-M.23-24,46) |
| EP-01-02 | Autler-Townes dressed-state splitting of the cavity susceptibility | two-Lorentzian split response; strong-coupling threshold Gph >> κ (main text: Gph > sqrt(κ1κ2)); \|split\| = Gph (Rabi frequency) | the physical splitting is optical; not evidence for a quartz acoustic ATS effect | RSCS observation-layer lineshape; ties to RGCS-M.24/M.27 |
| EP-01-03 | Critical-coupling transmission zero | critical-coupling condition (intrinsic loss = external coupling); insertion-loss/isolation contrast metric | device insertion-loss/contrast values are the paper's | RSCS observation: coupling/insertion-loss metric |

## SRC-3-02 — A Terahertz Bandwidth Nonmagnetic Isolator

| EP id | Mechanism / equation | Reusable math (adapted) | Forbidden transfer (binding) | RSCS home |
|---|---|---|---|---|
| EP-02-01 | Acousto-optic phase-matching condition and phase mismatch | momentum/phase matching between two modes via a coupling wave of wavevector q; mismatch linear in detuning through group-index difference; response ∝ sinc^2(Δq_pm La/2) | no claim quartz realizes THz-bandwidth optical isolation or CMOS-photonic beam splitters | RSCS coupling/propagation: phase-matching predicate + mismatch coordinate |
| EP-02-02 | AOM-section transfer matrix (parity basis) | unitary 2x2 transfer matrix; RF phase φ_RF as a controllable coupling phase; conserved r^2+μ^2=1 | acoustic field b, group velocities v±, and device geometry stay optical-domain | RSCS transforms: cascadable transfer-matrix operator; parity basis in RSCS modes |
| EP-02-03 | Delay-region matrix and forward/backward interference (group-delay balancing) | cascaded transfer matrices; group-delay/dispersion balancing to widen the reciprocity-breaking bandwidth; direction dependence via RF phase ordering | no import of nonreciprocity/isolation as an intrinsic quartz property | RSCS propagation: group-delay coordinate + nonreciprocal cascade operator |

## SRC-3-03 — Integrated Magnetless Passive Broadband Faraday Isolator

| EP id | Mechanism / equation | Reusable math (adapted) | Forbidden transfer (binding) | RSCS home |
|---|---|---|---|---|
| EP-03-01 | Alternating spiral-helix filament laser-writing path | parameterization of a spiral-helix writing trajectory; fabrication path-history as a state variable affecting the written structure | latched-magnetization / Faraday-rotation physics is BIG-specific; NOT a quartz effect. Preprint (not peer-reviewed) -- SRC weight. | RSCS provenance/state_preparation: fabrication-path coordinate; feeds rgcs_core.geometry.spiral |
| EP-03-02 | Crossed-polarizer Faraday isolator assembly (45-degree offset) | 45-degree polarization-basis geometry; figure-of-merit (deg/dB) bookkeeping | no quartz Faraday rotation claim; figures of merit are the paper's | RSCS: comparison reference (documentation), not an implemented operator |

## SRC-3-04 — Self-induced optical non-reciprocity

| EP id | Mechanism / equation | Reusable math (adapted) | Forbidden transfer (binding) | RSCS home |
|---|---|---|---|---|
| EP-04-01 | Anti-symmetric (gyrotropic) susceptibility tensor | anti-symmetric off-diagonal coupling tensor as the algebraic signature of nonreciprocity/time-reversal breaking | the medium is atomic vapor; no claim quartz has a self-induced χxy | RSCS coupling: nonreciprocity (anti-symmetric coupling) predicate |
| EP-04-02 | Nonlinear (signal-induced) non-reciprocal susceptibility expansion | expansion of a coupling coefficient in a bias term plus a state-dependent (self-induced) term proportional to field spin E×E* | no import of the physical claim that a signal self-induces nonreciprocity in quartz | RSCS state_preparation + coupling: state-dependent coupling coordinate |
| EP-04-03 | Nonreciprocal transmittance, phase, and isolation | Beer-law isolation from Im(coupling); reciprocity-breaking phase from Re(coupling); both linear in interaction length L | atomic-vapor performance stays the paper's | RSCS observation: isolation + nonreciprocal-phase metrics |

## SRC-3-05 — Noiseless single-photon isolator at room temperature

| EP id | Mechanism / equation | Reusable math (adapted) | Forbidden transfer (binding) | RSCS home |
|---|---|---|---|---|
| EP-05-01 | Velocity-selective optical pumping (Doppler) coordinate | internal-state population indexed by a velocity/detuning class coordinate v = Δp/k; direction selectivity via which class is addressed | no claim quartz has Doppler-selected atomic populations; single-photon/quantum regime not imported | RSCS state_preparation + modes: population-over-selection-coordinate |
| EP-05-02 | Insertion loss / isolation and single-photon fidelity metrics | log-ratio insertion-loss/isolation definitions; correlation-based signal-fidelity/noise measurement principle | g^(2) single-photon statistics are quantum-optical; not claimed for classical quartz acoustics | RSCS observation: isolation + fidelity/noise metrics |

## SRC-3-06 — Integrated TE optical isolator based on magneto-optical perturbation in coupled waveguides

| EP id | Mechanism / equation | Reusable math (adapted) | Forbidden transfer (binding) | RSCS home |
|---|---|---|---|---|
| EP-06-01 | Nonreciprocal propagation-constant shift (TMOKE) | direction-dependent propagation constant via a signed perturbation δβ; 2δβ nonreciprocal split | the perturbation is magneto-optic (Kerr); no quartz analogue asserted | RSCS propagation: directional propagation-constant coordinate |
| EP-06-02 | Even/odd supermode decomposition of a coupled system | supermode (even/odd parity) basis for two coupled modes; amplitudes as normalized column vectors | waveguide-specific field profiles are the paper's | RSCS modes: parity supermode basis |
| EP-06-03 | Modal beating length and transfer-matrix cascade | beating length from supermode propagation-constant difference; nonreciprocity from row/column swap of the transfer matrix under reversal | device isolation performance is the paper's | RSCS transforms/propagation: beating-length coordinate + nonreciprocal cascade |

## Cross-mechanism summary

| Ingredient that breaks reciprocity | Which sources | Quartz status |
|---|---|---|
| Travelling acoustic drive (phase-matched, momentum-biased) | SRC-3-01, SRC-3-02 | possible to APPLY externally; effect size must be computed, not imported (RSCS-O.19) |
| Signal-induced chi(3) spin term | SRC-3-04 | not claimed for quartz; modelled as the s_z term of RSCS-O.22 with null default |
| Doppler-selected atomic population | SRC-3-05 | no quartz analogue; abstracted to the selection coordinate RSCS-C.10 only |
| Magneto-optic bias (TMOKE / latched garnet) | SRC-3-03, SRC-3-06 | quartz is not magneto-optic; delta_beta of RSCS-C.17 defaults to 0 |

A passive, lossless, unbiased quartz path is reciprocal. Any measured asymmetry is HYP (claims H-21/H-23) until it survives the reversal battery.
