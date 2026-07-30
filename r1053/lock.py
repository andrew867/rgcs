"""R10.53 -- the V1 lock: verdicts, corrections, and every open blocker.

A verdict here states what was IMPLEMENTED and LOCKED, never what was
proven. The pack draws that boundary itself and this module keeps it:
``R10_53_V1_CANDIDATE_NOT_FINAL_PHYSICAL_VALIDATION`` is a required
verdict, so a green V1 and an unvalidated projector are consistent
states, not a contradiction.
"""

from __future__ import annotations

from r1028 import acceptance, staged
from r1053 import kernel, ledger, projector, residuals

NOT_FINAL_PHYSICAL_VALIDATION = True

VERDICTS = (
    "R10_53_V1_EARTH_ROOT_ALIGNMENT_OPERATIONAL",
    "R10_53_DIRECT_9DIGIT_OCTAL_LANE_LOCKED",
    "R10_53_FIXED_ROOT_STAGED_PARSER_LOCKED",
    "R10_53_SOURCE_RATIO_10_19_PROJECTOR_LOCKED_AS_V1",
    "R10_53_DRUMMONDVILLE_RELABEL_APPLIED",
    "R10_53_MONTREAL_LABEL_RETIRED_TO_HINT_PROVENANCE",
    "R10_53_WIDE_ENVELOPE_SLEEP_BATCH_GATED",
    "R10_53_WATER_ACCEPTANCE_READY_NOT_SCOREABLE_WITHOUT_COASTLINE",
    "R10_53_V1_CANDIDATE_NOT_FINAL_PHYSICAL_VALIDATION",
)

#: The eleven non-negotiable corrections, each bound to what enforces it.
CORRECTIONS = {
    1: ("9-digit direct words are NOT 16|payload|3",
        "r1053.kernel.assert_direct_lane"),
    2: ("direct words decode by binary/octal path first",
        "r1053.kernel.fields / octal10"),
    3: ("decimal header table scoped to wide-envelope records",
        "r1053.kernel.decimal_header_table_applies"),
    4: ("fixed root is 4 bits, zero-padded",
        "r1028.staged.ROOT_FIXED / ROOT_BITS"),
    5: ("section and path are maximum envelopes, not fixed fields",
        "r1028.staged.legal_splits"),
    6: ("at least one unit from the 8-bit section and one from the "
        "12-bit path", "r1028.staged.SECTION_MIN / PATH_MIN"),
    7: ("section splits into layer2 plus optional layer3",
        "r1028.staged.section_layers"),
    8: ("level-3 datum is mean sea level",
        "r1028.acceptance.LEVEL3_DATUM"),
    9: ("water acceptance implemented, scoreable only with coordinates "
        "and a coastline dataset", "r1028.acceptance.readiness"),
    10: ("M3 kept distinct from the decimal terminal",
         "r1053.kernel.fields returns S3 separately; not used in geometry"),
    11: ("no direct-Montreal contamination",
         "r1053.ledger.RETIRED_LABELS may_fit_projector = False"),
}

#: Open blockers. Every one of these is a real, stated limit on V1.
BLOCKERS = {
    "V1-B01": {
        "title": "the pack's projected coordinates are not reproducible "
                 "from the law as stated",
        "detail": "A retains two free parameters at three anchors. Every "
                  "member of that family fits all three anchors to "
                  "machine precision and sends a non-anchor word "
                  "thousands of km apart. The pack's outputs are one "
                  "member; this repo's recorded pinning selects another. "
                  "Measured gap for the four V1 targets: 177 km to "
                  "5122 km. The two members disagree about which "
                  "CONTINENT 165879243 addresses -- and the repo's "
                  "pinning is the one that agrees with octal branch 117, "
                  "landing all four words in southern England.",
        "clears_when": "a pinning rule is recorded upstream, OR a 4th "
                       "and 5th independent anchor arrive",
        "severity": "STRUCTURAL",
    },
    "V1-B02": {
        "title": "three anchors cannot test the projector",
        "detail": "8 free parameters against 6 constraints. Anchor "
                  "residual 0.0 km is guaranteed by construction. Five "
                  "anchors is the threshold at which A first becomes "
                  "over-determined; four is still exactly determined.",
        "clears_when": ">=5 independently sourced hard anchors",
        "severity": "STRUCTURAL",
    },
    "V1-B03": {
        "title": "165879243 sits in octal branch 117 (British) while its "
                 "working label is in Quebec",
        "detail": "the 117/120 branch partition separates Britain from "
                  "North America across the whole labelled corpus with "
                  "no crossovers. Relabelling Montreal to Drummondville "
                  "does not move the wire between branches, so the "
                  "conflict carried over from R10.44 B002 is unchanged.",
        "clears_when": "either an independent coordinate for 165879243, "
                       "or a demonstrated crossover that breaks the "
                       "partition",
        "severity": "STRUCTURAL",
    },
    "V1-B04": {
        "title": "the cell-scale reading of the 15.7 km residual is n=1",
        "detail": "the depth ladder is geometric with ratio 2, so at the "
                  "+/-30%% tolerance the reading was first stated with, "
                  "88%% of residuals under 60 km qualify. The observed "
                  "residual is tight (within 4.6%% of one depth-9 edge) "
                  "but it is a single observation against a six-rung "
                  "ladder.",
        "clears_when": "the same cell-scale offset appears for >=3 "
                       "independent non-anchor words",
        "severity": "EVIDENTIAL",
    },
    "V1-B05": {
        "title": "water acceptance cannot score",
        "detail": "no coastline dataset in this environment, and the "
                  "criterion needs decoded coordinates from a projector "
                  "that is not yet determined. The 71%% Earth-water "
                  "baseline must be beaten, not merely met.",
        "clears_when": "a coastline dataset is present AND the projector "
                       "clears V1-B01/B02",
        "severity": "OPERATIONAL",
    },
    "V1-B06": {
        "title": "Rue Saint-Frederic corridor is a proxy, not a geocode",
        "detail": "the pack supplies 45.883,-72.486 as a proxy pending "
                  "the exact civic point. It is also an OBSERVER "
                  "location, so scoring a projected object position "
                  "against it is a category difference, not a residual.",
        "clears_when": "an exact civic geocode is supplied and the "
                       "observer/object distinction is settled",
        "severity": "OPERATIONAL",
    },
    "V1-B07": {
        "title": "the wide-envelope batch has no bridge",
        "detail": "the seven 11-13 digit records exceed 30 bits and "
                  "cannot enter the direct lane. The affine transport "
                  "bridge was REFUTED at R10.47C by the third labelled "
                  "pair, and no replacement exists.",
        "clears_when": "a transport bridge that reproduces all three "
                       "labelled pairs",
        "severity": "STRUCTURAL",
    },
}


def correction_status() -> dict:
    """Each correction, with the check that actually enforces it run."""
    checks = {
        1: lambda: not kernel.decimal_header_table_applies(165879243),
        2: lambda: kernel.octal10(165879243) == "1170616713",
        3: lambda: all(kernel.decimal_header_table_applies(w)
                       for w in ledger.GATED_WIDE_ENVELOPE),
        4: lambda: staged.ROOT_FIXED and staged.ROOT_BITS == 4,
        5: lambda: len(staged.legal_splits(30)) > 1,
        6: lambda: staged.SECTION_MIN >= 1 and staged.PATH_MIN >= 3,
        7: lambda: any(r["level3_present"]
                       for r in staged.section_layers(0b10110101, 8)),
        8: lambda: acceptance.LEVEL3_DATUM == "MEAN_SEA_LEVEL",
        9: lambda: acceptance.readiness()["criterion_defined"]
        and not acceptance.readiness()["scoreable_now"],
        10: lambda: kernel.fields(165879243)[2] == 165879243 & 7,
        11: lambda: not ledger.RETIRED_LABELS["165879243"]["may_fit_projector"],
    }
    rows = []
    for n, (text, enforced_by) in CORRECTIONS.items():
        rows.append({"correction": n, "requirement": text,
                     "enforced_by": enforced_by, "holds": bool(checks[n]())})
    return {"schema": "rgcs.r1053.corrections.v1", "rows": rows,
            "all_hold": all(r["holds"] for r in rows)}


def water_acceptance_status() -> dict:
    """CORRECTION 9 / verdict 8: implemented, not scoreable."""
    r = acceptance.readiness()
    scored = acceptance.water_criterion(
        [{"vector": v, "over_water": None} for v in ledger.V1_PROJECTED])
    return {
        "schema": "rgcs.r1053.water-acceptance.v1",
        "datum": acceptance.LEVEL3_DATUM,
        "criterion_implemented": True,
        "scoreable_now": r["scoreable_now"],
        "land_water_mask_present": r["land_water_mask_present"],
        "baseline_to_beat": r["baseline_to_beat"],
        "attempted_score": scored,
        "verdict": "R10_53_WATER_ACCEPTANCE_READY_NOT_SCOREABLE_"
                   "WITHOUT_COASTLINE",
    }


def gate_status() -> dict:
    """CORRECTION 6 / task 6: the wide-envelope batch stays gated."""
    rows = []
    for w in ledger.GATED_WIDE_ENVELOPE:
        try:
            kernel.assert_direct_lane(w)
            admitted = True
        except kernel.DirectLaneError:
            admitted = False
        rows.append({"record": w, "digits": len(w),
                     "bits": int(w).bit_length(),
                     "admitted_to_direct_lane": admitted,
                     "gated": ledger.is_gated(w)})
    return {
        "schema": "rgcs.r1053.wide-envelope-gate.v1",
        "rows": rows,
        "all_gated": all(r["gated"] and not r["admitted_to_direct_lane"]
                         for r in rows),
        "bridge_status": staged.transport_bridge_status()["status"],
        "verdict": "R10_53_WIDE_ENVELOPE_SLEEP_BATCH_GATED",
    }


def relabel_status() -> dict:
    """Verdicts 5 and 6: the relabel applied, Montreal retired."""
    return {
        "schema": "rgcs.r1053.relabel.v1",
        "vector": "165879243",
        "active_label": ledger.active_label("165879243"),
        "retired": ledger.RETIRED_LABELS["165879243"],
        "relabel_applied": bool(ledger.active_label("165879243")),
        "montreal_retired_to_provenance":
            ledger.RETIRED_LABELS["165879243"]["status"]
            == "HINT_PROVENANCE_ONLY",
        "montreal_may_fit_projector":
            ledger.RETIRED_LABELS["165879243"]["may_fit_projector"],
        "blocked_labels": list(ledger.BLOCKED_LABELS),
        "label_rule": ledger.LABEL_RULE,
    }


def v1_lock_report() -> dict:
    """The whole V1 lock, verdicts and blockers together."""
    return {
        "schema": "rgcs.r1053.v1-lock.v1",
        "verdicts": list(VERDICTS),
        "not_final_physical_validation": NOT_FINAL_PHYSICAL_VALIDATION,
        "corrections": correction_status(),
        "projector": {
            "law": "lat/lon = normalize(A u); u from F5|Q22|S3 at "
                   "source_face=(F5+14)%20 with split t=10/19",
            "split_t": kernel.SPLIT_T,
            "pinning": projector.V1_PINNING,
            "underdetermination": projector.underdetermination_report(),
            "anchor_residuals": projector.anchor_residuals(),
        },
        "relabel": relabel_status(),
        "gate": gate_status(),
        "water": water_acceptance_status(),
        "scorecard": residuals.full_scorecard(),
        "blockers": BLOCKERS,
        "blocker_count": len(BLOCKERS),
        "structural_blockers": sorted(
            k for k, v in BLOCKERS.items() if v["severity"] == "STRUCTURAL"),
    }
