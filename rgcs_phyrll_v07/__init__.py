"""RGCS Phyrll v0.7 -- engineering optimizer and measurement-prep package.

The v0.7 active correction, verbatim in spirit:

    Do not try to prove thrust.
    Stop trying to make the arithmetic carry the physics;
    make the physics pipeline carry the physics.

What changed from v0.6 and why:

* ``67.3`` is now typed ``SOURCE_DISPLAY`` and ``64672/961`` is typed
  ``EXACT_ARITHMETIC``. They are related by ONE-DECIMAL ROUNDING and by
  nothing else; the exact gap 33/9610 is asserted, not footnoted.
* exactly ONE function in the whole package may compute a candidate
  force, and no thrust claim exists without a measured eta.
* the ring model is an OPTIMIZER: which mask/weight family maximises
  effective field-centre displacement under the source locks -- not a
  proof engine.
* success is |d_eff| up, |dB| up (bench), arg alignment, bounded
  controls. Success is NOT force.

Source locks (GEOMETRY_DESIGN, immutable inputs to the optimizer):

    37-family ring   35/37 running   33 active steering
    no mechanical rotation
    f_c = 1,683,456 Hz = 4096*411,  411/37 = 11 + 4/37
    188/288 = 47/72

    PUBLICATION: HOLD
"""

from __future__ import annotations

from fractions import Fraction as F

RUN_ID = "R10.72-PHYRLL-ENGINEERING-V07"

#: The five role classes. Only PHYSICAL_MEASUREMENT may carry a
#: physical-performance claim, and only with a measured value attached.
ROLE_CLASSES = ("SOURCE_DISPLAY", "EXACT_ARITHMETIC", "GEOMETRY_DESIGN",
                "PHYSICAL_MEASUREMENT", "BENCH_REQUIRED")

#: Source locks the optimizer must never vary.
SOURCE_LOCKS = {
    "ring_family": 37,
    "running_cells": 35,
    "steering_active": 33,
    "mechanical_rotation": False,
    "carrier_hz": 1683456,
    "carrier_ratio": F(411, 37),
    "aux_ratio_188_288": F(47, 72),
}

PUBLICATION_STATUS = "HOLD"

__all__ = ["RUN_ID", "ROLE_CLASSES", "SOURCE_LOCKS", "PUBLICATION_STATUS"]
