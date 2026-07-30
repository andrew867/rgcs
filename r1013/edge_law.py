"""R10.13 Phase 30 — state-dependent edge-law hypothesis registry.

The GLOBAL 10/9 edge law was tested and rejected (R10.11F-A). What
remains active is the source-approved BASE odds ratio 10/9 modified by
a bounded modifier family:

    r_e = (10/9) * M(phi_tor, phi_pol, phi_rad, c, e, sigma)
    t_e = r_e / (1 + r_e)

No modifier law is selected: selection requires held-out improvement,
and no held-out labels exist (sealed holdouts stay sealed). The
nonlinear radial "sundial" table and the 15-degrees-per-unit phase
clue are preserved as UNRESOLVED source clues, not implemented as
active mappings.
"""

from __future__ import annotations

from fractions import Fraction

from r1013.errors import UserError

BASE_ODDS = Fraction(10, 9)

#: Bounded, declared modifier families. ALL UNDERDETERMINED.
MODIFIER_FAMILIES = (
    {"id": "M0_IDENTITY", "form": "M = 1 (state-independent)",
     "status": "REJECTED_GLOBAL",
     "note": "the global 10/9 law was tested against the exact "
             "operator and rejected (R10.11F-A)"},
    {"id": "M1_TOR_LINEAR", "form": "M = 1 + a*phi_tor/63",
     "status": "UNDERDETERMINED"},
    {"id": "M2_POL_LINEAR", "form": "M = 1 + b*phi_pol/63",
     "status": "UNDERDETERMINED"},
    {"id": "M3_RAD_SUNDIAL", "form": "M = f_sundial(phi_rad); "
     "nonlinear table, 15-degrees-per-unit clue",
     "status": "UNRESOLVED_SOURCE_CLUE",
     "note": "the sundial table itself is not recovered; the 15 "
             "degree step is a clue, not a mapping"},
    {"id": "M4_CHILD_INDEXED", "form": "M = m_c per child c",
     "status": "UNDERDETERMINED"},
    {"id": "M5_EDGE_CLASS", "form": "M = m_e per edge class e",
     "status": "UNDERDETERMINED"},
    {"id": "M6_SIDE", "form": "M = m_sigma per refinement side "
     "(left/right)", "status": "UNDERDETERMINED"},
)

SELECTION_RULE = ("a modifier family may be selected ONLY on "
                  "out-of-sample improvement against held-out data "
                  "that was never used for fitting; no such data is "
                  "available, so no family is selected")


def registry() -> dict:
    return {"schema": "rgcs.r1013.edge-law.v1",
            "base_odds": [BASE_ODDS.numerator, BASE_ODDS.denominator],
            "base_edge_fraction": float(BASE_ODDS / (1 + BASE_ODDS)),
            "families": list(MODIFIER_FAMILIES),
            "selection_rule": SELECTION_RULE,
            "selected": None,
            "evidence_class": "SOURCE_PROVENANCE_ONLY"}


def edge_fraction(modifier: float = 1.0) -> dict:
    """t_e for a HYPOTHETICAL modifier value. Marked conditional;
    passing modifier != 1 does not select a law."""
    if modifier <= 0:
        raise UserError("RGCS-E005", "modifier must be positive")
    r = float(BASE_ODDS) * modifier
    return {"odds_ratio": r, "edge_fraction": r / (1 + r),
            "conditional_on": "hypothetical modifier value; no law is "
                              "selected", "modifier": modifier}


def select_law(family_id: str) -> dict:
    """Selecting a law refuses without held-out improvement."""
    ids = [f["id"] for f in MODIFIER_FAMILIES]
    if family_id not in ids:
        raise UserError("RGCS-E006", f"unknown family '{family_id}'; "
                        f"declared families: {', '.join(ids)}")
    raise UserError("RGCS-E013",
                    f"selection of '{family_id}' refused: {SELECTION_RULE}.")
