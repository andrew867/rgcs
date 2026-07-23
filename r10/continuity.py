"""P14/P15 — bus-factor-zero continuity: manifest, export, restore.

The project must survive the loss of any person or model. That is not a
slogan; it is a testable property. This module makes it one.

**A deterministic manifest.** :func:`build_manifest` hashes a set of
canonical artifacts into a sorted, reproducible manifest — same tree,
same bytes, same manifest. Two builds of an unchanged tree are identical,
so a drift is detectable rather than deniable.

**Export and restore.** :func:`export_manifest` writes the manifest;
:func:`verify_restore` checks a (re)built tree against it and names every
file that is missing or altered. That is the disaster-recovery loop: from
the manifest alone you can prove whether a restored copy is faithful.

**A successor drill.** :func:`successor_checklist` is the clean-room test:
a stranger with only the repositories and docs must clone, build, test,
regenerate docs, locate the private boundary, reproduce one analysis,
commit one valid change, and restore an archive. If any step needs
knowledge that lives only in a person's head or a chat log, the drill
fails — and this module refuses to pretend otherwise.

Nothing here is a physical measurement; it is repository hygiene, and it
carries the same `PHYSICAL_VALIDATION_NOT_CLAIMED` discipline as
everything else.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path


class ContinuityError(RuntimeError):
    """Raised on an incomplete manifest or a failed restore."""


def hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_file(path: Path) -> str:
    return hash_bytes(Path(path).read_bytes())


@dataclass(frozen=True)
class ManifestEntry:
    """One canonical artifact: its repo-relative path and content hash."""

    path: str
    sha256: str
    public_private_class: str = "PUBLIC"
    restore_order: int = 100
    purpose: str = ""


def build_manifest(root: Path, rel_paths: list[str],
                   classes: dict[str, str] | None = None) -> list[ManifestEntry]:
    """Hash each artifact into a DETERMINISTIC, sorted manifest.

    ``rel_paths`` are repo-relative. A path that does not exist is an
    error: a continuity manifest that silently omits a missing canonical
    file is worse than useless.
    """
    classes = classes or {}
    entries: list[ManifestEntry] = []
    for rel in sorted(set(rel_paths)):
        p = Path(root) / rel
        if not p.is_file():
            raise ContinuityError(
                f"canonical artifact missing: {rel!r}. A continuity "
                f"manifest may not omit a required file.")
        entries.append(ManifestEntry(
            rel, hash_file(p), classes.get(rel, "PUBLIC")))
    return entries


def manifest_to_json(entries: list[ManifestEntry], *, commit: str) -> str:
    """Serialize deterministically (sorted keys, stable order)."""
    payload = {
        "schema": "rgcs.continuity_manifest.v1",
        "commit": commit,
        "artifact_count": len(entries),
        "artifacts": [
            {"path": e.path, "sha256": e.sha256,
             "public_private_class": e.public_private_class,
             "restore_order": e.restore_order}
            for e in entries
        ],
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def export_manifest(entries: list[ManifestEntry], dest: Path, *,
                    commit: str) -> Path:
    dest = Path(dest)
    dest.write_text(manifest_to_json(entries, commit=commit),
                    encoding="utf-8", newline="\n")
    return dest


def verify_restore(root: Path, entries: list[ManifestEntry]) -> dict:
    """Check a (restored) tree against the manifest. Names every problem."""
    missing: list[str] = []
    altered: list[str] = []
    for e in entries:
        p = Path(root) / e.path
        if not p.is_file():
            missing.append(e.path)
        elif hash_file(p) != e.sha256:
            altered.append(e.path)
    ok = not missing and not altered
    return {
        "ok": ok,
        "checked": len(entries),
        "missing": missing,
        "altered": altered,
        "verdict": "RESTORE_VERIFIED" if ok else "RESTORE_INCOMPLETE",
    }


def refuse_restore_on_mismatch(report: dict) -> None:
    """Refuse to declare a restore successful when files differ."""
    if not report.get("ok"):
        raise ContinuityError(
            f"restore not verified: {len(report['missing'])} missing, "
            f"{len(report['altered'])} altered. A disaster-recovery restore "
            f"is complete only when every canonical hash matches.")


#: The clean-room successor drill. Every step must be doable from the
#: repositories and docs alone — no person, no chat log, no hidden path.
SUCCESSOR_STEPS = (
    "clone the public repository",
    "create the environment and install the dev extras",
    "run the full test suite green",
    "regenerate the documentation set",
    "locate the public/private boundary and the private repository policy",
    "reproduce one analysis (e.g. a null result) from source",
    "commit one valid change on a branch",
    "restore an archive and verify it against its manifest",
    "explain established vs source-derived claims and why natural and "
    "synthetic quartz are both required",
    "state the exact next command and ten unresolved questions",
)


def successor_checklist() -> dict:
    return {
        "steps": list(SUCCESSOR_STEPS),
        "pass_condition": ("every step completes using only the "
                           "repositories and documentation"),
        "fail_condition": ("any step needs knowledge that lives only in a "
                           "person's memory or a chat transcript"),
        "bus_factor_target": 0,
    }


def continuity_report() -> dict:
    return {
        "what_this_is": (
            "bus-factor-zero continuity: a deterministic manifest, an "
            "export/restore verification loop, and a clean-room successor "
            "drill"),
        "successor_steps": len(SUCCESSOR_STEPS),
        "evidence_class": "DERIVED_MATHEMATICS",
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "verdict": "CONTINUITY_SOFTWARE_ONLY",
        "what_this_does_not_say": (
            "It does not guarantee any third party has actually run the "
            "successor drill, nor that off-repository backups exist. It "
            "proves that, given a manifest and a tree, faithfulness is "
            "checkable, and it enumerates what a successor must be able to "
            "do."),
    }
