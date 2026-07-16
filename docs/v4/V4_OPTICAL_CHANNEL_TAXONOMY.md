# V4 Optical Channel Taxonomy and Ablation Suite (Agent M14)

`rscs2_core/optics_channels.py`. Sixteen registered channels
(propagation, ħk, Jones, helicity, polarization angle, SAM, OAM index,
intensity, intensity gradient, E/B waveforms, phase, group delay,
spectrum, beam geometry, envelope). Derived channels (ħk, helicity,
polarization angle, SAM) are computed from the primitive fields and
cannot be ablated independently of them (attempting to raises).

## Mechanical channel isolation

A response model DECLARES its consumed channels
(`ResponseDeclaration.consumes`); `respond()` passes ONLY those values
— undeclared channels cannot leak in by construction (a spy-function
test proves the mechanism sees exactly its declaration).

## Registered comparator mechanisms and their channels

| mechanism | consumes | ablation signature (tested) |
|---|---|---|
| iome_linipo4 | propagation, intensity | flips under k-reversal; blind to polarization/helicity/OAM |
| inverse_faraday | helicity, intensity | signed by helicity; blind to direction |
| inverse_cotton_mouton | polarization angle, intensity | responds to polarization rotation at fixed direction |
| mnf2_annealing | polarization angle, intensity | polarization-angle-dependent heating; helicity-blind |
| photothermal | intensity | linear in intensity only |
| vortex_diagnostic | OAM index, phase | responds only to charge |

`ablation_matrix()` runs every mechanism × every single-channel
variation and reports response changes — the automated
channel-discrimination table (selectivity tested).

## Hidden-order diagnostics + identity prohibition

`hidden_order_report()` assembles the typed family (toroidal moment
with P/T/PT, AFM order parameter, populations, walls, directional
Re/Im index contrast, NDD, retained bias, spatial resolution,
penetration uniformity) on the M11 model. `compare_patterns()` permits
spatial correlation but embeds `physical_identity: False`; asserting
identity between distinct registered quantities raises (M3 registry) —
toroidal order ≠ mechanical vortex ≠ optical vortex ≠ quartz eye.

# V4 Eye Consensus Expansion (Agent M9, corrected)

`rscs2_core/eye_votes.py` + the V4C-D-001-corrected field engine.
Fourteen catalogue votes each carrying applicability from the M2
record; optical votes additionally require an actually SOLVED optical
field (else INTERFACE_ONLY). NOT_APPLICABLE/INTERFACE_ONLY votes are
never counted as positive evidence AND their absence never counts
against an anomaly. The vote layer can downgrade (to
INSUFFICIENT_RESOLUTION) but can never upgrade toward a stable
verdict. Node coincidence is uncertainty-aware
(`docs/v4/EYE_NODE_COINCIDENCE_CORRECTION.md`); the binding scope
statement is `docs/v4/WHAT_THIS_QUARTZ_MODEL_DOES_NOT_INCLUDE.md`.
