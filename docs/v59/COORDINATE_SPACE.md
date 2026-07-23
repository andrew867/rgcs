# Coordinate Space — Root Frames, Routes, and Codec Binding

**Authority:** RGCS R10.10 / v5.9.0 (candidate)
**Scope:** Roots-first coordinate frames, rooted interbody routes with a light-time floor, and the refusal to read a bare codec number as a position.
**Last verified commit:** v5.8.0 baseline (branch v580-r10-10)
**Prerequisites:** [CW_CODEBOOK_V2.md](CW_CODEBOOK_V2.md) (what a codec output is), [FREQUENCY_AND_PHASE_SYSTEM.md](FREQUENCY_AND_PHASE_SYSTEM.md) (epochs and timebases)
**Related code / tests / schemas:** [../../r10/rootframe.py](../../r10/rootframe.py), [../../r10/route.py](../../r10/route.py), [../../r10/codecbind.py](../../r10/codecbind.py); tests/v52/test_r10_rootframe.py, tests/v52/test_r10_route.py, tests/v52/test_r10_codecbind.py
**Known limitations:** These are coordinate conventions and bookkeeping. Declaring a frame or compiling a route reaches, actuates, and measures nothing. No physical edge or gateway is claimed. Hardware is deferred.
**Next review trigger:** A new frame convention, a change to the causal (light-time) floor, or any binding rule change in `codecbind.py`.

## Roots-first frames (`rootframe.py`)

Interbody addresses (Earth-to-Moon, Earth-to-Mars) are built on
**calculated roots**, not on latitude/longitude. Lat/lon, elevation, and
ephemerides are *calibration observations*; the address frame is a root
with a declared orientation, epoch, handedness, scale, and uncertainty.

The mathematics that keeps this honest is **roll-identifiability**:

- **A single direction does not determine a frame.** Point the primary
  axis at the Sun and the frame can still spin about that axis — one
  degree of freedom (the roll) is unfixed. A root built from one
  direction is `ROOT_UNDERDETERMINED` and is refused.
- **Two non-parallel directions determine a rotation.** From a primary
  and a second, non-parallel direction the full orientation (a
  quaternion) is fixed by Gram-Schmidt, and the module round-trips it
  exactly enough to verify.

This is the same "two non-parallel directions" rule that recovers a
crystal c-axis in [CRYSTAL_SPECIMEN_PROGRAM.md](CRYSTAL_SPECIMEN_PROGRAM.md).

## Rooted routes (`route.py`)

Routes compile *through roots*, not lat/lon:

    Earth local cell → Earth body root → Earth-Moon parent root
                     → Moon body root → Moon local cell

Each transition carries a source root, destination root, epoch,
transform, a conventional travel-time baseline, and a causal status. The
compiler's value is what it **refuses**:

- edges whose two roots sit at incompatible epochs;
- transitions with no supported graph edge;
- roots whose roll is undetermined (delegated to `rootframe`);
- most importantly, **any conventional travel across nonzero distance in
  zero time.**

`ROUTE_SOFTWARE_VALID` means the frames compose and the bookkeeping is
consistent — never that a physical edge exists. That is
`PHYSICAL_EDGE_UNSUPPORTED`, and `CAUSAL_DELAY_REQUIRED` — the **light-time
floor** — is attached to every hop that spans a distance. Software route
existence is not a physical gateway.

## Codec binding (`codecbind.py`)

A CW codec output (see [CW_CODEBOOK_V2.md](CW_CODEBOOK_V2.md)) is a
NUMBER. A number is not a coordinate. Before a decoded value can be
called a position it must be bound to declared things:

- **A frame and an epoch are mandatory** (`GREEN_FRAME_EPOCH_REQUIRED`).
  The same digits name different places in different frames and at
  different epochs; binding without both is refused.
- **An uncertainty is mandatory.** A decoded integer is not an infinitely
  precise point; a binding with zero or missing uncertainty is refused.
- **No retrofit.** A binding does not back-date or re-interpret an
  earlier codec result.

Until a frame, an epoch, and an uncertainty are all attached, the value
is an uninterpreted symbol, and the module refuses to pretend otherwise.

PHYSICAL_VALIDATION_NOT_CLAIMED
