"""R10.9 historical header-table recovery (Phase 2, R109-HDR-01/02).

Search result (2026-07-27, full evidence in
``docs/r109/evidence/R10_9_HEADER_TABLE_RECOVERY.md``): the primary
historical header list ``3,5,6,7,8,9,10,12,15`` appears NOWHERE in the
repository working tree, in any commit of git history (``git grep`` +
``git log -S`` over ``--all``), or in the operator archive area
(``internal-docs/``, including every zipped prompt pack) EXCEPT the
R10.9 prompt pack itself. Its archived binary interpretation therefore
CANNOT be recovered from project history.

Per the spec ("If the header semantics cannot be recovered, return an
explicit alias set rather than inventing labels"), this module exposes
the list as typed UNRESOLVED aliases: exact binary renderings are
provided (deterministic arithmetic), semantics are explicitly unknown,
and NO labels are invented.

The larger list ``5,7,24,27,28,48,54,57,64,75,97`` is quarantined as
the frequency-channel/key list: :func:`assert_not_header` refuses any
attempt to feed it into header parsing.
"""

from __future__ import annotations

from dataclasses import dataclass

PRIMARY_HEADER_LIST = (3, 5, 6, 7, 8, 9, 10, 12, 15)
FREQUENCY_KEY_LIST = (5, 7, 24, 27, 28, 48, 54, 57, 64, 75, 97)

RECOVERY_STATUS = "NOT_RECOVERED_FROM_HISTORY"
RECOVERY_EVIDENCE = (
    "searched: integration repo working tree; git grep across all "
    "refs; git log -S pickaxe over --all; the sibling RGCS checkout; "
    "internal-docs/ operator archives including every plans-v5 zip. "
    "Only occurrences: the R10.9 prompt pack files themselves."
)


class HeaderError(ValueError):
    pass


@dataclass(frozen=True)
class HeaderAlias:
    """One primary-list value as an explicit UNRESOLVED alias."""

    value: int
    binary4: str
    binary5: str
    binary6: str
    semantics: str = "UNKNOWN — not invented (R109-HDR-01)"
    evidence_class: str = "UNRESOLVED"


def alias_set() -> tuple[HeaderAlias, ...]:
    """Exact binary renderings at plausible field widths (4/5/6 bits);
    widths are renderings, NOT a recovered structure claim."""
    return tuple(
        HeaderAlias(v, format(v, "04b"), format(v, "05b"), format(v, "06b"))
        for v in PRIMARY_HEADER_LIST)


#: Source-reported group/body codes — typed, never parsed from wire
#: values (no transport-header width exists to parse them with).
SOURCE_REPORTED_GROUP_CODES = {
    "16": "Sol members in the GFW/intergalactic-federation group",
    "16-5": "Terra",
    "16-7": "Luna",
}


def assert_not_header(values) -> None:
    """Quarantine: the frequency-key list can never enter the header
    parser (R109-HDR-02)."""
    vals = set(int(v) for v in values)
    if vals & (set(FREQUENCY_KEY_LIST) - set(PRIMARY_HEADER_LIST)):
        raise HeaderError(
            "refused: values from the frequency-channel/key list "
            f"{sorted(vals & set(FREQUENCY_KEY_LIST))} must not be used "
            "as the primary header table (R109-HDR-02)")


def parse_header_candidate(value: int) -> dict:
    """Typed header lookup: primary-list membership only; no invented
    semantics; frequency-key values refused."""
    assert_not_header([value])
    known = value in PRIMARY_HEADER_LIST
    return {
        "value": value,
        "in_primary_historical_list": known,
        "semantics": ("UNKNOWN — alias retained, not invented"
                      if known else "not in the primary historical list"),
        "recovery_status": RECOVERY_STATUS,
        "evidence_class": "UNRESOLVED",
    }


def recovery_receipt() -> dict:
    return {
        "schema": "rgcs.r109.header-recovery.v1",
        "primary_list": list(PRIMARY_HEADER_LIST),
        "frequency_key_list_quarantined": list(FREQUENCY_KEY_LIST),
        "status": RECOVERY_STATUS,
        "evidence": RECOVERY_EVIDENCE,
        "aliases": [a.__dict__ for a in alias_set()],
        "source_reported_group_codes": SOURCE_REPORTED_GROUP_CODES,
        "chronology": [
            {"date": "2026-07-26", "event":
                "federation group / node 23 provenance recorded in the "
                "private operator area (internal-docs, untracked)"},
            {"date": "2026-07-27", "event":
                "R10.9 pack names the primary historical header list; "
                "repo+history+archive search finds no earlier "
                "interpretation; list stored as explicit UNRESOLVED "
                "alias set"},
        ],
    }
