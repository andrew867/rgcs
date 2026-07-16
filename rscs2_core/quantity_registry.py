"""Torsion / circulation / angular-momentum quantity registry
(Agent M3; shared schema section 3).

Twelve DISTINCT registered quantities. Frozen boundary 7: none of
these is the same physical object as any other; geometric comparison
is permitted, physical identity is mechanically rejected. The
historical spacetime-torsion entry has ceiling SOURCE_HYPOTHESIS and
no solver."""

from __future__ import annotations

from dataclasses import dataclass


class IdentityError(TypeError):
    """Raised when two distinct registered quantities are asserted to
    be the same physical object."""


@dataclass(frozen=True)
class QuantityKind:
    quantity_id: str
    dimensions: str                # SI base-dimension expression
    si_units: str
    coordinate_dependent: bool
    origin_dependent: bool
    pt_behavior: str               # parity/time-reversal signature
    state_block: str
    material_predicate: str        # capability key or 'any'
    classification_ceiling: str
    forbidden_aliases: tuple

    def check_alias(self, name: str) -> None:
        low = name.lower().replace(" ", "_")
        for alias in self.forbidden_aliases:
            if alias in low:
                raise IdentityError(
                    f"'{name}' is a forbidden alias for "
                    f"{self.quantity_id}: distinct physical objects "
                    "(frozen boundary 7)")


QUANTITIES: dict[str, QuantityKind] = {q.quantity_id: q for q in (
    QuantityKind("torsion.mechanical.twist_rate", "1/L", "rad/m",
                 True, False, "P:+1 T:+1", "mechanical",
                 "elasticity_isotropic", "CORE_VALIDATED",
                 ("spacetime", "toroidal", "optical_vortex")),
    QuantityKind("torsion.mechanical.mode_energy", "M L^2 / T^2", "J",
                 False, False, "P:+1 T:+1", "mechanical",
                 "elasticity_isotropic", "CORE_VALIDATED",
                 ("spacetime", "chiral_phonon")),
    QuantityKind("torsion.curve.frenet_serret", "1/L", "1/m",
                 True, False, "P:-1 T:+1", "mechanical", "any",
                 "CORE_VALIDATED",
                 ("force_field", "spacetime", "twist_rate")),
    QuantityKind("circulation.mechanical.velocity", "L^2/T", "m^2/s",
                 True, False, "P:+1 T:-1", "mechanical",
                 "elasticity_isotropic", "CORE_VALIDATED",
                 ("vortex_claim", "optical", "toroidal")),
    QuantityKind("circulation.mechanical.displacement", "L^2", "m^2",
                 True, False, "P:+1 T:+1", "mechanical",
                 "elasticity_isotropic", "CORE_VALIDATED",
                 ("vortex_claim", "optical", "toroidal")),
    QuantityKind("angular_momentum.optical.spin",
                 "M/(L T^2) * T = M/(L T)", "J s/m^3", False, False,
                 "P:-1 T:-1", "optical", "any", "CORE_VALIDATED",
                 ("orbital", "mechanical", "phonon", "toroidal")),
    QuantityKind("angular_momentum.optical.orbital",
                 "M/(L T)", "J s/m^3", True, True,
                 "P:+1 T:-1", "optical", "any", "CORE_VALIDATED",
                 ("spin_density", "mechanical", "toroidal")),
    QuantityKind("angular_momentum.optical.transverse_spin",
                 "M/(L T)", "J s/m^3", True, False,
                 "P:-1 T:-1", "optical", "any", "CORE_VALIDATED",
                 ("longitudinal", "mechanical")),
    QuantityKind("angular_momentum.phonon.chiral_mode",
                 "M L^2/T", "kg m^2/s", False, False,
                 "P:+1 T:-1", "phonon_internal", "chiral_phonons",
                 "REDUCED_ORDER_VALIDATED",
                 ("optical_spin", "magnon", "toroidal", "quartz_eye")),
    QuantityKind("chirality.spin_texture", "1", "dimensionless",
                 True, False, "P:-1 T:+1", "spin", "magnetic_order",
                 "REDUCED_ORDER_VALIDATED",
                 ("optical_helicity", "mechanical")),
    QuantityKind("toroidal_moment.magnetic", "I L^2", "A m^2 (micro)",
                 True, True, "P:-1 T:-1", "domain",
                 "ferrotoroidic_order", "REDUCED_ORDER_VALIDATED",
                 ("mechanical_vortex", "optical_vortex", "quartz_eye",
                  "circulation")),
    QuantityKind("torsion.historical.spacetime_claim", "UNDECLARED",
                 "UNDECLARED", True, True, "UNDECLARED",
                 "source_hypothesis", "none", "SOURCE_HYPOTHESIS",
                 ("mechanical", "curve", "optical", "phonon",
                  "toroidal", "circulation")),
)}


def get_quantity(quantity_id: str) -> QuantityKind:
    if quantity_id not in QUANTITIES:
        raise KeyError(f"unregistered quantity '{quantity_id}'")
    return QUANTITIES[quantity_id]


def compare_geometric(qa: str, qb: str, note: str = "") -> dict:
    """Permitted: GEOMETRIC comparison record between two quantities.
    The record explicitly denies physical identity."""
    a, b = get_quantity(qa), get_quantity(qb)
    return {"kind": "GEOMETRIC_COMPARISON_ONLY",
            "quantities": [a.quantity_id, b.quantity_id],
            "physical_identity": False,
            "note": note or "spatial-pattern comparison; the "
                            "quantities are distinct physical objects"}


def assert_identity(qa: str, qb: str):
    """The forbidden operation: identity between distinct registered
    quantities ALWAYS raises (same id trivially allowed)."""
    if qa == qb:
        return True
    raise IdentityError(
        f"physical identity between '{qa}' and '{qb}' is forbidden "
        "(frozen boundary 7); use compare_geometric for pattern "
        "comparison")


def has_solver(quantity_id: str) -> bool:
    """The historical spacetime claim has NO numerical solver."""
    return get_quantity(quantity_id).classification_ceiling != \
        "SOURCE_HYPOTHESIS"
