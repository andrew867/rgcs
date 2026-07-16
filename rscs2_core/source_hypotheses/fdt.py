"""FDT external-theory adapter and falsification harness (Agent M13;
source SRC-V4-18, equations RGCS-V4-EQ-008/009).

The theory is preserved faithfully enough to AUDIT and TEST — never
endorsed, never repaired, never imported by default solvers. Every
output carries classification SOURCE_HYPOTHESIS and tags SRC/HYP.
The equations and claims are taken from the pack's enumeration
(the essay file was not supplied locally, DV4C-003)."""

from __future__ import annotations

import math

C_M_S = 299_792_458.0
G_SI = 6.67430e-11
CLASSIFICATION = "SOURCE_HYPOTHESIS"
EVIDENCE_TAGS = ("SRC", "HYP")

#: typed claim records (pack enumeration; no local essay file)
CLAIMS = {
    "force_relation": {
        "expression": "F = c^4/(4G) * alpha1 * alpha2",
        "kind": "equation", "executable_for_audit": True},
    "alpha_r_map": {
        "expression": "alpha_R = (n^2 - 1)/n^2",
        "kind": "equation", "executable_for_audit": True},
    "carrier_identity": {
        "expression": "proposed carrier identity (text claim)",
        "kind": "text_only", "executable_for_audit": False,
        "note": "retained as typed hypothesis; NEVER executable "
                "equivalence"},
    "cone_position_mass_mapping": {
        "expression": "cone-position and mass mappings",
        "kind": "text_only", "executable_for_audit": False},
    "bounded_alignment_map": {
        "expression": "bounded alignment map", "kind": "map",
        "executable_for_audit": True},
    "isotope_pressure_temperature_equivalence": {
        "expression": "isotope, pressure, temperature equivalences",
        "kind": "claim", "executable_for_audit": False},
    "iome_path_integral": {
        "expression": "proposed IOME path integral",
        "kind": "claim", "executable_for_audit": False},
}


def force_relation(alpha1: float, alpha2: float) -> dict:
    """Audit-only evaluation of F = c^4/(4G) a1 a2. Returns a
    quarantined record; never enters any solver."""
    coeff = C_M_S ** 4 / (4.0 * G_SI)
    return {"classification": CLASSIFICATION,
            "evidence_tags": list(EVIDENCE_TAGS),
            "F_newton_if_alphas_dimensionless": coeff * alpha1 * alpha2,
            "coefficient_newton": coeff,
            "audit_note": "coefficient ~3.03e43 N; the theory "
                          "supplies no independent normalization for "
                          "alpha — recorded as a dimensional gap"}


def alpha_r(n: float) -> float:
    if n < 1.0:
        raise ValueError("n >= 1 required")
    return (n * n - 1.0) / (n * n)


def alpha_r_inverse(a: float) -> float:
    if not (0.0 <= a < 1.0):
        raise ValueError("alpha_R in [0, 1) required")
    return math.sqrt(1.0 / (1.0 - a))


def dimensional_audit() -> dict:
    """Base dimensions, hidden constants, unresolved gaps."""
    return {
        "classification": CLASSIFICATION,
        "force_relation": {
            "coefficient": "c^4/(4G) = 3.026e43 N (SI exact inputs)",
            "alphas": "dimensionless by declaration",
            "gaps": ["no independent measurement fixes alpha's scale",
                     "no declared domain for alpha1*alpha2",
                     "normalization choice absorbs all magnitude "
                     "freedom"]},
        "alpha_r_map": {
            "dimensions": "dimensionless in, dimensionless out",
            "range": "n in [1, inf) -> alpha_R in [0, 1)",
            "gaps": ["which n (phase/group/complex?) is unspecified"]},
        "unresolved_inconsistencies": [
            "isotope/pressure/temperature 'equivalence' lacks units "
            "of exchange between the three axes"],
    }


def algebraic_audit() -> dict:
    """Invertible reparameterizations and tautology risks."""
    # demonstrate invertibility numerically (monotone bijection)
    ns = [1.0, 1.2, 1.5443, 2.0, 4.0]
    round_trip = max(abs(alpha_r_inverse(alpha_r(n)) - n)
                     for n in ns)
    return {
        "classification": CLASSIFICATION,
        "alpha_r_is_invertible_bijection": round_trip < 1e-12,
        "consequence": "alpha_R is an invertible reparameterization "
                       "of n; INVERTIBILITY ALONE ADDS NO EVIDENCE — "
                       "any statement true in n is restatable in "
                       "alpha_R without new physical content",
        "tautology_risks": ["fitting alpha_R to index data and "
                            "reporting agreement with index data",
                            "using the same source data as both fit "
                            "and validation"],
        "hidden_fit_function_flags": ["any undeclared monotone map "
                                      "inserted between alpha and an "
                                      "observable"],
    }


def empirical_audit() -> dict:
    """Claim -> data status map. No local FDT data exists; the Toyoda
    experiment is NOT usable as confirmation (frozen rule)."""
    return {
        "classification": CLASSIFICATION,
        "claims": {
            "wavelength_thresholds_near_dd_bands": {
                "status": "PREDICTION_PENDING",
                "conventional_comparator": "resonant absorption "
                "(Lorentz + Kramers-Kronig)"},
            "bounded_saturation": {
                "status": "UNDERDETERMINED",
                "conventional_comparator": "tanh/logistic bounded "
                "domain-population laws (M11, held-out compared)"},
            "nickel_isotope_sign_test": {
                "status": "NO_LOCAL_DATA",
                "conventional_comparator": "material-specific isotope "
                "effects on exchange/anisotropy"},
            "pressure_co_sign_test": {"status": "NO_LOCAL_DATA",
                                      "conventional_comparator":
                                      "pressure-dependent exchange"},
            "real_index_partner": {
                "status": "PREDICTION_PENDING",
                "conventional_comparator": "KK-consistent dispersive "
                "channel of the directional index (M11 EQ-003 Re)"},
            "index_linked_domain_scale": {
                "status": "PREDICTION_PENDING",
                "conventional_comparator": "domain-wall energetics"},
        },
        "toyoda_usage": "SRC-V4-01 may not be cited as confirmation "
                        "of FDT universal claims (frozen rule; "
                        "no fabricated confirmation)",
    }


def prediction_registry() -> list[dict]:
    """Pre-registered discriminators with interpretations for
    positive, null, and opposite-sign outcomes — no outcome is
    permitted to be spun."""
    def entry(name, observable, positive, null, opposite):
        return {"prediction_id": f"FDT-P-{name}",
                "classification": CLASSIFICATION,
                "observable": observable,
                "if_positive": positive,
                "if_null": null,
                "if_opposite_sign": opposite}
    shared_null = ("FDT variant disfavored; conventional model "
                   "stands; record and stop")
    shared_pos = ("consistent with BOTH FDT and the conventional "
                  "comparator unless the comparator is excluded; "
                  "no exclusive confirmation may be claimed")
    return [
        entry("nickel-isotope-sign", "sign of writing bias vs Ni "
              "isotope substitution", shared_pos, shared_null,
              "contradicts the FDT sign mapping; falsified variant"),
        entry("pressure-co-sign", "bias sign under hydrostatic "
              "pressure", shared_pos, shared_null,
              "contradicts FDT co-sign claim"),
        entry("wavelength-thresholds", "writing efficiency vs "
              "wavelength near d-d bands", shared_pos, shared_null,
              "spectral inversion contradicts the mapping"),
        entry("bounded-saturation", "alignment saturation form",
              shared_pos, shared_null, "unbounded response falsifies "
              "both FDT and conventional bounded laws"),
        entry("real-index-partner", "beam deflection / dispersive "
              "partner of the optical diode", shared_pos, shared_null,
              "sign-reversed dispersion contradicts the KK pairing "
              "FDT asserts"),
        entry("index-linked-domain-scale", "minimum written domain "
              "size vs index contrast", shared_pos, shared_null,
              "inverse scaling contradicts the claim"),
    ]


FORBIDDEN_CONCLUSION_PHRASES = (
    "fdt is confirmed", "proves the fdt", "universal force law",
    "no alternative explanation", "establishes the carrier identity",
    "fdt explains all")


def conclusion_linter(text: str) -> list[str]:
    """Reject universal-completeness wording in public conclusions."""
    low = text.lower()
    return [p for p in FORBIDDEN_CONCLUSION_PHRASES if p in low]
