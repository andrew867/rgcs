# E02 — Compression-node electrode pulse programme

Coverage: **E005–E007, F004–F006, F024–F026**.
Status: **`PROTOCOL_READY_HARDWARE_REQUIRED`** — not performed.
Preregistration: `PREREG-E02`. Safety: ≤24 V, ≤0.5 A, battery-isolated.
Implementation: `protocols_v4x.build_protocols()["E02"]`.

## Node position: three estimators, kept separate

The electrode goes at "the compression node" — but which one?

| Estimator | Source |
|---|---|
| Measured node | FEM modal analysis of the as-built geometry |
| Metric centre | geometric midpoint |
| Geometry estimator | the source's own construction |

These **disagree**, and the disagreement is data. The protocol tests
all three positions rather than picking one and calling it *the* node.
The Eye programme's whole lesson applies here: node position carries an
uncertainty, and a claim that ignores it is not a claim.

## Drive matrix

- Frequencies: 19.8 / 20 / 21 Hz; 40 / 40.96 / 41 / 42 Hz.
- Node excitation: 1496 / 587 / 644 Hz.
- Pulse: width, mark-space, polarity, rise/fall, phase, burst length.
- Timing candidates: 46 ms, 60π/4096, 192 cycles, φ⁸ (dimensionless —
  **not** a time; see [TIMING_FAMILY_AUDIT.md](../TIMING_FAMILY_AUDIT.md)),
  552 ms, 2260.992, 1507.328.

## Electrodes

Silver, copper, removable foil, conductive paint, capacitive
non-contact. End-to-end and facet-pair configurations. Coverage and
mass loading are modelled (`bvd.electrode_loading`) because both pull
the frequency by ordinary means.

## Channels

Current, voltage, charge, capacitance, temperature, acoustic pickup,
magnetic field.

## Controls

Open, short, dummy glass, resistor, **no-crystal**, reversed polarity,
**shifted-node** (deliberately wrong position). The shifted-node
control is the key one: if the response is the same 5 mm off the node,
the node is not what is responding.

## Boundaries

- **No mains-connected body contact.**
- **No therapeutic or EEG-entrainment claim.** 40 Hz here is a drive
  frequency for a crystal, and nothing else.
- Do not call an electrode response a new field until the ordinary
  piezoelectric and capacitive channels are bounded — that bound is
  the C07 artifact budget, and it must be computed first.

## Blocker

Hardware: isolated pulse driver, current probe, electrometer, LCR.
Nothing procured. Human-only action.
