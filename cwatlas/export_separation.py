"""P55 — Privacy narrative versus public export separation.

A public export or audit bundle must carry **only** synthetic/public, redacted
content. Private narrative, source attributions, predictions, personal
locations, and raw vector strings never cross into a public artifact. This
module builds that separation on top of the enforced boundary in
:mod:`cwatlas.privacy`:

* every record is run through :func:`cwatlas.privacy.assert_exportable`, which
  refuses a ``PRIVATE`` record outright and defensively redacts a public one;
* **every field** of the resulting payload — nested dicts, lists, keys, and
  string values — is then scanned with
  :func:`cwatlas.privacy.refuse_private_in_public`, so a private path or
  identity token embedded anywhere in an otherwise public record is caught.

The build is strict: a single private record, or a single private token in any
field, refuses the whole export rather than shipping a partial leak.
:func:`partition` lets the operator see, separately, which records were public
and which were withheld — but only the public projection is ever exported.

Deterministic; ships no private data.

    SOURCE_VECTOR_GEOGRAPHIC_SEMANTICS_NOT_CLAIMED
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple

from cwatlas import privacy
from cwatlas.claims import ClaimClass
from cwatlas.privacy import PrivacyError, Record, Sensitivity


class ExportError(PrivacyError):
    """Raised when private content would enter a public export bundle."""


def _scan_value(where: str, value) -> None:
    """Recursively refuse any private path/identity token in a value tree."""
    if isinstance(value, str):
        try:
            privacy.refuse_private_in_public(value)
        except PrivacyError as exc:
            raise ExportError(f"in {where}: {exc}") from exc
    elif isinstance(value, dict):
        for k, v in value.items():
            if isinstance(k, str):
                try:
                    privacy.refuse_private_in_public(k)
                except PrivacyError as exc:
                    raise ExportError(f"in key of {where}: {exc}") from exc
            _scan_value(f"{where}.{k}", v)
    elif isinstance(value, (list, tuple)):
        for i, v in enumerate(value):
            _scan_value(f"{where}[{i}]", v)


def partition(records: Sequence[Record]) -> Tuple[List[Record], List[Record]]:
    """Split records into ``(public, private)`` without exporting anything."""
    public = [r for r in records if not r.is_private()]
    private = [r for r in records if r.is_private()]
    return public, private


def build_public_export(records: Iterable[Record]) -> dict:
    """Assemble a public export bundle, refusing any private content.

    Each record is asserted exportable (a ``PRIVATE`` record refuses; a public
    one is redacted), then every field of the redacted payload is scanned for
    private tokens. The whole bundle refuses on the first violation.
    """
    records = list(records)
    items: List[dict] = []
    for r in records:
        if r.is_private():
            raise ExportError(
                f"refused: record {r.record_id!r} is PRIVATE and may not enter "
                f"a public export bundle. Withhold it or export only its "
                f"synthetic public fixture.")
        payload = privacy.assert_exportable(r)  # redacts + refuses leftover
        _scan_value(f"record {r.record_id!r} id", r.record_id)
        _scan_value(f"record {r.record_id!r} payload", payload)
        items.append({
            "record_id": r.record_id,
            "sensitivity": r.sensitivity.value,
            "payload": payload,
        })
    return {
        "what_this_is": "a public export bundle carrying only redacted public content",
        "item_count": len(items),
        "items": items,
        "private_fields_stripped": sorted(privacy.PRIVATE_FIELDS),
        "claim_class": ClaimClass.MATHEMATICAL_TRANSLATION.value,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "source_vector_geographic_semantics": "NOT_CLAIMED",
        "verdict": "PUBLIC_EXPORT_SEPARATED_NO_PRIVATE_CONTENT",
    }


def assert_export_clean(bundle: dict) -> bool:
    """Re-scan an assembled bundle end to end; refuse if anything leaked."""
    if any(item["sensitivity"] != Sensitivity.PUBLIC_SYNTHETIC.value
           for item in bundle.get("items", [])):
        raise ExportError("refused: a bundle item is not PUBLIC_SYNTHETIC.")
    for item in bundle.get("items", []):
        _scan_value(f"bundle item {item['record_id']!r}", item)
    return True


def export_separation_report() -> dict:
    """P55 declaration receipt."""
    return {
        "phase_id": "P55",
        "what_this_is": (
            "privacy-narrative versus public-export separation: a public export "
            "bundle carries only synthetic/public, redacted content; private "
            "records and private tokens in any field are refused."),
        "private_fields": sorted(privacy.PRIVATE_FIELDS),
        "scan_is_recursive": True,
        "claim_class": ClaimClass.MATHEMATICAL_TRANSLATION.value,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "source_vector_geographic_semantics": "NOT_CLAIMED",
        "verdict": "PRIVATE_NARRATIVE_AND_PUBLIC_EXPORT_SEPARATED",
        "what_this_does_not_say": (
            "The export ships no private narrative, attribution, prediction, "
            "personal location, or raw vector string, and asserts no geographic "
            "or physical claim about any exported record."),
    }
