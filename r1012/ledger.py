"""R10.12 Phases 01+04 — correction ledger and artifact authority graph.

Nothing is deleted: every superseded interpretation is listed with its
successor, and the authority graph makes it machine-checkable that no
historical artifact silently becomes active (Phase 06 tests enforce).
"""

from __future__ import annotations

from r1012.evidence import Tier

CORRECTIONS = [
    {"id": "COR-01", "superseded": "E2 payload frame (2-bit lead)",
     "by": "E3 octal-aligned frame (3-bit lead; internal subdivision "
           "UNRESOLVED; source two-bit shell/epoch wording preserved)",
     "tier_of_old": Tier.HISTORICAL_ONLY},
    {"id": "COR-02", "superseded": "monolithic F5|Q22|S3 as final semantics",
     "by": "segmented 001|110|E3|S6|S6|S6|C3^d|M3 for the 16-headed family",
     "note": "old profile stays EXACT_OLD_STRUCTURAL_PROFILE — arithmetic "
             "valid, semantics historical",
     "tier_of_old": Tier.HISTORICAL_ONLY},
    {"id": "COR-03", "superseded": "1687425419853 (malformed transcription)",
     "by": "168742538943 (verified: depth 3, E3=6, states [32,56,7], "
           "children [1,0,6], terminal 3)",
     "tier_of_old": Tier.HISTORICAL_ONLY},
    {"id": "COR-04", "superseded": "batch verdict 27/28 + ONE_WIDTH_OVERFLOW",
     "by": "corrected batch 28/28 exact parses, 0 failures",
     "tier_of_old": Tier.HISTORICAL_ONLY},
    {"id": "COR-05", "superseded": "144000 as evidential match",
     "by": "PRIMED_RETROSPECTIVE_MATCH — associative/null-control only",
     "tier_of_old": Tier.UNSUPPORTED},
    {"id": "COR-06", "superseded": "627-step fitted Earth operator",
     "by": "analytic recursive construction (operator retraction, verbatim "
           "in R10.11F-A pack)", "tier_of_old": Tier.REVOKED},
    {"id": "COR-07", "superseded": "any 1200-step substitute operator",
     "by": "NOTHING — no such operator ever existed (V2 was 868-step, "
           "rejected for folding, FALSIFIED as a candidate)",
     "tier_of_old": Tier.FALSIFIED_FAMILY},
    {"id": "COR-08", "superseded": "publication status",
     "by": "HOLD (unchanged; restated)", "tier_of_old": Tier.SOURCE_KNOWN},
]

#: file/artifact -> (tier, superseded_by or None)
AUTHORITY_GRAPH = {
    "r1011/e3_frame.py": (Tier.SOURCE_KNOWN, None),
    "r1011/segmented_codec.py": (Tier.SOURCE_KNOWN, None),
    "r1011/gf2_affine.py": (Tier.CONDITIONAL_COMPLETION, None),
    "r1011/affine_envelope.py": (Tier.CONDITIONAL_COMPLETION, None),
    "r1011/probe_intake.py": (Tier.SOURCE_KNOWN, None),
    "docs/r1011/evidence/r1011fa/R10_11FA_INTAKE_PARSE_RECEIPT.json":
        (Tier.SOURCE_KNOWN, None),
    "rgcs_coordinate/codecs/federation_terra_30.py":
        (Tier.HISTORICAL_ONLY, "r1011/segmented_codec.py"),
    "docs/r109/earth_v1/RGCS_Earth_Alignment_Candidate_2026-07-26/"
    "operator/WARP_STEPS.json.gz": (Tier.REVOKED, "analytic construction"),
    "docs/r109/evidence/R10_9_EARTH_V2_WARP_STEPS.json.gz":
        (Tier.FALSIFIED_FAMILY, None),
    "docs/r1011/evidence/R10_11_NODE_LIFT_PARAMETERS.json":
        (Tier.HISTORICAL_ONLY, "analytic construction (fitted meshes "
                               "excluded by R10.11F-A)"),
    "r1011/flat_hedron.py": (Tier.HISTORICAL_ONLY, "r1012/geometry.py"),
    "cwatlas/geodesy.py": (Tier.SOURCE_KNOWN, None),
    "cwatlas/r1085a/shell_profile.py": (Tier.CONDITIONAL_COMPLETION, None),
}


def graph_dict() -> dict:
    return {
        "schema": "rgcs.r1012.authority-graph.v1",
        "corrections": [{**c, "tier_of_old": c["tier_of_old"].value}
                        for c in CORRECTIONS],
        "artifacts": {k: {"tier": t.value, "superseded_by": s}
                      for k, (t, s) in AUTHORITY_GRAPH.items()},
    }


def active_artifacts() -> list[str]:
    from r1012.evidence import ACTIVE_TIERS
    return [k for k, (t, _) in AUTHORITY_GRAPH.items() if t in ACTIVE_TIERS]


def revoked_artifacts() -> list[str]:
    return [k for k, (t, _) in AUTHORITY_GRAPH.items()
            if t in (Tier.REVOKED, Tier.HISTORICAL_ONLY,
                     Tier.FALSIFIED_FAMILY)]
