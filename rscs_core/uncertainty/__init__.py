"""RSCS-O.11 uncertainty-propagation operator.

Propagates an :class:`~rscs_core.coordinates.Uncertainty` (RSCS-C.12) through
exact scaling and reciprocal-scaling, delegating to the frozen v2
``UncertainValue`` (RGCS-M.10/M.11) so results match v2 exactly. First-order
relative uncertainty is invariant under an exact multiplicative factor.
"""

from __future__ import annotations

from ..coordinates import Uncertainty
from ..registry import rscs_classified

__all__ = ["scale", "reciprocal_scale", "combine_relative"]


@rscs_classified("DER", registry=("RSCS-O.11",), units="unit -> unit",
                 note="exact scaling: u_rel invariant (RGCS-M.11); delegates "
                      "to frozen v2 UncertainValue.scale")
def scale(u: Uncertainty, factor: float) -> Uncertainty:
    """Multiply by an exact factor; relative uncertainty is unchanged."""
    if not isinstance(u, Uncertainty):
        raise TypeError("u must be an Uncertainty (RSCS-C.12)")
    scaled = u.uncertain_value.scale(factor)
    return Uncertainty(scaled.mean, scaled.u_rel, u.dist)


@rscs_classified("DER", registry=("RSCS-O.11",), units="unit -> 1/unit",
                 note="numerator/value; first-order u_rel invariant "
                      "(delegates to frozen v2 UncertainValue)")
def reciprocal_scale(u: Uncertainty, numerator: float) -> Uncertainty:
    """numerator / value; first-order relative uncertainty is unchanged."""
    if not isinstance(u, Uncertainty):
        raise TypeError("u must be an Uncertainty (RSCS-C.12)")
    rec = u.uncertain_value.reciprocal_scale(numerator)
    return Uncertainty(rec.mean, rec.u_rel, u.dist)


@rscs_classified("DER", registry=("RSCS-O.11",), units="dimensionless",
                 note="quadrature sum of relative uncertainties for a product "
                      "of independent factors (standard GUM first-order)")
def combine_relative(*u_rels: float) -> float:
    """Combine independent relative uncertainties in quadrature:
    sqrt(sum u_rel_i^2). Monotonic: adding a term never decreases the result."""
    total = 0.0
    for r in u_rels:
        if not (isinstance(r, (int, float)) and r >= 0):
            raise ValueError("relative uncertainties must be >= 0")
        total += float(r) ** 2
    return total ** 0.5
