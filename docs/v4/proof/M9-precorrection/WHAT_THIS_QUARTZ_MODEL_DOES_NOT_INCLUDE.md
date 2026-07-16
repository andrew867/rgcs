# What This Quartz Model Does Not Include (Agent M9; gate J4)

Binding statement for the canonical 110 mm alpha-quartz application.
Everything below is either NOT IMPLEMENTED for quartz or NOT
APPLICABLE to quartz by its registered capability record — a request
returns a typed NOT_APPLICABLE result, never a numeric zero.

## Not applicable to alpha quartz (capability firewall, tested)

- magnetic order, magnon modes, spin-orbit blocks, spin-phonon
  coupling, chirality of spin textures;
- excitons of any flavor and exciton-magnon coupling;
- ferrotoroidic order and magnetic toroidal moments;
- dynamic magnetoelectric tensors and their optical-rotation
  observables;
- IOME domain writing and thermal domain selection;
- quantum-statistical (metacrystal) response and plasmonic near
  fields;
- microscopic (proton) tunnelling models;
- chiral-phonon Zeeman physics (no registered quartz g-factor);
- any historical spacetime-torsion field (SOURCE_HYPOTHESIS ceiling,
  no solver).

## Not implemented anywhere in RGCS v4 (all materials)

- DFT, Bethe-Salpeter, ab-initio spin dynamics, QFT;
- microscopic plasmonic simulation;
- full uniaxial double-refraction walk-off (plane-wave indices only,
  declared);
- quantum photon-statistics generation (the metacrystal transfer is a
  declared reduced rule);
- photon creation from classical boundary switching (classical mode
  mixing only, by construction and wording tests).

## Reference systems are not quartz

Every reduced-order model (exciton-magnon, avoided crossing, dynamic
ME, metacrystal, LiNiPO4 IOME, MnF2 comparator, nonlinear AFM,
phonon-controlled exchange, chiral phonon, dressed spin) is a
SEPARATE_REFERENCE_SYSTEM with `reference_only: true`; alias lookups
that would let a toy system inherit quartz identity are rejected.

## Eye Consensus posture

The canonical verdict remains in the conventional/null family
(v4.0.0: CONVENTIONAL_NODE_FOUND). Votes for unsupported mechanisms
are recorded NOT_APPLICABLE and are never counted as evidence;
optical votes without an actually solved optical field are
INTERFACE_ONLY. A stable eye is not required for release.
