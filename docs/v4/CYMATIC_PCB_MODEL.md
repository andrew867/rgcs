# Cymatic PCB disk model (Agent G02)

Coverage: **S012–S024**. Gates: **G18, G19**.
Status: `REDUCED_ORDER_VALIDATED` (plate physics) /
`ENGINEERING_PROTOTYPE` (patterns, exports).
Implementation: [`rscs2_core/cymatic_disk.py`](../../rscs2_core/cymatic_disk.py).

## Plate physics (validated)

Clamped circular plate eigenvalues from the exact characteristic
equation `J_n(λ) I_n′(λ) − I_n(λ) J_n′(λ) = 0`, solved by Brent's
method. λ₀₁ ≈ 3.1962 — matches the standard tabulated value, which is
the check that the root finder is solving the right equation.

    f_nm = (λ_nm² / (2 pi R²)) sqrt(D / (rho h))

`composite_plate()` builds the FR4 + copper stack: copper adds both
mass and stiffness, and both are carried (adding only the mass would
push every frequency down and look like a "detuning").

## The three resonances are separated (G19)

This is the load-bearing distinction of G02, and the reason the module
exists rather than a picture of a spiral:

| Resonance | Governed by | Typical band |
|---|---|---|
| **Structural plate mode** | D, ρ, h, R | ~kHz |
| **Electrical self-resonance** | L(spiral) and C(disk) | ~MHz |
| **Visual cymatic pattern** | the driven mode shape | not a resonance at all |

`resonance_separation_report()` computes the first two and reports
their ratio. They are typically **three orders of magnitude apart**.
Conflating them — treating the etched pattern's "frequency" as one
number — is the central error this module refuses to make.

The etched pattern has **no unique mystical frequency**. The disk has
many structural modes and a separate electrical self-resonance, and
which one you excite depends on how you drive it.

## Inductance and capacitance

- `spiral_inductance_h()` — Mohan's modified-Wheeler expression for a
  planar spiral (EST, standard).
- `disk_capacitance_f()` — parallel-plate estimate over the substrate.
- `electrical_resonance_hz()` — 1/(2π√(LC)).

## Chladni patterns

`chladni_pattern()` generates the nodal contours **from the actual
computed plate mode**, not from a decorative drawing:

    W(r,θ) = [J_n(λr/R) − (J_n(λ)/I_n(λ)) I_n(λr/R)] cos(nθ)

The pattern is a consequence of the plate physics. It is not an input.

## Controls (S016–S021)

`control_set()` supplies plain disk, simple cone, flat log spiral,
Archimedean spiral, mass-matched blank, and material controls. A claim
about the spiral pattern must beat the **mass-matched blank** and the
**randomized trace** — otherwise it is a claim about having etched
copper onto a plate.

## Fabrication (G18)

`gerber_spiral_text()`, `drill_text()`, `bom()` — deterministic text
generation. Validity evidence and DRC status:
[FABRICATION_CONTRACT.md](FABRICATION_CONTRACT.md).

## Design for target

`design_for_target()` solves for the disk radius that places f₀₁ at a
selected kHz band. It returns a **design**, not a measurement, and no
disk has been fabricated.

## Boundaries

- No unique-frequency claim for a pattern.
- No claim that a visual cymatic figure indicates a special physical
  state; it indicates which mode is being driven.
- Structural, electrical, and visual are reported separately, always.
