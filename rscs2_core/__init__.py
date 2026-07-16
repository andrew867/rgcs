"""rscs2_core — RGCS v4 / RSCS 2.0 multiphysics platform (IN DEVELOPMENT).

Status: FOUNDATION. This package is under active v4 development on the
`v4-dev` branch and is NOT part of any released tag. The frozen v3
libraries (`rgcs_core`, `rscs_core`, `archive/`) are untouched.

What is verified and shipped in this foundation:
  * the analytic reference formulas (`rscs2_core.reference`) — closed-form
    truths for the benchmark systems, unit-tested independently of any
    solver;
  * the RSCS 2.0 registry + classification lint
    (`rscs2_core.registry`) — governance for RSCS2-* ids.

What is NOT yet validated (see docs/plans-v4/V4_AGENT_00_HANDOFF.md):
  * the CPU finite-element eigensolver does not yet reproduce the
    analytic beam eigenfrequencies to the required tolerance
    (V4_ACCEPTANCE_CRITERIA M3). No solver result is exposed as
    validated, and no release is possible until the M3 gate is green.

Planning package: docs/plans-v4/.
"""

from __future__ import annotations

__version__ = "4.0.0.dev0"
__status__ = "foundation"

__all__ = ["__version__", "__status__"]
