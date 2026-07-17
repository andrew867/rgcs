# Magnon-polariton and transduction interface (C01/C13)

Coverage: **A04, A05, A06**.
Implementation: `rscs2_core.refmodels.polariton.hopfield_3x3`,
`polarization_channel`, `transduction_interface`.

## Three-mode extension (A04) — `REDUCED_ORDER_VALIDATED`

A magnon branch is added to the exciton-photon pair:

    H = [ E_x        Omega_xc/2   Omega_xm/2 ]
        [ Omega_xc/2 E_c          0          ]
        [ Omega_xm/2 0            E_m(B)     ]

    E_m(B) = E_m0 + (dE/dB) * B      (declared Zeeman channel)

The magnon couples to the exciton, not directly to the cavity photon,
which is the standard reduced topology. The 3x3 reduces exactly to the
2x2 when `Omega_xm = 0` — tested, and the reason the extension is
trustworthy at all.

## Polarization channel (A05) — `ENG` rule, declared

    TE: coupling = Omega_R
    TM: coupling = Omega_R * cos(theta)

This is a **declared field-projection rule**, labelled ENG. It is a
modelling convention chosen for this reference system, not a derived
result, and it is documented as such so nobody later cites it as
established physics.

## Transduction interface (A06) — `INTERFACE_ONLY`

`transduction_interface()` returns a schema hook and **no numbers**:

```
{"classification": "INTERFACE_ONLY", "value": None,
 "declares": ["input mode (polariton branch, Hopfield fractions)",
              "output mode (itinerant photon)",
              "efficiency: NOT COMPUTED"]}
```

Quantum transduction efficiency is not implemented. There is no
microscopic solver behind this hook, so it emits nothing rather than a
plausible-looking figure (gate G15). Fabricating a conversion
efficiency would be the single most tempting number in this module and
is exactly the one that does not exist.

## Magnetic mechanisms and quartz

The magnon branch belongs to the reference material. Per the frozen
authority list, **no magnetic, excitonic, or ferrotoroidic mechanism is
imported into alpha quartz** without new material-specific evidence and
a registered capability. Neither exists. The 3x3 model is mathematics
about another material and is retained for comparison only.

## Sources

`SRC-V4-13` (chiral phonons), `SRC-V4-14` (spin-momentum locking) —
both FULL_TEXT_LOCAL, retained with page-level provenance. Their
presence in the registry is not an endorsement of transferring their
mechanisms to quartz; the `forbidden_transfer` column exists for that.
