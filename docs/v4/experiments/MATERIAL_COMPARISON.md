# E04 — Quartz-family and specimen comparison

Coverage: **E021, G015–G030**.
Status: **`PROTOCOL_READY_HARDWARE_REQUIRED`**.
Preregistration: `PREREG-E04`.

## Question

Do clear quartz, citrine, amethyst, smoky quartz, and rutilated quartz
behave differently under identical protocols?

## The confound that eats this experiment

Mineral variety is confounded with **geometry, orientation, surface
state, inclusion content, size, and price** — because specimens are
bought, not grown to spec. An amethyst that rings differently may
simply be 2 mm longer, cut at a different angle, or more chipped.

The design therefore matches or models: length, mass, facet count,
taper, density, clarity, inclusion content, surface state, orientation.
Where matching is impossible, the covariate is measured and modelled —
and where it cannot be measured (orientation, absent XRD), the
comparison is **reported as confounded** rather than run and believed.

Since [XRD_ORIENTATION_CONTRACT.md](../XRD_ORIENTATION_CONTRACT.md)
leaves every specimen's orientation unknown, and the elastic model is
orientation-dependent, **variety-vs-orientation is currently
inseparable**. That is a blocker on the interpretation, not just the
data.

## Design

- **Cheap quartz before precision crystals** (E021). If the effect
  appears in a $5 rod, the $500 wand is not the cause.
- Within-specimen repeats **and** between-specimen variation —
  hierarchical, because n=1 per variety is not a comparison.
- Blinded specimen IDs; seller metadata separated from measurement
  (`metrology.specimen_record`).
- Same acoustic, impedance, node, and loading tests across all.

## Analysis

Hierarchical model with variety as a factor and geometry/inclusion as
covariates. Small-sample warnings are mandatory outputs. Preregistered
null criteria.

## Boundaries

- **Do not attribute a difference to colour or inclusion type when
  geometry, orientation, or surface damage can explain it.** Colour in
  quartz comes from trace impurities and irradiation at the ppm level;
  the elastic tensor barely notices. Geometry is a far larger lever,
  and the honest prior is that geometry wins.
- No cherry-picking specimens that "work".
- Price is not a variable with physical meaning.

## Retuning (ORPHAN-005)

The source claim that a crystal can be "retuned" by exposure is
operationalized here: a persistent pre/post shift in modal frequency or
Q, measured against a **sham-exposed matched control**, that exceeds
the control's day-to-day drift. Falsified if it does not.

## Blocker

Hardware + specimens + metrology. Nothing procured or measured.
