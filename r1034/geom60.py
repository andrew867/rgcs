"""R10.34 Agent 03 — the 60°/120° triangular domain-wall primitive.

Ari's conclusion, implemented: the 60° quartz end is not a decorative
bevel, it is a TRIANGULAR-DOMAIN-WALL INTERFACE PRIMITIVE.

The arithmetic that supports the reframing is exact and is checked here:

    60 + 120 = 180          a 60 deg facet and a 120 deg bend are
                            supplementary -- the facet normal and the
                            bend are the same interface seen twice
    360 / 60 = 6            a 60 deg wall tiles the plane six-fold, the
                            triangular-lattice symmetry
    360 / 120 = 3           the bend closes a three-fold circuit
    120 = 2 * 60            the bend is exactly two facet units

Quartz (alpha-SiO2) is trigonal, point group 32, so three-fold symmetry
is the crystal's own symmetry, not an imposed one. That is why 60/120
is a candidate primitive and 51.843 deg is not: 360/51.843 = 6.944...,
which closes no circuit.

WHAT THIS IS NOT: no C-point, V-point or stress singularity is claimed
to exist. Ari's own rule is explicit -- "do not claim a node exists
until a solver or measurement locates one" -- and no solver is run here.
This module defines the CASES and the DETECTOR CONTRACT so that a
solver can later either find them or fail exactly.
"""

from __future__ import annotations

import math

#: alpha-quartz is trigonal, point group 32 (three-fold about c).
QUARTZ_POINT_GROUP = "32"
QUARTZ_FOLD = 3


def angle_arithmetic() -> list:
    rows = []
    for name, deg in (("FACET_60", 60.0), ("BEND_120", 120.0),
                      ("ALT_51_843", 51.843), ("FLAT_CONTROL_0", 0.0),
                      ("RIGHT_90_CONTROL", 90.0)):
        closes = (360.0 / deg) if deg else float("inf")
        rows.append({
            "case": name, "angle_deg": deg,
            "supplement_deg": 180.0 - deg if deg else None,
            "circuit_closure_360_over_angle": (round(closes, 6)
                                               if deg else ""),
            "closes_integer_circuit": bool(deg) and
                                      abs(closes - round(closes)) < 1e-9,
            "matches_quartz_3fold": bool(deg) and
                                    abs(360.0 / deg - QUARTZ_FOLD) < 1e-9
                                    or bool(deg) and
                                    abs(360.0 / deg - 2 * QUARTZ_FOLD) < 1e-9,
        })
    return rows


def supplementary_pair() -> dict:
    """The core claim: 60 and 120 are one interface, not two."""
    return {
        "facet_deg": 60.0, "bend_deg": 120.0,
        "sum_deg": 180.0, "are_supplementary": True,
        "bend_is_two_facet_units": abs(120.0 - 2 * 60.0) < 1e-12,
        "facet_tiles_plane_sixfold": abs(360.0 / 60.0 - 6) < 1e-12,
        "bend_closes_threefold": abs(360.0 / 120.0 - 3) < 1e-12,
        "quartz_point_group": QUARTZ_POINT_GROUP,
        "three_fold_is_intrinsic_to_quartz": True,
        "interpretation": "a 60 deg termination and a 120 deg routing "
                          "bend are supplementary views of the same "
                          "triangular domain-wall interface; the "
                          "three-fold circuit is quartz's own symmetry",
    }


def simulation_cases() -> list:
    """The comparison set Ari specified. Nothing is simulated here."""
    base = [
        ("TERMINATION_60", 60.0, "primary: triangular domain-wall primitive"),
        ("TERMINATION_51_843", 51.843, "alternative bevel; closes no circuit"),
        ("FLAT_CUT_CONTROL", 0.0, "negative control: no domain wall"),
        ("BEND_120_COMPLEMENT", 120.0, "routing path complement of the 60 facet"),
        ("ANNULAR_35_33_INTERFACE", None,
         "35-position ring with 33 active / 2 blank; couples to the "
         "SSPP/OAM lane"),
    ]
    rows = []
    for name, deg, note in base:
        rows.append({
            "case": name, "angle_deg": deg, "note": note,
            "is_control": "CONTROL" in name,
            "simulated": False, "solver_run": False,
            "expected_outputs": "C_points;V_points;stress_antinodes;"
                                "piezo_charge_phase_vortices;"
                                "impedance_discontinuity_map",
            "status": "CASE_DEFINED_NO_SOLVER_RUN"})
    return rows


def detector_contract() -> list:
    """What a detector must report for a find to count.

    Written as a contract precisely so that a later run cannot report a
    singularity without also reporting the things that would falsify it.
    """
    return [
        {"observable": "OPTICAL_C_POINT",
         "definition": "point of purely circular polarization; "
                       "ellipticity |S3|/S0 -> 1 with undefined azimuth",
         "required_evidence": "topological index +-1/2 from a closed "
                              "loop integral of the polarization azimuth",
         "falsifier": "index 0 on every enclosing loop",
         "mesh_convergence_required": True},
        {"observable": "OPTICAL_V_POINT",
         "definition": "vector singularity; field amplitude null with "
                       "undefined polarization direction",
         "required_evidence": "integer topological index from the same "
                              "loop integral, plus an amplitude null",
         "falsifier": "amplitude does not go to zero under refinement",
         "mesh_convergence_required": True},
        {"observable": "ACOUSTIC_STRESS_ANTINODE",
         "definition": "local maximum of the stress invariant with a "
                       "displacement node (see r1025.nodes)",
         "required_evidence": "co-location of displacement null and "
                              "stress maximum, stable under refinement",
         "falsifier": "the two separate as the mesh refines",
         "mesh_convergence_required": True},
        {"observable": "PIEZO_CHARGE_PHASE_VORTEX",
         "definition": "2*pi winding of the surface-charge phase",
         "required_evidence": "closed-loop phase winding of +-2*pi n "
                              "with n != 0",
         "falsifier": "winding collapses to 0 with finer sampling",
         "mesh_convergence_required": True},
        {"observable": "IMPEDANCE_DISCONTINUITY",
         "definition": "acoustic/EM impedance step at the facet",
         "required_evidence": "computed from the anisotropic tensors, "
                              "not assumed from the angle",
         "falsifier": "step vanishes for the flat-cut control too",
         "mesh_convergence_required": False},
    ]


def report() -> dict:
    return {
        "schema": "rgcs.r1034.geom60.v1",
        "supplementary_pair": supplementary_pair(),
        "angle_arithmetic": angle_arithmetic(),
        "simulation_cases": simulation_cases(),
        "detector_contract": detector_contract(),
        "singularity_found": False,
        "solver_run": False,
        "physical_validation_claimed": False,
        "phase_conjugation_node": (
            "SOURCE_PROVENANCE_LANGUAGE_UNTIL_MEASURED; engineering "
            "translation is a candidate internal field/stress/"
            "polarization singularity, caustic, antinode or "
            "mode-conversion point, and no such point is claimed to "
            "exist until a solver or measurement locates one"),
        "verdict": "R10_34_CRYSTAL_60_120_SINGULARITY_LANE_READY",
    }
