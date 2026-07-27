"""R10.9 sealed holdout intake — 2026-07-27 operator records.

Five raw wire values received 2026-07-27, sealed into a HOLDOUT
registry, NOT the training corpus. Hard rules (operator, verbatim in
intent):

- raw records hashed and preserved BEFORE decoding;
- never used to select the T11 interleave;
- never used to fit Earth alignment V2;
- the pair (1687209343, 168724343) arrived together but NO parent-child
  relation is assumed; that test waits until T11 is frozen;
- no place-name/gazetteer lookup until T11 + header profile + face
  orientation + Earth V2 are frozen;
- pre-reveal prediction receipts are produced for every decodable
  vector and no retuning happens after labels are later supplied;
- publication remains HOLD.

The referenced external receipt file
``RGCS_Sealed_Holdout_Intake_2026-07-27/SEALED_HOLDOUT_INTAKE.json``
was NOT found anywhere on disk (repo, internal-docs, archives searched
2026-07-27); the operator message itself is therefore the sealed
intake source and is preserved verbatim below.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict

INTAKE_ID = "SEALED_HOLDOUT_INTAKE_2026-07-27"
EXTERNAL_RECEIPT_STATUS = (
    "referenced file RGCS_Sealed_Holdout_Intake_2026-07-27/"
    "SEALED_HOLDOUT_INTAKE.json NOT FOUND on disk after full search; "
    "operator chat message of 2026-07-27 is the intake source")


@dataclass(frozen=True)
class SealedRecord:
    raw: int
    received_local: str
    batch: str
    source_note: str
    evidence_class: str = "SOURCE_REPORTED"

    def sha256(self) -> str:
        return hashlib.sha256(str(self.raw).encode("ascii")).hexdigest()

    def to_dict(self) -> dict:
        d = asdict(self)
        d["raw_sha256"] = self.sha256()
        return d


RECORDS: tuple[SealedRecord, ...] = (
    SealedRecord(165892323, "2026-07-27 ~06:07", "waking",
                 "recorded immediately on waking; no description"),
    SealedRecord(1687209343, "2026-07-27 ~14:05", "pair",
                 "received together without description; relationship "
                 "to 168724343 UNKNOWN — not assumed"),
    SealedRecord(168724343, "2026-07-27 ~14:05", "pair",
                 "received together without description; relationship "
                 "to 1687209343 UNKNOWN — not assumed"),
    SealedRecord(165872943, "2026-07-27 ~16:31", "preset-pair",
                 "source note: 'move like preset locations'; no "
                 "geographic labels"),
    SealedRecord(165829473, "2026-07-27 ~16:31", "preset-pair",
                 "source note: 'move like preset locations'; no "
                 "geographic labels"),
)

_RAWS = frozenset(r.raw for r in RECORDS)


class SealedHoldoutError(ValueError):
    pass


def intake_sha256() -> str:
    """Hash of the ordered raw records (sealed before decoding)."""
    payload = json.dumps([r.raw for r in RECORDS]).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def assert_not_training_input(raw: int, purpose: str) -> None:
    """Firewall: sealed records never enter T11 selection or V2
    (or any) calibration fitting."""
    if int(raw) in _RAWS:
        raise SealedHoldoutError(
            f"refused: {raw} is a SEALED holdout record "
            f"({INTAKE_ID}) and cannot be used for {purpose}")


#: Structural observation preserved verbatim (rule 6/7): every raw
#: decimal value ends in 3, while the compact low-three-bit
#: diagnostics are NOT uniform — S3 in {3, 7, 7, 1} across the four
#: decodable vectors. This strengthens the firewall:
#: decimal terminal marker != automatically binary low-three bits
#: != automatically physical shell semantics.
STRUCTURAL_OBSERVATION = {
    "all_decimal_terminals": 3,
    "decodable_s3_values": {165892323: 3, 168724343: 7,
                            165872943: 7, 165829473: 1},
    "uniform": False,
    "firewall": "decimal terminal marker != binary low-three bits != "
                "physical shell semantics (R109-SHL-02, strengthened)",
}


def registry_dict() -> dict:
    return {
        "schema": "rgcs.r109.sealed-holdout-intake.v1",
        "intake_id": INTAKE_ID,
        "external_receipt_status": EXTERNAL_RECEIPT_STATUS,
        "intake_sha256": intake_sha256(),
        "records": [r.to_dict() for r in RECORDS],
        "structural_observation": {
            **STRUCTURAL_OBSERVATION,
            "decodable_s3_values": {
                str(k): v for k, v in
                STRUCTURAL_OBSERVATION["decodable_s3_values"].items()},
        },
        "rules": [
            "hashed before decoding", "never T11 selection input",
            "never Earth V2 fit input",
            "pair relationship untested until T11 frozen",
            "no gazetteer lookup until T11+header+face+V2 frozen",
            "no retuning after label reveal", "publication HOLD",
        ],
    }
