# Piezoelectric Audit (Agent 13 Role B)

| item | method | result |
|---|---|---|
| Uncoupled limit (G8) | e=0 piezo solve vs pure elastic, same mesh | rel < 1e-9 (audit re-derivation) |
| Energy patch | single-element analytic energy 1/2 SᵀCS − SᵀeᵀE... vs assembled blocks | 1e-9 (pins tensor order + signs) |
| Reciprocity/symmetry | saddle block [[Kuu,Kup],[Kupᵀ,−Kpp]] uses one Kup for both couplings; Kuu/Kpp symmetric | structural + audit symmetry check |
| Short vs open (G9) | f_open ≥ f_short; k_eff² = (fo²−fs²)/fo² physical order on X-cut extensional | green (tests) |
| Electrode reversal | +V/−V swap flips displacement sign exactly | green (tests) |
| Zero drive | V=0 → zero response | green (tests) |
| Gauge handling | open circuit grounds exactly one DoF; grad(φ) gauge-independent | enforced (raises without gauge) |
| Convergence | coupled modes converge with refinement; frame invariance under rotation | green (tests) |
| Static saddle solve | live D5 field in the proof bundle from a real 10 V solve | present (fields/electric/) |

Conventions: stress-charge form σ = C:S − eᵀE, D = e:S + εE
(IEEE 176); Bechmann 1958 constants. No accuracy claim beyond
supplied tensors/BCs (registered exclusion).

No defects found.
