"""RGCS R10.8.2 — Locked Two-Layer Earth Root and Source-Map Calibration.

R10.8.1 built the general CW Atlas and bidirectional geocoder. R10.8.2 *locks*
the operator-selected Earth-root configuration (``EARTH_ROOT_D_V1``) and makes
the source-map experiment produce **candidate pins, cells, regions, or
alias sets with uncertainty** instead of stopping at a generic
``NO_UNIQUE_GEOGRAPHIC_DECODE``.

It reuses the ``cwatlas`` engine (frames, icosahedron, dodecahedral dual,
subdivision, codecs, calibration, uncertainty, claims) and adds the locked
two-layer root: a **fixed** spatial anchor (the Wilkes Land gravity-anomaly
centroid, as a versioned centroid+uncertainty profile) and a **dynamic**
phase-zero direction (the South Atlantic Anomaly magnetic minimum, resolved at
the packet's encoded epoch and body-relative shell radius).

The discipline is the whole point:

* candidate maps are fit **only** against sealed training anchors (the Wilkes
  fixed root and the user-reported ``165876523 = Stonehenge`` training anchor);
* the winning or retained ensemble is **frozen** with a cryptographic receipt
  before any holdout is scored;
* after the freeze there is **no result shopping** — no regridding, no
  handedness flip, no root/topology/tokenization/epoch swap, no moving a label
  between training and holdout; any such change mints a new profile id and
  invalidates prior-holdout comparison;
* where the anchors cannot select one mapping, the complete **bounded alias
  set** and disagreement surface are rendered — the app produces pins or
  regions, never a bare refusal, but never invented precision either.

A candidate pin is a ``SOFTWARE_RESULT`` under a declared calibration
(``CALIBRATED_CANDIDATE``). **It is not a measured fact.** The source
attribution is user-reported and unverified: this package may produce
candidate calibrated source maps, but it does not claim a nonhuman origin,
established physical semantics, or any physical effect.
"""

from __future__ import annotations
