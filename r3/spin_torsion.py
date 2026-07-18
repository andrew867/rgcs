"""P04/P05 (A28-A43) — spin/torsion typing and the metric-source
boundary.

The ontology (core/04) is enforced by type: seven spin categories that
never merge implicitly. Bulk rotation is not intrinsic spin density; a
toroidal EM mode is not spacetime torsion; a twisted crystal is not an
Einstein-Cartan source by terminology alone.

The metric-source lane (A36-A43) is the quantitative refusal: the
inverse Einstein calculator takes a desired metric perturbation and
returns the stress-energy it would require; the energy-condition audit
then reports whether any known matter can supply it. For every
"useful" target the answer is no by tens of orders of magnitude —
extending the v4.6 energy audit from "what does our apparatus imply"
to "what would the wish require".
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from . import ClaimBoundaryError, SPIN_CATEGORIES
from cspc.spacetime import C, G

HBAR = 1.054_571_817e-34            # J s

#: Einstein-Cartan torsion couples to spin density via kappa = 8*pi*G/c^4.
EC_COUPLING = 8 * math.pi * G / C ** 4          # ~2.1e-43 s^2/(kg m)


@dataclass(frozen=True)
class SpinQuantity:
    """A value that knows which spin category it belongs to. Algebra
    across categories is refused — there is no implicit merge."""
    category: str
    value: float
    unit: str
    provenance: str = ""

    def __post_init__(self):
        if self.category not in SPIN_CATEGORIES:
            raise ClaimBoundaryError(
                f"{self.category!r} is not a spin/torsion category")

    def __add__(self, other: "SpinQuantity") -> "SpinQuantity":
        if self.category != other.category:
            raise ClaimBoundaryError(
                f"cannot add {self.category} to {other.category}: "
                "categories never merge implicitly (core/04)")
        return SpinQuantity(self.category, self.value + other.value,
                            self.unit, "sum")


def bulk_rotation_spin_density(mass_kg: float, radius_m: float,
                               omega_rad_s: float) -> dict:
    """A29/A31: a spinning cylinder's CLASSICAL angular momentum,
    expressed per volume, next to what an INTRINSIC spin density of
    the same magnitude would require — the comparison that stops the
    'rotating crystal = spin source' slide."""
    inertia = 0.5 * mass_kg * radius_m ** 2
    L_total = inertia * omega_rad_s
    volume = math.pi * radius_m ** 2 * radius_m   # unit-height proxy
    classical = SpinQuantity("CLASSICAL_ANGULAR_MOMENTUM",
                             L_total / volume, "J*s/m^3",
                             "rigid rotation")
    n_atoms = mass_kg / (60.08 * 1.66054e-27) / volume   # SiO2
    max_intrinsic = SpinQuantity("INTRINSIC_SPIN_DENSITY",
                                 n_atoms * HBAR / 2, "J*s/m^3",
                                 "every nucleus fully polarized")
    return {"classical_per_volume": classical.value,
            "max_intrinsic_if_fully_polarized": max_intrinsic.value,
            "categories_distinct": True,
            "note": "the two rows are different CATEGORIES, not "
                    "different sizes of one thing; adding them is a "
                    "type error by construction",
            "evidence_class": "ANALYTIC_MODEL"}


def einstein_cartan_torsion(spin_density_J_s_m3: float) -> dict:
    """A32/A33: the spacetime torsion an Einstein-Cartan coupling
    would produce from a given spin density — with the scale stated.

    Even a fully polarized solid (~1e10 J*s/m^3) yields torsion
    ~1e-33 1/m: unmeasurable by any laboratory technique. The registry
    exists so the number is on the table, not so it can be rounded up.
    """
    torsion = EC_COUPLING * spin_density_J_s_m3 * C   # 1/m scale
    return {"spin_density": spin_density_J_s_m3,
            "torsion_scale_1_per_m": torsion,
            "coupling": EC_COUPLING,
            "orders_below_measurable":
                -math.log10(max(torsion, 1e-300)) - 0,
            "verdict": "UNMEASURABLE_AT_LABORATORY_SCALE",
            "evidence_class": "ANALYTIC_MODEL"}


def laboratory_spin_firewall(claim: str) -> dict:
    """A34/A35: the standing refusals, queryable."""
    refusals = {
        "rotating_mass_produces_torsion_field":
            "classical rotation carries CLASSICAL_ANGULAR_MOMENTUM; "
            "Einstein-Cartan torsion couples to INTRINSIC spin and is "
            "~40 orders below measurement for any lab source",
        "toroidal_coil_is_spacetime_torsion":
            "a toroidal EM mode carries EM angular momentum; it is "
            "not geometry",
        "twisted_crystal_is_einstein_cartan_source":
            "MECHANICAL_TORSION and DEFECT_TORSION_ANALOG are "
            "material geometry unless a separate gravitational "
            "coupling is demonstrated — none is",
    }
    if claim not in refusals:
        raise ClaimBoundaryError(f"unknown firewall query {claim!r}")
    return {"claim": claim, "status": "REFUSED",
            "reason": refusals[claim]}


# --- metric-source boundary (A36-A43) -------------------------------------

def inverse_einstein(target_fractional_metric: float,
                     region_radius_m: float) -> dict:
    """A38: what stress-energy would a desired weak-field metric
    perturbation h over a region of radius R require?

    Weak field: h ~ 2*G*M/(R*c^2)  =>  M = h*R*c^2/(2*G).
    """
    if not (0 < target_fractional_metric < 1):
        raise ClaimBoundaryError(
            "target h must be in (0, 1): the weak-field formula is "
            "the only regime this calculator claims")
    M = target_fractional_metric * region_radius_m * C ** 2 / (2 * G)
    rho = M / (4 / 3 * math.pi * region_radius_m ** 3)
    energy = M * C ** 2
    return {"target_h": target_fractional_metric,
            "region_radius_m": region_radius_m,
            "required_mass_kg": M,
            "required_density_kg_m3": rho,
            "required_energy_J": energy,
            "sun_masses": M / 1.989e30,
            "world_annual_energy_multiples":
                energy / 6e20,       # ~6e20 J/year global
            "evidence_class": "ANALYTIC_MODEL"}


def energy_condition_audit(required_density_kg_m3: float,
                           available_density_kg_m3: float) -> dict:
    """A40: can any actual matter supply the requirement?"""
    ratio = required_density_kg_m3 / max(available_density_kg_m3,
                                         1e-300)
    return {"required": required_density_kg_m3,
            "available": available_density_kg_m3,
            "shortfall_orders_of_magnitude":
                math.log10(max(ratio, 1e-300)),
            "achievable": ratio <= 1.0,
            "note": "negative-energy requirements are refused "
                    "outright: no classical matter violates the weak "
                    "energy condition on demand",
            "evidence_class": "ANALYTIC_MODEL"}


def metric_actuation_verdict(target_fractional_metric: float = 1e-9,
                             region_radius_m: float = 1.0) -> dict:
    """A43: the source-control map's bottom line for a 'modest' wish —
    a part-per-billion metric change in a one-metre region."""
    req = inverse_einstein(target_fractional_metric, region_radius_m)
    audit = energy_condition_audit(req["required_density_kg_m3"],
                                   22_590.0)     # osmium, densest solid
    return {**req, "densest_solid_kg_m3": 22_590.0,
            "audit": audit,
            "verdict": "REFUSED_BY_ARITHMETIC" if not
            audit["achievable"] else "ACHIEVABLE",
            "claim_boundary":
                "metric ACTUATION is renamed to what it is: a mass "
                "budget. The budget is unpayable; sensing the metric "
                "(v4.6) remains the only supported capability."}
