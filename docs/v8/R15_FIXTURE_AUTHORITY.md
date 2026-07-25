# R15 P06 — Fixture Authority

**Tranche:** T2 Specimen Authority
**Module:** `r15/fixtures.py`
**Tests:** `tests/v8/test_fixtures.py`
**Receipt:** `docs/v8/receipts/P06.json`
**Status:** COMPLETE — synthetic only, no physical measurement.

## What this authority is

A specimen is never measured in free space: it is clamped, supported,
suspended, bonded, or pressed against a mount, and *how* it is held changes
what the instrument reads. This phase makes the mount part of the physical
model. It writes the fixture down as a typed record, models the boundary
condition the mount imposes on the synthetic modes, folds the fixture's
repeatability into the error budget, and — the load-bearing part — refuses
to let a fixture-induced shift be read as a specimen signal.

Nothing here is measured. No fixture has been machined, no specimen mounted,
no clamp torqued. Every frequency is arithmetic on a declared model in the
R11 mechanical chain's own units, and every record is a `SYNTHETIC_FIXTURE`
(the R15 claim taxonomy, `r15/claims.py`).

## The record — `FixtureRecord`

Conforms to `r15/schemas/fixture_record.schema.json`. Required keys:

| Key | Meaning |
| --- | --- |
| `fixture_id` | Fixture-namespace id (`FIX-…`); never a specimen id |
| `mount_type` | Centre clamp, three-point, suspension, elastomer, adhesive, or synthetic |
| `contact_points` | Contact geometry: label, position, boundary, contact stiffness |
| `preload` | Clamp force and torque, with mount-to-mount repeatability |
| `materials` | The interface material stack |
| `orientation_transform` | Euler rotation and translation in the fixture frame |
| `uncertainty` | Fixture repeatability (modal, remount, clamp-force) |

Beyond the required keys a record also carries its coupling medium, whether
an electrode contacts the specimen, the dominant boundary condition, the
expected perturbation classes, and the acquisition provenance
(`SYNTHETIC` here — `REAL`, `REPLAY`, `FAULT_INJECTION` are declared so the
mode is never silently assumed).

The six mount types are all present in `FIXTURE_REGISTRY`, one record each.

## Boundary conditions and synthetic modes

`FREE`, `SPRING` and `FIXED` map to end stiffnesses of the R11 grounded
mass-spring chain (`r11/mechboundary.py`). The synthetic modal frequencies
come from solving `K v = omega**2 M v` for that chain, not from an asserted
number, so **changing the support changes the modes**: the fundamental rises
`FREE < SPRING < FIXED`. Changing the boundary while the resonator holds
energy is booked through the R13 boundary-energy ledger
(`r13/boundaryenergy.py`) as ordinary boundary work — the ledger closes and
reports **no new energy channel**. The fixture is the route through which an
external agent (the clamp, the actuator) pays; it is never a source.

## The ordinary-explanation firewall

A fixture change that shifts a mode produces a `FIXTURE_EFFECT` — a **known
ordinary effect** in the R15 taxonomy, one of the explanations a residual
must survive before it may even be called an
`UNEXPLAINED_INSTRUMENT_RESIDUAL`.

- `fixture_shift_is_ordinary(...)` classifies the shift as exactly that:
  `claim_class = FIXTURE_EFFECT`, `is_signal = False`, and books the change
  through the energy ledger to show nothing new was created.
- `refuse_fixture_effect_as_signal(...)` refuses every route by which the
  shift is promoted to a specimen signal. To read a shift as a signal the
  fixture must be held identical across the comparison and its repeatability
  must bound the shift; a shift produced *by changing the fixture* fails
  that at the first step.

## Ids do not swap

Fixture ids (`FIX-…`) and specimen ids (`SPX-…`) live in separate
namespaces. `check_fixture_id` refuses a specimen-shaped id, `check_specimen_id`
refuses a fixture-shaped one, `FixtureRecord` refuses a specimen-shaped id at
construction, and `mount` refuses a fixture id in the specimen slot. A fixture
holds a specimen; it is not one.

## Remounting is a new binding

`mount(fixture, specimen_id, mount_index)` produces a `RunBinding` whose hash
folds the fixture content, the specimen id, and the mount index together.
`remount(...)` advances the mount index, so taking the specimen out and
putting it back yields a **distinct binding** — same parts, different mount,
different hash. Binding hashes are deterministic (seeded content only, no
wall-clock).

## The error budget and the precision gate

`fixture_error_budget(...)` conforms to `r15/schemas/error_budget.schema.json`
and combines three fixture terms in quadrature: modal repeatability, remount
shift, and clamp-force repeatability through a declared sensitivity. Every
term is a declared model repeatability, not a measured one.

A fixture with an **unrecorded preload** cannot support a precision claim:
without a clamp force the contact stiffness — and hence the modal frequency —
is unconstrained, so the repeatability a precision claim rests on is
undefined. `precision_claim_supported` reports it and `assert_precision_claim`
blocks it as `BLOCKED_MISSING_INPUT`.

## Reversal and sensor-permutation plans

- `reversal_plan(...)` is a deterministic remount/reversal protocol that
  alternates a 180° reversal so a fixed orientation bias cancels across the
  set.
- `sensor_permutation_plan(...)` enumerates capped, lexicographically ordered
  sensor permutations: a fixture effect stays with the port, a specimen
  property follows the specimen, and permuting the two tells them apart.

Both are protocols. Nothing in them is executed here (`executed = False`).

## What this does not say

It does not say any fixture exists, that any specimen was mounted, or that any
clamp force, torque, modal frequency, or repeatability was measured — every
number is a declared model value. It does not say a fixture change is a
signal; a shift produced by changing the mount is a `FIXTURE_EFFECT`, and the
firewall refuses to promote it. No apparatus was operated.
`PHYSICAL_VALIDATION_NOT_CLAIMED`.

## Reopening test

Re-run `pytest tests/v8/test_fixtures.py -q`. Reopen this phase if any record
in `FIXTURE_REGISTRY` stops conforming to `fixture_record.schema.json`, if
`fixture_shift_is_ordinary` stops classifying a boundary-change shift as
`FIXTURE_EFFECT`, if `refuse_fixture_effect_as_signal` stops raising, if a
specimen id becomes usable as a fixture id (or vice versa), if a missing
preload stops blocking a precision claim, or if a remount stops producing a
distinct binding hash.
