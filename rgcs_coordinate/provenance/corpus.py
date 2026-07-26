"""RCW P05 — public-safe corpus and provenance registry.

Loads the packaged golden-vector fixtures, exposes typed records with
training labels and operator corrections, and validates any external
fixture file against the packet arithmetic. Immutable: records are
frozen dataclasses; the raw extraction of a corrected vector is always
retained beside its active value.

Private operator provenance is excluded by policy: the packaged
fixture carries public-safe chronology metadata only.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import resources

from rgcs_coordinate.codecs import federation_terra_30 as ft30
from rgcs_coordinate.domain.claims import ClaimClass

FIXTURE_RESOURCE = "golden_vectors.json"


@dataclass(frozen=True)
class CorpusVector:
    """One registered vector with its labels and any correction."""

    label: str
    raw_decimal: str
    role: str
    physical_label_class: str | None
    raw_extracted_shell: int | None
    active_shell: int | None
    correction_class: str | None

    @property
    def corrected(self) -> bool:
        return (self.raw_extracted_shell is not None
                and self.active_shell is not None
                and self.raw_extracted_shell != self.active_shell)


def _fixture_text() -> str:
    return (resources.files("rgcs_coordinate.fixtures")
            / FIXTURE_RESOURCE).read_text(encoding="utf-8")


def load_corpus() -> dict:
    """The packaged fixture document, parsed verbatim."""
    return json.loads(_fixture_text())


def vectors() -> tuple[CorpusVector, ...]:
    out = []
    for v in load_corpus()["vectors"]:
        intended = v.get("intended_shell")
        raw_shell = v.get("raw_extracted_shell")
        if raw_shell is None and intended is not None:
            # uncorrected member: active == raw extraction (verified
            # against the arithmetic in validate_corpus)
            raw_shell_actual = ft30.decode(
                int(v["raw_decimal"])).extracted_shell
            raw_shell = raw_shell_actual
        out.append(CorpusVector(
            label=v["label"],
            raw_decimal=v["raw_decimal"],
            role=v.get("role", "unspecified"),
            physical_label_class=v.get("physical_label_class"),
            raw_extracted_shell=raw_shell,
            active_shell=intended if intended is not None else raw_shell,
            correction_class=v.get("correction_class")))
    return tuple(out)


def training_vectors() -> tuple[CorpusVector, ...]:
    return tuple(v for v in vectors()
                 if v.physical_label_class
                 == ClaimClass.TRAINING_EQUALITY.value)


def validate_corpus(document: dict | None = None) -> dict:
    """Check a fixture document against the packet arithmetic.

    Every field a vector declares (binary, octal, face, path, shell,
    morton) must match the exact structural decode; corrections must
    declare both the raw extraction and the correction class. Returns
    a report; raises nothing for content errors — callers get the
    failures listed, receipts stay honest.
    """
    doc = document if document is not None else load_corpus()
    failures: list[str] = []
    checked = 0
    for v in doc.get("vectors", []):
        raw = v.get("raw_decimal")
        if raw is None or not str(raw).isdigit():
            failures.append(f"{v.get('label')}: missing/invalid raw_decimal")
            continue
        trace = ft30.decode(int(raw))
        checked += 1
        expected = {
            "binary": trace.binary30, "octal": trace.octal10,
            "face": trace.face_id,
            "q22_bits": trace.q22_bits,
            "q22_path": list(trace.q22_path),
            "shell": trace.extracted_shell,
            "spatial_octal": trace.spatial_octal_path,
        }
        for key, want in expected.items():
            if key in v and v[key] != want:
                failures.append(
                    f"{v['label']}: field {key} = {v[key]!r} does not "
                    f"match the packet arithmetic ({want!r})")
        if "morton" in v:
            m, a = v["morton"], trace.morton_audit
            for key, want in (("x_bits", a.x_bits), ("x_index", a.x_index),
                              ("y_bits", a.y_bits), ("y_index", a.y_index),
                              ("z_bits", a.z_bits), ("z_index", a.z_index)):
                if key in m and m[key] != want:
                    failures.append(
                        f"{v['label']}: morton.{key} = {m[key]!r} != "
                        f"{want!r}")
        if "raw_extracted_shell" in v:
            if v["raw_extracted_shell"] != trace.extracted_shell:
                failures.append(
                    f"{v['label']}: raw_extracted_shell "
                    f"{v['raw_extracted_shell']} != arithmetic "
                    f"{trace.extracted_shell}")
            if "correction_class" not in v:
                failures.append(
                    f"{v['label']}: a corrected vector must declare its "
                    f"correction_class")
        if (v.get("intended_shell") is not None
                and "raw_extracted_shell" not in v
                and v["intended_shell"] != trace.extracted_shell):
            failures.append(
                f"{v['label']}: intended_shell {v['intended_shell']} "
                f"differs from extraction {trace.extracted_shell} but no "
                f"raw_extracted_shell/correction is declared")
    return {"schema": doc.get("schema"), "vectors_checked": checked,
            "failures": failures, "valid": not failures}


def orange_slice_active_shells() -> tuple[int, ...]:
    """The locked active solve: 7, 7, 7 (raw 7, 3, 7 kept in provenance)."""
    rows = [v for v in vectors() if v.label.startswith("orange-slice")]
    return tuple(v.active_shell for v in rows)
