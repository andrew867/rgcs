"""R10.9 machine-readable authority registry (Phase 1).

Every lock from ``01_AUTHORITY/LOCKED_SOURCE_AND_OPERATOR_UPDATES.md``
(prompt pack 2026-07-27), stored with an explicit evidence class.
Source-reported wording is NEVER converted into established physical
fact; superseded interpretations are retained, not deleted.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict

EVIDENCE_CLASSES = (
    "SOURCE_REPORTED",       # wording attributed by AG to The L's
    "OPERATOR_NOTE",         # AG's own interpretation or recollection
    "EXACT_ARITHMETIC",      # deterministic conversion or identity
    "SOFTWARE_RESULT",       # output of a named implementation
    "CALIBRATED_CANDIDATE",  # fitted model, not independent validation
    "HOLDOUT_RESULT",        # frozen prediction evaluated after reveal
    "UNRESOLVED",            # insufficient information
    "SUPERSEDED",            # retained historical interpretation
)


class AuthorityError(ValueError):
    """An authority entry violates the registry contract."""


@dataclass(frozen=True)
class AuthorityEntry:
    authority_id: str
    wording: str
    source: str                       # "source(L's) via AG", "operator(AG)", "pack 2026-07-27", ...
    evidence_class: str
    timestamp: str = "2026-07-27"     # pack date unless a finer time is known
    supersedes: tuple[str, ...] = ()
    superseded_by: str | None = None
    affected_modules: tuple[str, ...] = ()
    affected_tests: tuple[str, ...] = ()
    notes: str = ""

    def __post_init__(self) -> None:
        if self.evidence_class not in EVIDENCE_CLASSES:
            raise AuthorityError(
                f"{self.authority_id}: unknown evidence class "
                f"{self.evidence_class!r}")
        if not self.wording:
            raise AuthorityError(f"{self.authority_id}: empty wording")

    def to_dict(self) -> dict:
        return asdict(self)


ENTRIES: tuple[AuthorityEntry, ...] = (
    # ------------------------------------------------ packet locks
    AuthorityEntry(
        "R109-PKT-01",
        "Decimal wire values are converted to binary/octal before spatial decoding.",
        "source(L's) via AG, pack 2026-07-27", "SOURCE_REPORTED",
        affected_modules=("r109.codec",),
    ),
    AuthorityEntry(
        "R109-PKT-02",
        "The compact nine-digit family retains the 30-bit packet F5|Q22|S3.",
        "pack 2026-07-27; reproduced by rgcs_coordinate.codecs.federation_terra_30",
        "EXACT_ARITHMETIC",
        affected_modules=("rgcs_coordinate.codecs.federation_terra_30", "r109.codec"),
        affected_tests=("tests/rgcs_coordinate", "tests/r109/test_t10.py"),
    ),
    AuthorityEntry(
        "R109-PKT-03",
        "Ten octal digits are the compact family (T10); eleven octal digits add "
        "one recursive surface-refinement level (T11).",
        "source(L's) via AG, pack 2026-07-27", "SOURCE_REPORTED",
        affected_modules=("r109.codec",),
        affected_tests=("tests/r109/test_t10.py", "tests/r109/test_t11.py"),
    ),
    AuthorityEntry(
        "R109-PKT-04",
        "The added child digit is at the end of the recursive path, before shell "
        "and epoch semantics.",
        "source(L's) via AG, pack 2026-07-27", "SOURCE_REPORTED",
        affected_modules=("r109.t11_candidates",),
    ),
    AuthorityEntry(
        "R109-PKT-05",
        "The eleven-digit family uses a different interleave from the compact "
        "family; similar but not identical. The exact T11 interleave is NOT yet "
        "known and must not be invented.",
        "source(L's) via AG, pack 2026-07-27", "UNRESOLVED",
        affected_modules=("r109.t11_candidates",),
        notes="Finite candidate registry only; aliases reported, none promoted.",
    ),
    AuthorityEntry(
        "R109-PKT-06",
        "A refined address must be contained by its compact parent: "
        "Omega(refined) subset Omega(parent). Extra length refines the surface "
        "cell; it does not primarily encode crust depth.",
        "source(L's) via AG, pack 2026-07-27", "SOURCE_REPORTED",
        affected_tests=("tests/r109/test_t11.py",),
    ),
    AuthorityEntry(
        "R109-PKT-07",
        "The fixed and long forms of Stonehenge (165876523 / 1643789253) and "
        "Toronto (168930443 / 1672875493) are the same physical addresses at "
        "different precision.",
        "source(L's) via AG, pack 2026-07-27", "SOURCE_REPORTED",
        affected_tests=("tests/r109/test_t11.py",),
    ),
    # ------------------------------------------------ group and body
    AuthorityEntry(
        "R109-GRP-01",
        "16 = Sol members in the GFW/intergalactic-federation group; "
        "16-5 = Terra; 16-7 = Luna.",
        "source(L's) via AG, pack 2026-07-27", "SOURCE_REPORTED",
        affected_modules=("r109.types",),
        notes="Typed values only; the exact numeric group ID's wire encoding "
              "remains unknown; no transport-header width invented.",
    ),
    AuthorityEntry(
        "R109-HDR-01",
        "Primary historical header list = 3,5,6,7,8,9,10,12,15; recover its "
        "archived binary interpretation first from project history.",
        "source(L's) via AG + operator(AG), pack 2026-07-27", "OPERATOR_NOTE",
        affected_modules=("r109.header_recovery",),
        affected_tests=("tests/r109/test_headers.py",),
    ),
    AuthorityEntry(
        "R109-HDR-02",
        "The larger list 5,7,24,27,28,48,54,57,64,75,97 is a frequency-"
        "channel/key list and must not be used as the primary header table.",
        "source(L's) via AG, pack 2026-07-27", "SOURCE_REPORTED",
        affected_modules=("r109.header_recovery",),
        affected_tests=("tests/r109/test_headers.py",),
    ),
    # ------------------------------------------------ face and node
    AuthorityEntry(
        "R109-FACE-01",
        "node 23 = six-bit 64-state face/node selector; Stonehenge top-six "
        "state = 9; 23 - 9 = 14; source_face = (F5 + 14) mod 20.",
        "source(L's) via AG; arithmetic reproduced", "EXACT_ARITHMETIC",
        affected_modules=("r109.face_node",),
        affected_tests=("tests/r109/test_face_node.py",),
        notes="The identity is exact arithmetic; its physical meaning stays "
              "source-reported.",
    ),
    AuthorityEntry(
        "R109-FACE-02",
        "Physical face numbering: root feature Wilkes face; routing graph "
        "dodecahedral dual; order clockwise; phase zero = SAA direction.",
        "source(L's) via AG, pack 2026-07-27", "SOURCE_REPORTED",
        affected_modules=("r109.face_node", "cwatlas.r1082.wilkes", "cwatlas.r1082.saa"),
    ),
    AuthorityEntry(
        "R109-FACE-03",
        "Literal five-bit F5=23 does not exist (F5 max 31, faces 20..31 "
        "reserved); face 23 as a literal packet face remains refused.",
        "pack 2026-07-27 + frozen parser behavior", "EXACT_ARITHMETIC",
        affected_modules=("rgcs_coordinate.codecs.federation_terra_30",),
        affected_tests=("tests/r109/test_face_node.py",),
    ),
    # ------------------------------------------------ shells
    AuthorityEntry(
        "R109-SHL-01",
        "S3 is the physical shell field; shell 3 contains the crustal surface "
        "as a finite body-relative band (sea floor, land, mountains occupy "
        "variable depth within it); shell 7 is an orbital object class; shell "
        "thickness differs by planet.",
        "source(L's) via AG, pack 2026-07-27", "SOURCE_REPORTED",
        affected_modules=("r109.shell_semantics", "cwatlas.r1085a.shell_profile"),
        affected_tests=("tests/r109/test_shells.py",),
    ),
    AuthorityEntry(
        "R109-SHL-02",
        "A source wire ending in decimal 3 is reported as a surface object; "
        "ending in decimal 7 as an object in orbit. The decimal terminal "
        "marker is preserved SEPARATELY from parsed binary S3 until their "
        "exact relationship is proved.",
        "source(L's) via AG, pack 2026-07-27", "SOURCE_REPORTED",
        affected_modules=("r109.types", "r109.shell_semantics"),
        affected_tests=("tests/r109/test_shells.py",),
    ),
    AuthorityEntry(
        "R109-SHL-03",
        "The current outer-in shell-fraction equation remains provisional "
        "production authority (cwatlas.r1085a.outer_in_radial).",
        "operator(AG), pack 2026-07-27", "OPERATOR_NOTE",
        affected_modules=("cwatlas.r1085a.outer_in_radial",),
    ),
    # ------------------------------------------------ Montréal correction
    AuthorityEntry(
        "R109-MTL-01",
        "The current source-reported Montréal vector is the DIRECT compact "
        "packet 165879243 (binary30 001001111000110001110111001011, octal10 "
        "1170616713, F5=4, path 3,3,0,1,2,0,3,2,3,2,1, S3=3).",
        "source(L's) via AG, pack 2026-07-27; arithmetic reproduced",
        "EXACT_ARITHMETIC",
        supersedes=("R109-MTL-02-SUPERSEDED", "R109-MTL-03-SUPERSEDED"),
        affected_modules=("r109.registry",),
        affected_tests=("tests/r109/test_montreal.py",),
        notes="Structural decode is exact arithmetic; the LOCATION attribution "
              "remains source-reported.",
    ),
    AuthorityEntry(
        "R109-MTL-02-SUPERSEDED",
        "The bridge 165879243 -> 168500683 (general affine "
        "y=(923*x+550585316) mod 2^30) is superseded and is not current "
        "authority; preserved as a historical model.",
        "pack 2026-07-27", "SUPERSEDED",
        superseded_by="R109-MTL-01",
        affected_modules=("r109.superseded",),
        affected_tests=("tests/r109/test_stale_models.py",),
    ),
    AuthorityEntry(
        "R109-MTL-03-SUPERSEDED",
        "The older Montréal transcription 168729543 is preserved as superseded "
        "provenance and is not the current Montréal packet.",
        "pack 2026-07-27", "SUPERSEDED",
        superseded_by="R109-MTL-01",
        affected_modules=("r109.registry",),
        affected_tests=("tests/r109/test_stale_models.py",),
    ),
    # ------------------------------------------------ earth alignment + holdout
    AuthorityEntry(
        "R109-EAR-01",
        "The existing nonlinear Earth operator is preserved as "
        "EARTH_ALIGNMENT_V1_LEGACY_CALIBRATED; a new candidate "
        "EARTH_ALIGNMENT_V2_MONTREAL_DIRECT is built from Wilkes root, SAA "
        "phase, Stonehenge 165876523, Erie 167849523, Montréal 165879243, "
        "Toronto 168930443, and the orange-slice plane constraint.",
        "pack 2026-07-27", "CALIBRATED_CANDIDATE",
        affected_modules=("r109.earth_v2",),
        affected_tests=("tests/r109/test_earth_v2.py",),
    ),
    AuthorityEntry(
        "R109-HLD-01",
        "167854923 is a frozen blind holdout with its existing V1 blind "
        "receipt and candidate Ohio output; no retuning of V2 to move that "
        "result; Newfoundland records and the corrupted Gander/Argentia "
        "collision (1658792343) are excluded from fitting.",
        "pack 2026-07-27", "OPERATOR_NOTE",
        affected_modules=("r109.registry", "r109.earth_v2"),
        affected_tests=("tests/r109/test_stale_models.py",),
    ),
    # ------------------------------------------------ publication
    AuthorityEntry(
        "R109-PUB-01",
        "The manuscript, package, and repository remain private and "
        "unpublished; no tag, push, release, merge to public main, manuscript "
        "submission, or public claim is authorized in this phase.",
        "operator(AG), pack 2026-07-27", "OPERATOR_NOTE",
    ),
)

_BY_ID = {e.authority_id: e for e in ENTRIES}


def entry(authority_id: str) -> AuthorityEntry:
    try:
        return _BY_ID[authority_id]
    except KeyError:
        raise AuthorityError(f"unknown authority id {authority_id!r}") from None


def registry_dict() -> dict:
    return {
        "schema": "rgcs.r109.authority-registry.v1",
        "pack": "RGCS_R10_9_Variable_Depth_Octal_Codec_Integration_Prompt_Pack_2026-07-27",
        "evidence_classes": list(EVIDENCE_CLASSES),
        "entries": [e.to_dict() for e in ENTRIES],
    }


def validate() -> dict:
    """Cross-check supersedes links and evidence classes."""
    for e in ENTRIES:
        for sid in e.supersedes:
            if sid not in _BY_ID:
                raise AuthorityError(f"{e.authority_id} supersedes unknown {sid}")
            if _BY_ID[sid].evidence_class != "SUPERSEDED":
                raise AuthorityError(
                    f"{e.authority_id} supersedes {sid}, which is not marked "
                    f"SUPERSEDED")
        if e.superseded_by and e.superseded_by not in _BY_ID:
            raise AuthorityError(
                f"{e.authority_id} superseded_by unknown {e.superseded_by}")
    return {"entries": len(ENTRIES), "valid": True}
