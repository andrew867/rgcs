# Adaptation Matrix — RGCS v3 / RSCS 1.0

Agent 02, Task 7 (allow side). For every reusable method, the explicit
**substitution map** from the source's symbols/quantities to RGCS/RSCS
quantities. This is the record that lets an equation be adapted *as
mathematics* without importing its physics (paired 1:1 with
`docs/EXCLUSION_MATRIX.md`). Provenance IDs reference
`references/equation_provenance.yaml`.

Binding rule: a substitution here does not by itself authorize use. The
target RSCS operator must still receive a registry ID, units, a
dimensional check, and a machine test before first use in any document
(orchestrator integration rule; Quality Gates 2 & 5).

## Optics / physics sources (mathematical templates)

| Provenance | Source quantity | → RGCS/RSCS quantity | Substitution / mapping | Dimensional check |
|---|---|---|---|---|
| EP-01-01 | intracavity fields a₁,a₂; decay κ_j; coupling Gph e^{±iΩt} | complex modal amplitudes; damping γ_n (rad/s); coupling K=i·2πg | a_j→modal amplitude; κ_j/2→γ_n; i(Gph/2)→ anti-Hermitian K/2 (frozen QA-D-04 sign) | rate terms rad/s; matrix acts on amplitude vector — consistent |
| EP-01-02 | Rabi split Gph; loss κ; detuning Δ | mode splitting; linewidth Γ_n; offset ε_R | Gph→2×(half-splitting g); κ→Γ; Δ→detuning about resonance | Hz vs rad/s tracked explicitly (2π factor) |
| EP-01-03 | κ_int, κ_ex critical point | RGCS drive/readout coupling budget | κ_int=κ_ex → matched-coupling condition | dimensionless ratio — ok |
| EP-02-01 | k±(ω), q(Ω); n_g,±; Δq_pm | RGCS mode wavevectors; coupling-wave wavevector; group indices; mismatch coordinate | k±→mode wavevectors; q→drive wavevector; (n_g,+−n_g,−)/c→group-delay-difference variable | m⁻¹ throughout; Δq_pm·L dimensionless |
| EP-02-02 | transfer matrix t_a^f(φ_RF); r²+μ²=1; φ_RF | RSCS cascadable transfer operator; drive phase | φ_RF→controllable RGCS coupling phase; r,μ→through/cross amplitudes | unitary (dimensionless) — ok |
| EP-02-03 | t_delay=diag(e^{ik_d L_d}); group-delay diff | RSCS propagation/delay operator; group-delay coordinate τ_g | k_d L_d→accumulated phase; Δτ_g→balancing variable | phase dimensionless; τ_g in s |
| EP-04-01 | χ tensor [[χxx,iχxy],[−iχxy,χyy]] | RSCS anti-symmetric coupling tensor (nonreciprocity indicator) | iχxy→anti-Hermitian off-diagonal coupling | tensor acts E→D; ok as algebraic template |
| EP-04-02 | χxy = χ⁽¹⁾B·e_z + χ⁽³⁾(E×E*)·e_z | coupling = bias + state-dependent term; spin coordinate s∝E×E* | B·e_z→bias; (E×E*)→RGCS drive-state coordinate | each term same units as χ — ok |
| EP-04-03 | T=e^{−4k·Im χ L}; φ=2k·Re χ L | RSCS isolation & nonreciprocal-phase metrics | Im χ→loss coupling; Re χ→phase coupling; L→interaction length | exponent & phase dimensionless — ok |
| EP-05-01 | v = Δp/k velocity class | RSCS selection coordinate over an internal-state population | Δp→detuning; k→wavevector; v→selection coordinate (generalized, need not be a velocity) | m/s if literal; abstracted as a labelled coordinate |
| EP-05-02 | IL=−10log T_f; iso=−10log T_b; g⁽²⁾, R | RSCS IL/isolation (dB) + fidelity/noise figure R | T_f,T_b→RGCS transmissions; g⁽²⁾ ratio→normalized fidelity metric (principle only) | dB from log ratio; R dimensionless |
| EP-06-01 | β_f=β+δβ, β_b=β−δβ | RSCS directional propagation-constant coordinate | δβ→signed directional perturbation | m⁻¹ — ok |
| EP-06-02 | even/odd supermodes E_{e,o} | RSCS parity mode basis | a_{e,o},b_{e,o}→parity amplitudes | normalized (dimensionless) |
| EP-06-03 | L_beat=2π/|β_e−β_o|; swap-on-reversal T | RSCS beating-length coordinate + nonreciprocal cascade | Δβ=β_e−β_o→coupling-strength proxy; L_beat in m | 2π/Δβ → m — ok |
| EP-03-01 | spiral-helix writing trajectory | RGCS spiral geometry (RGCS-M.30-37) + fabrication-path provenance coordinate | trajectory params→spiral pitch a, growth q, height H; write-history→provenance tag | mm geometry — matches frozen notation |
| EP-03-02 | 45° crossed-polarizer Faraday assembly | RSCS documentation reference only | 45° basis→reference geometry (not implemented) | n/a (reference) |

## NHT/HAL source (SRC → candidate HYP only)

| Provenance | Source quantity | → RSCS candidate | Substitution / mapping | Status |
|---|---|---|---|---|
| EP-07-01 | Ψ_i(r,t)=A cos(k_i·r−ωt+φ); frame {k_i} | RSCS `memory` space-to-phase candidate coordinate | spatial position→carrier phase φ; {k_i}→oriented basis | **HYP**, needs observable + failure condition before use |
| EP-07-02 | ring-attractor lattice of phase states | RSCS `memory` lattice-occupancy candidate | orientation×carrier-phase→lattice index | **HYP** (Agent 04) |
| EP-08-01 | scale + rotation frame transforms | RSCS `transforms` reference (scale-rotation, cf. RGCS-M.32) | scale, rotation→composable transform params | reference/documentation |

Any substitution not listed here is **unauthorized**. New adaptations must
be added to this matrix (and its exclusion counterpart) before use.
