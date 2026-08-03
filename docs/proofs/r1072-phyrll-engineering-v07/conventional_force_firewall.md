# Conventional force firewall (v0.7)

The six-term decomposition any measured force must survive:

```text
F_measured = F_charged_fluid
           + F_grad_epsilon
           + F_electrostriction
           + F_Maxwell
           + F_boundaries
           + F_residual
```

**The residual exists only when the other five terms are numbers and
every required control receipt is present.** A missing control does not
shrink the residual — it voids it (`residual_quotable = False`, residual
= NaN). Asserted by test in both directions, including the case where a
single term (`F_Maxwell = NaN`) voids an otherwise complete budget.

## Required control tests

| Control | Protocol |
|---|---|
| polarity_reversal | repeat at −V; even/odd split via the audited decomposition |
| pressure_gas_variation | vacuum + ≥2 gas pressures; ion-wind forces die with the medium |
| thermal | thermal ramp with drive off; IR map under drive |
| vibration | accelerometer + contact mic during every run |
| electrostatic_attraction | grounded-shroud comparison run |
| ion_wind | airflow measurement + reversed-polarity comparison |
| cable_forces | cable-drape permutations and force-null check |

## Lineage

The arithmetic (even/odd decomposition, cubic-harmonic extraction with
h₃ = a₃V_ac³/4 isolating the cubic fingerprint, EHD F ≈ Id/μ that refuses
vacuum) is the audited `r1070tb` / v0.6 implementation, reused not
reimplemented. What v0.7 adds is the *ledger*: named terms, named
controls, and a quotability gate.

Standing interpretation, unchanged since the Townsend Brown audit:

```text
RESIDUAL_IS_NOT_EVIDENCE_OF_NEW_PHYSICS
```

A residual is the prompt to find the next conventional term.
