# Research Brief: Engineered Annular Surface Waves under Phase-Gated
# Space-Time Modulation

Status: internal draft, publication HOLD. No claim of anomalous
propulsion, gravity modification, or free energy is made or implied.

## Summary

We have built and verified an open analytic and computational toolkit
for a patterned dielectric-loaded annular structure driven by
phase-gated modulation. The toolkit reproduces exact analytic
benchmarks to 1e-14 and produces closed-surface force values with
verified momentum and energy closure.

Applied to the candidate geometry, the model returns **negative
results for the interesting readings** and ordinary explanations for
the rest. We consider publishing that outcome, with the tooling, to be
the useful contribution. The physics questions that remain open --
whether a strongly slow-wave annular surface can be driven into a
sideband-resolved regime, and what the momentum budget looks like
there -- are legitimate and unexplored, but they are questions about a
*different* operating point than the source record describes.

## What is established

- The Maxwell-stress integrator is verified against four exact
  analytic problems (point charge in a uniform field, Coulomb pair,
  source-free region, third-law closure) to 1e-14 or better.
- Two independent formulations of the annular eigenproblem agree to
  4e-7.
- Force is invariant to 15 significant figures under integration
  surface radius, and exactly zero for symmetric masks.

## What is falsified for the candidate operating point

1. 4096 Hz cannot be the electromagnetic surface-wave carrier at bench
   scale (would require a ~1e5 slow-wave factor).
2. 16 Hz modulation cannot open a space-time nonreciprocal gap on a
   Q <= 49 resonance (needs Q > 3.6e7).
3. Lateral force is an ordinary m=1 asymmetry force, exactly balanced
   by the support reaction.

## What is genuinely open

- Whether a deliberately engineered high-slow-wave-factor annular
  surface can reach the sideband-resolved regime at practical Q.
- Whether the 33/35 occupancy has any advantage over other masks once
  the m=1 amplitude is held constant. Our data say the m=1 amplitude
  is the only thing that matters for net lateral force, which makes
  the specific 33/35 choice uninteresting for force and possibly
  interesting for mode structure.
- The momentum budget of a genuinely modulated (not adiabatic) annular
  resonator, which nobody has computed here.

## Funding tiers

**Tier 0 -- public theory and software (current).** Analytic solvers,
open schemas, synthetic examples, convergence infrastructure, a
literature map, negative results. No hardware, no hardware claim.
Cost: personnel only.

**Tier 1 -- basic RF bench.** VNA or impedance analyzer, signal
generation, low-voltage switching, near-field probes, fabricated
annular boards, dielectric fixtures. Goal: measure the annular
eigenmode spectrum and Q against the derived predictions. This is a
falsification test of the solver, not of any propulsion hypothesis.

**Tier 2 -- precision force and field bench.** Torsion balance,
interferometric displacement, controlled enclosure, thermal and
acoustic instrumentation, calibrated RF power. Goal: place an upper
bound on any unexplained force, with the full artifact control set
(vacuum, sham drive, reversal, locked balance, dielectric removal,
mirroring, blind analysis).

**Tier 3 -- independent replication.** Second laboratory, blinded
geometry files, signed raw data, independent solver and
instrumentation. Only reached if Tier 2 produces something above the
artifact floor.

## Milestones and gates

| Gate | Criterion | Consequence if failed |
|---|---|---|
| G1 | measured eigenmode spectrum within 5% of derived | solver model revised |
| G2 | measured Q within a factor of 2 of the upper bound | loss model revised |
| G3 | force channel noise floor below the artifact floor | bench redesign |
| G4 | any candidate force survives all seven controls | proceed to Tier 3 |
| G5 | independent replication | publish |

A failure at G1-G3 ends the programme at that tier. That is the
intended behaviour, not a setback.

## Risks

- **Primary risk: the effect is not there.** The current simulation
  says so. Tier 1 and 2 are worth doing for the instrument and the
  bound, not for a positive expectation.
- Artifact contamination on any force bench is the dominant technical
  risk; ion wind alone at 1 uA and 1 mm exceeds a 1e-9 N candidate by
  three orders of magnitude.
- Reputational risk from association with propulsion claims. Mitigated
  by publishing negative results first and by the standing nonclaim on
  every artifact.

## Partner profiles

- an RF/microwave group with impedance-surface and metasurface
  experience;
- a precision-measurement group with torsion-balance heritage;
- an independent CEM group able to reproduce results in a commercial
  full-wave package (this repository's rung 10 is internal only).
