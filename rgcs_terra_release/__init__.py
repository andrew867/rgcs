"""Terra public-release lane, v0.6.

Two jobs, both filters in spirit:

* ``release_filter`` -- decides what may enter a public coordinate/codec
  release, excluding message-decoding material (Crabwood/ASCII/plaintext
  lanes) unless it already sits in a private, non-release archive;
* ``miami_bermuda_calibration`` -- the 236805/142 geodesic candidate,
  scored against the declared Bermuda metrics WITH a look-elsewhere null
  control, and the two operator vector candidates mapped through the
  EXISTING root projector. No projector is fitted to Miami.

    PUBLICATION: HOLD
"""

from __future__ import annotations

RUN_ID = "R10.71-TERRA-RELEASE"
PUBLICATION_STATUS = "HOLD"

__all__ = ["RUN_ID", "PUBLICATION_STATUS"]
