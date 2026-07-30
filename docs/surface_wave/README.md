# RGCS Surface-Wave Research Package (R10.15)

Publication status: HOLD. No tag, no push, no release.

## What is being modeled

A **candidate** device architecture, treated as a research model and
nothing more: a conducting annulus whose surface is patterned into 35
angular cells (33 active, 2 omitted), loaded by a dielectric slab, and
driven by a phase-gated, time-modulated excitation.

The package computes:

- exact angular mask spectra for any active/omitted cell set;
- temporal switching spectra for seven declared waveforms;
- a declared surface-impedance dispersion model and unit-cell
  eigenproblem;
- annular eigenmodes of a dielectric-loaded parallel-plate region;
- Floquet sidebands and forward/reverse nonreciprocity;
- Maxwell-stress force and torque on **closed** surfaces;
- momentum and energy ledgers;
- ordinary-artifact estimates for bench work.

## Which parts are established electromagnetism

Established (cited, not derived here): the Maxwell stress tensor and
its closed-surface integral; Bessel-function solutions of the annular
Helmholtz problem; the inductive-impedance-surface bound TM branch
(Sievenpiper 1999; Pozar); the groove effective-medium reactance
(Pendry, Martin-Moreno, Garcia-Vidal, Science 305, 847, 2004); Peek's
corona law; ion-wind thrust `F = I d / mu`.

Everything the solvers produce is labelled `DERIVED` (exact analytic
consequence), `SIMULATED` (numerical output under declared
approximations), `HYPOTHESIS`, `SOURCE_PROVENANCE`, `NULL`, or
`REPLICATION_REQUIRED`. No software path can emit `ESTABLISHED`, and
none can emit a measurement.

## Which geometry and frequencies are candidate inputs

These come from the source record and carry **no physical warrant**.
They are `SOURCE_PROVENANCE` and every study compares them against
controls:

| quantity | candidate value |
|---|---|
| angular cells | 35 (33 active, 2 omitted) |
| inner / outer radius | 82.261610772 / 144.109699835 mm |
| inner-to-outer area ratio | 29/89 |
| master phase and switching reference | 4096 Hz |
| traveling-pattern modulation | 16 Hz |
| passage rates | 560 / 528 / 32 Hz |
| carrier phase states | 125 (2.88 deg, 1.953125 us) |

**The rates above are drive rates, not the electromagnetic carrier.**
The surface-wave carrier `f_SW` is *derived* from the eigenvalue
problem, never assumed.

## What the software can calculate today

```bash
rgcs surface-wave geometry validate            # typed geometry record
rgcs surface-wave mask analyze                 # exact Fourier spectrum
rgcs surface-wave temporal analyze --waveform stepped
rgcs surface-wave eigenmodes solve             # derives f_SW
rgcs surface-wave floquet solve                # sidebands + reversal
rgcs surface-wave stress integrate             # closed-surface force
rgcs surface-wave momentum close               # momentum ledger
rgcs surface-wave energy close                 # energy ledger
rgcs surface-wave artifacts estimate           # ordinary-artifact floor
rgcs surface-wave privacy scan                 # public/private gate
rgcs surface-wave bundle verify DIR            # evidence bundle
```

Add `--format json` to any command for the machine interface. Every
command emits a receipt with input hashes, versions, evidence class,
limitations, and the standing nonclaim.

## What has NOT been measured

Everything. There is no instrument intake in this package and no
measurement path exists. Nothing here has been built or tested on a
bench. Three specific limits are worth stating plainly:

1. **Full-wave 3D transient FDTD is not executed.** A reduced-order
   modal transient is executed and agrees with harmonic balance to
   4e-8, but no result in this release depends on the unexecuted rung.
2. **Radiation Q is not modelled.** The eigenmode model uses closed
   PEC walls, so every reported Q is an **upper bound**.
3. **No coupled structural, thermal, or acoustic solve.** Artifact
   magnitudes are analytic estimates only.

## Principal findings, including the nulls

- **4096 Hz is falsified as the electromagnetic carrier.** For the
  candidate geometry the annulus is 9.7e-6 free-space wavelengths
  around at 4096 Hz. Supporting an m=1 annular resonance there would
  need a slow-wave factor of 1.03e5 and a groove depth of ~18 km. The
  derived lowest eigenmode is ~1.15 GHz. 4096 Hz remains a coherent
  *switching and phase* reference, which is what the source record
  actually describes.
- **The space-time nonreciprocity mechanism does not engage.**
  Resolving 16 Hz sidebands on a 1.15 GHz mode needs Q > 3.6e7; the
  modelled structure gives Q <= 49. Every sideband lies about six
  orders of magnitude inside one linewidth, so forward and reversed
  modulation address the same resonance identically and the computed
  nonreciprocity contrast is exactly zero.
- **Lateral force is an ordinary asymmetry force.** It tracks the
  mask's m=1 Fourier amplitude with correlation 1.000, is exactly zero
  for any rotationally symmetric mask, and closes against the support
  reaction in the momentum ledger. An isolated charge distribution has
  zero self-force (verified to 6e-25 N).
- **An exactly diametric pair of omitted cells is impossible** for an
  odd cell count, so the minimum-asymmetry control is labelled
  `nearest_diametric` and has |M_1| 22x smaller than adjacent gaps.

## How private source records are excluded

The private path-vector capture never enters this tree. The gate uses
structural detection against a git-derived allowlist of everything
already public at the R10.13 baseline commit, plus two aggregate
SHA-256 commitments to the private capture. **No per-wire digest is
stored**: a 9-to-11 digit decimal is brute-forceable, so publishing
per-wire hashes would publish the wires. Run
`rgcs surface-wave privacy scan`; `tests/r1015/test_privacy_boundary.py`
fails the build on any leak.

## How another researcher reproduces a result

```bash
python -m pip install -e ".[fem]"
pytest tests/r1015 -q
rgcs surface-wave eigenmodes solve --format json --output modes.json
rgcs surface-wave bundle verify evidence/r1015/
```

Every number in this README is produced by those commands. The
manufactured-solution suite (`rgcs_surface_wave.manufactured`) verifies
the stress integrator against exact analytic answers to 1e-14 before
any device result is computed.

## What would falsify the hypothesis

The hypothesis under test is that the 33/35 patterned annulus with
phase-gated modulation produces a net force that is not accounted for
by ordinary reactions. It is falsified, and currently **is** falsified
in simulation, by any of:

- momentum closing to tolerance once every body is included (it does);
- lateral force scaling with the m=1 mask amplitude and vanishing for
  symmetric masks (it does);
- sidebands lying inside a single resonance linewidth (they do);
- a candidate force below the ordinary-artifact floor (it is);
- forward and reversed modulation giving identical results (they do).

A bench result would additionally have to survive: hard vacuum, a
sham drive at matched dissipated power, drive and polarity reversal,
a locked balance, dielectric removal, geometry mirroring, and blind
analysis. Note that polarity reversal does **not** discriminate a
Maxwell-stress signal from electrostatic attraction: both are
quadratic in the field.
