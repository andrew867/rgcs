"""P35 — replication package and external handoff.

Assembles a deterministic manifest an external replicator can use: the r15
module set with per-file SHA-256, the schema set, the phase-receipt set, and
the deterministic seeds. It refuses to include any file containing private
content, and it caps the whole package at SOFTWARE_IMPLEMENTED — a
replication package is code and protocols, not a physical result.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path


class ReplicationPackageError(RuntimeError):
    """Raised if a package would carry private content or a physical claim."""


#: Fragment-built forbidden tokens so this module never trips its own scan.
_PRIVATE_TOKENS = (
    "private" + "_do_not_commit",
    "C:" + "\\Users",
    "one" + "drive - ",   # the private path fragment, not the bare word
)


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def scan_for_private(text: str) -> list:
    low = text.lower()
    return [tok for tok in _PRIVATE_TOKENS if tok.lower() in low]


@dataclass
class ReplicationManifest:
    package_id: str
    files: dict = field(default_factory=dict)      # rel path -> sha256
    schemas: list = field(default_factory=list)
    receipts: list = field(default_factory=list)
    seeds: list = field(default_factory=list)

    def content_hash(self) -> str:
        payload = json.dumps({
            "package_id": self.package_id,
            "files": self.files,
            "schemas": sorted(self.schemas),
            "receipts": sorted(self.receipts),
            "seeds": sorted(self.seeds),
        }, sort_keys=True).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()


def build_manifest(repo_root: Path | str = ".", *,
                   seeds=(0, 1, 7)) -> ReplicationManifest:
    root = Path(repo_root)
    man = ReplicationManifest(package_id="R15_REPLICATION_PACKAGE",
                              seeds=list(seeds))
    r15dir = root / "r15"
    for py in sorted(r15dir.glob("*.py")):
        rel = f"r15/{py.name}"
        # a package file with private content must never ship
        if scan_for_private(py.read_text(encoding="utf-8", errors="ignore")):
            raise ReplicationPackageError(
                f"refused: {rel} contains private content; a replication "
                f"package ships only public, synthetic-fixture code.")
        man.files[rel] = _sha256_file(py)
    for sch in sorted((r15dir / "schemas").glob("*.json")):
        man.schemas.append(f"r15/schemas/{sch.name}")
    recdir = root / "docs/v8/receipts"
    if recdir.exists():
        for rec in sorted(recdir.glob("*.json")):
            man.receipts.append(f"docs/v8/receipts/{rec.name}")
    return man


def refuse_package_with_private_content(sample: str = "") -> None:
    if scan_for_private(sample):
        raise ReplicationPackageError(
            "refused: the replication package must contain no private "
            "content; only public, synthetic-fixture code and protocols ship.")


def replication_package_report() -> dict:
    return {
        "what_this_is": "the R15 replication package and external handoff",
        "claim_class": "SOFTWARE_IMPLEMENTED",
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "verdict": "REPLICATION_PACKAGE_ASSEMBLED_PUBLIC_ONLY",
        "what_this_does_not_say": (
            "It packages public code, schemas, receipts, and seeds for an "
            "external replicator; it contains no physical result and no "
            "private content."),
    }
