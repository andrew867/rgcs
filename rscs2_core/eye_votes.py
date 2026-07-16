"""Eye Consensus vote layer (Agent M9).

Wraps the validated v4.0.0 field-level eye engine (rscs2_core.eye)
with typed diagnostic VOTES carrying applicability. NOT_APPLICABLE
and INTERFACE_ONLY votes are NEVER counted as positive evidence; the
vote layer can DOWNGRADE the field-level verdict (e.g. to
INSUFFICIENT_RESOLUTION) but can never upgrade it. A stable eye is
not required for release: the null family passes."""

from __future__ import annotations

from dataclasses import dataclass

from .multiphysics import applicability as cap_applicability
from .multiphysics import get_material

VERDICTS = ("DISTINCT_STABLE_CANDIDATE",
            "UNCERTAINTY_OVERLAPS_CONVENTIONAL_NODE",
            "CONVENTIONAL_NODE_EXPLAINS_RESULT",
            "CONVENTIONAL_MODEL_INSUFFICIENT",
            "CANDIDATE_NEW_COUPLING",
            "STABLE_CANDIDATE_REGION",       # legacy v4.0.0 records
            "MODE_SPECIFIC_CANDIDATE",
            "BOUNDARY_SENSITIVE_CANDIDATE",
            "MESH_ARTIFACT_REJECTED", "NO_STABLE_CANDIDATE",
            "INSUFFICIENT_RESOLUTION", "CONTRADICTORY_DIAGNOSTICS")

#: verdicts asserting a gate-surviving (stable) candidate
_STABLE_VERDICTS = frozenset({
    "DISTINCT_STABLE_CANDIDATE",
    "UNCERTAINTY_OVERLAPS_CONVENTIONAL_NODE",
    "CONVENTIONAL_NODE_EXPLAINS_RESULT", "CANDIDATE_NEW_COUPLING",
    "CONVENTIONAL_MODEL_INSUFFICIENT", "STABLE_CANDIDATE_REGION"})

APPLICABILITIES = ("APPLICABLE", "NOT_APPLICABLE", "INTERFACE_ONLY",
                   "REFERENCE_ONLY")

#: the expanded vote catalogue: vote_id -> (quantity/description,
#: capability key gating it for the target material, units)
VOTE_CATALOGUE = {
    "torsional_mode_energy": ("torsion.mechanical.mode_energy",
                              "elasticity_anisotropic", "J"),
    "mechanical_circulation": ("circulation.mechanical.displacement",
                               "elasticity_anisotropic", "m^2"),
    "ordinary_nodal_structure": ("conventional node/antinode control",
                                 "elasticity_anisotropic", "m"),
    "mesh_fixture_sensitivity": ("persistence controls (D13/D14)",
                                 "elasticity_anisotropic", "mm"),
    "optical_sam": ("angular_momentum.optical.spin",
                    "optical_birefringent", "J s/m^3"),
    "optical_oam": ("angular_momentum.optical.orbital",
                    "optical_birefringent", "J s/m^3"),
    "topological_charge": ("optical phase winding",
                           "optical_birefringent", "integer"),
    "chirality_density": ("chirality.spin_texture",
                          "magnetic_order", "dimensionless"),
    "chiral_phonon_am": ("angular_momentum.phonon.chiral_mode",
                         "chiral_phonons", "kg m^2/s"),
    "hybridization_participation": ("near-degenerate pair "
                                    "participation",
                                    "elasticity_anisotropic",
                                    "fraction"),
    "symmetry_breaking_persistence": ("M6 splitting persistence",
                                      "elasticity_anisotropic", "Hz"),
    "dynamic_boundary_sensitivity": ("M6 boundary-variant shift",
                                     "elasticity_anisotropic", "mm"),
    "magnetoelectric_quadrature": ("dynamic ME I/Q",
                                   "magnetoelectric_dynamic", "s/m"),
    "cross_field_am_alignment": ("alignment of DISTINCT AM "
                                 "quantities (geometric only)",
                                 "optical_birefringent",
                                 "correlation"),
}

#: votes that need an actually SOLVED optical field even when the
#: material capability exists
_NEEDS_SOLVED_OPTICAL = {"optical_sam", "optical_oam",
                         "topological_charge",
                         "cross_field_am_alignment"}


@dataclass(frozen=True)
class EyeVote:
    vote_id: str
    applicability: str
    quantity: str
    units: str
    data_source: str
    value: float | None
    uncertainty: float | None
    control_result: str | None
    classification: str
    reason: str | None

    def __post_init__(self):
        if self.vote_id not in VOTE_CATALOGUE:
            raise ValueError(f"unregistered vote '{self.vote_id}'")
        if self.applicability not in APPLICABILITIES:
            raise ValueError("bad applicability")
        if self.applicability == "APPLICABLE" and \
                self.control_result is None:
            raise ValueError("APPLICABLE votes require a control "
                             "result")
        if self.applicability != "APPLICABLE" and \
                self.value is not None:
            raise ValueError("non-applicable votes carry null values")


def quartz_vote_applicability(material_id: str =
                              "material.alpha_quartz",
                              solved_optical_field: bool = False
                              ) -> dict:
    """Applicability of every catalogue vote for a material, from the
    M2 capability record. Optical votes additionally require a solved
    optical field (else INTERFACE_ONLY)."""
    mat = get_material(material_id)
    out = {}
    for vid, (qty, cap, units) in VOTE_CATALOGUE.items():
        app = cap_applicability(mat, cap)["applicability"]
        if app == "APPLICABLE" and vid in _NEEDS_SOLVED_OPTICAL \
                and not solved_optical_field:
            app = "INTERFACE_ONLY"
            reason = ("material supports optics but no optical field "
                      "was actually solved in this run")
        else:
            reason = None if app == "APPLICABLE" else \
                cap_applicability(mat, cap)["reason"]
        out[vid] = {"applicability": app, "quantity": qty,
                    "units": units, "reason": reason}
    return out


def consensus_from_votes(field_level_verdict: str,
                         votes: list[EyeVote],
                         min_applicable: int = 3) -> dict:
    """Combine the field-level engine verdict with the vote layer.
    Only APPLICABLE votes count; the layer may DOWNGRADE to
    INSUFFICIENT_RESOLUTION (too few applicable votes) but can never
    upgrade toward STABLE."""
    if field_level_verdict not in VERDICTS:
        raise ValueError("unknown field-level verdict")
    applicable = [v for v in votes
                  if v.applicability == "APPLICABLE"]
    excluded = [v for v in votes
                if v.applicability != "APPLICABLE"]
    if len(applicable) < min_applicable:
        verdict = "INSUFFICIENT_RESOLUTION"
    else:
        verdict = field_level_verdict
    # UPGRADE PROHIBITION: the vote layer cannot make a non-stable
    # field verdict stable; unimplemented mechanisms are excluded from
    # the count but their ABSENCE never counts against an anomaly
    if field_level_verdict not in _STABLE_VERDICTS:
        assert verdict not in _STABLE_VERDICTS
    return {
        "verdict": verdict,
        "field_level_verdict": field_level_verdict,
        "n_applicable_votes": len(applicable),
        "n_excluded_votes": len(excluded),
        "excluded_reasons": {v.vote_id: v.applicability
                             for v in excluded},
        "release_policy": "a null/conventional verdict PASSES the "
                          "release (gate J2)",
        "deterministic": True,
    }
