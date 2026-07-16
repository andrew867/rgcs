"""v4-completion source/equation provenance layer (Agent M1).

Loads and ENFORCES the v4 source registry and equation ledger:
classification ceilings, source hierarchy, the exclusion matrix
(forbidden mechanism/material transfers), the lawful-release filter,
the provenance linter, and the ingest/diff tool that upgrades
metadata-only records to FULL_TEXT_LOCAL with real hashes when files
are supplied (DV4C-003). The v3 registry is frozen and read-only.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
SRC_REGISTRY = REPO / "sources" / "registry" / "v4_source_registry.yaml"
EQ_LEDGER = REPO / "sources" / "registry" / "v4_equation_ledger.yaml"

#: source-type rank for the hierarchy resolver (lower = higher rank).
SOURCE_RANK = {
    "PEER_REVIEWED_PRIMARY": 0,
    "INTERNAL_RGCS_AUTHORITY": 1,
    "PEER_REVIEWED_THEORY": 2,
    "REVIEW": 3,
    "PREPRINT": 4,
    "AUTHOR_MANUSCRIPT": 5,
    "LINKED_V3_AUTHORITY": 1,
    "COMMENTARY": 6,
    "PUBLIC_PREVIEW": 7,
    "SOFTWARE_DOCUMENTATION": 7,
    "UNRESOLVED_TOPIC": 8,
    "INDEPENDENT_THEORY_ESSAY": 9,
    "HISTORICAL_SOURCE": 9,
    "SUBTITLE_TRANSCRIPT": 10,
}

#: classification ceilings by source type: nothing derived from these
#: source types may claim a class above the ceiling (gate B5).
CLASS_ORDER = ["SOURCE_HYPOTHESIS", "INTERFACE_ONLY",
               "REDUCED_ORDER_VALIDATED", "CORE_VALIDATED"]
TYPE_CEILING = {
    "INDEPENDENT_THEORY_ESSAY": "SOURCE_HYPOTHESIS",
    "SUBTITLE_TRANSCRIPT": "SOURCE_HYPOTHESIS",
    "HISTORICAL_SOURCE": "SOURCE_HYPOTHESIS",
    "COMMENTARY": "INTERFACE_ONLY",       # commentary is never primary data
    "PUBLIC_PREVIEW": "INTERFACE_ONLY",
    "UNRESOLVED_TOPIC": "REDUCED_ORDER_VALIDATED",
}

#: exclusion matrix: (mechanism, material) pairs that may NEVER
#: activate + named forbidden transfers. Enforced here AND by the M2
#: capability firewall (defense in depth).
FORBIDDEN_MECHANISMS_FOR_QUARTZ = frozenset({
    "magnetic_order", "magnon_modes", "exciton_frenkel",
    "exciton_wannier", "exciton_charge_transfer",
    "exciton_magnon_coupling", "ferrotoroidic_order",
    "toroidal_moment", "magnetoelectric_dynamic", "domain_writing",
    "thermal_domain_selection", "quantum_statistical_response",
    "microscopic_tunnelling_model", "spacetime_torsion",
})
FORBIDDEN_TRANSFERS = (
    ("SRC-V4-18", "*", "FDT equations may not enter default solvers"),
    ("SRC-V4-19", "*", "source-lore may not enter EST/DER conclusions"),
    ("SRC-V4-01", "material.alpha_quartz",
     "LiNiPO4 parameters may not be imported into quartz"),
    ("SRC-V4-02", "primary_data",
     "commentary/preview may not be treated as primary data"),
    ("*", "proton_tunnelling_from_continuum",
     "continuum symmetry sweeps may not ground tunnelling claims"),
    ("*", "photon_creation_from_classical_switching",
     "classical boundary switching may not ground photon creation"),
)


class ProvenanceError(ValueError):
    """Raised on any provenance/ceiling/exclusion violation."""


@dataclass(frozen=True)
class SourceRecord:
    source_id: str
    source_type: str
    access_status: str
    raw: dict

    @property
    def is_local(self) -> bool:
        return self.access_status in ("FULL_TEXT_LOCAL", "LOCAL")

    @property
    def redistribution_allowed(self) -> bool:
        return bool(self.raw.get("redistribution_allowed", False))


def load_sources(path: Path = SRC_REGISTRY) -> dict[str, SourceRecord]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    out: dict[str, SourceRecord] = {}
    for rec in data["sources"]:
        sid = rec["source_id"]
        if sid in out:
            raise ProvenanceError(f"duplicate source_id {sid}")
        st = rec["source_type"]
        if st not in SOURCE_RANK:
            raise ProvenanceError(f"{sid}: unknown source_type {st}")
        # no guessed hashes: a null local file must have a null sha256
        if rec.get("local_filename") is None and \
                rec.get("sha256") not in (None, "COMPUTED_AT_INGEST"):
            raise ProvenanceError(f"{sid}: sha256 without local file")
        out[sid] = SourceRecord(sid, st, rec.get("access_status", ""),
                                rec)
    return out


def load_equations(path: Path = EQ_LEDGER) -> dict[str, dict]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    out: dict[str, dict] = {}
    required = {"equation_id", "source_id", "source_locator",
                "source_expression", "adapted_expression",
                "adaptation_type", "forbidden_transfers", "units_check",
                "classification"}
    for eq in data["equations"]:
        missing = required - set(eq)
        if missing:
            raise ProvenanceError(
                f"{eq.get('equation_id', '?')}: missing {missing}")
        if eq["equation_id"] in out:
            raise ProvenanceError(
                f"duplicate equation_id {eq['equation_id']}")
        out[eq["equation_id"]] = eq
    return out


def classification_ceiling(source_id: str,
                           sources: dict[str, SourceRecord] | None = None
                           ) -> str:
    """Highest classification any result derived from this source may
    carry. Explicit per-record ceilings win; otherwise the type rule."""
    sources = sources or load_sources()
    rec = sources.get(source_id)
    if rec is None:
        raise ProvenanceError(f"unknown source {source_id}")
    explicit = rec.raw.get("classification_ceiling")
    if explicit:
        return explicit
    return TYPE_CEILING.get(rec.source_type, "CORE_VALIDATED")


def check_classification(source_id: str, claimed: str,
                         sources: dict[str, SourceRecord] | None = None
                         ) -> None:
    """Raise when a claimed class exceeds the source ceiling — the
    anti-laundering check (B5). SRC/HYP can never become EST/DER by
    passing through an adapter."""
    ceiling = classification_ceiling(source_id, sources)
    if CLASS_ORDER.index(claimed) > CLASS_ORDER.index(ceiling):
        raise ProvenanceError(
            f"classification laundering: {source_id} ceiling "
            f"{ceiling}, claimed {claimed}")


def resolve_precedence(source_ids: list[str],
                       sources: dict[str, SourceRecord] | None = None
                       ) -> str:
    """Source hierarchy resolver: return the highest-ranked source.
    Primary experimental papers outrank commentary (B4)."""
    sources = sources or load_sources()
    ranked = sorted(source_ids,
                    key=lambda s: SOURCE_RANK[sources[s].source_type])
    return ranked[0]


def check_transfer(source_id: str, target: str) -> None:
    """Raise on a forbidden transfer (exclusion matrix)."""
    for src, tgt, reason in FORBIDDEN_TRANSFERS:
        if (src in ("*", source_id)) and (tgt in ("*", target)):
            if src == "*" and tgt != target:
                continue
            if src != "*" and tgt == "*" and target.startswith(
                    "default_solver"):
                raise ProvenanceError(f"forbidden transfer: {reason}")
            if tgt == target:
                raise ProvenanceError(f"forbidden transfer: {reason}")


def quartz_mechanism_allowed(mechanism: str) -> bool:
    return mechanism not in FORBIDDEN_MECHANISMS_FOR_QUARTZ


def release_filter(paths: list[Path],
                   sources: dict[str, SourceRecord] | None = None
                   ) -> list[str]:
    """Return violations: any staged file that matches a registered
    restricted source filename (B3). Empty list = lawful."""
    sources = sources or load_sources()
    restricted_names = {
        Path(rec.raw["local_filename"]).name.lower()
        for rec in sources.values()
        if rec.raw.get("local_filename")
        and not rec.redistribution_allowed}
    # v3 registry PDFs are likewise never shipped
    v3 = yaml.safe_load((REPO / "references" /
                         "source_registry.yaml").read_text(
        encoding="utf-8"))
    for rec in v3.get("sources", []):
        if rec.get("file"):
            restricted_names.add(Path(rec["file"]).name.lower())
    return [str(p) for p in paths
            if p.suffix.lower() == ".pdf"
            and p.name.lower() in restricted_names]


_ID_RE = re.compile(r"(SRC-V4-\d+|RGCS-V4-EQ-\d+)")


def lint_provenance_ids(paths: list[Path]) -> list[str]:
    """Scan files for SRC-V4-* / RGCS-V4-EQ-* references and report
    any that do not resolve in the registries."""
    sources = load_sources()
    eqs = load_equations()
    known = set(sources) | set(eqs)
    bad = []
    for p in paths:
        txt = p.read_text(encoding="utf-8", errors="ignore")
        for m in _ID_RE.findall(txt):
            if m not in known:
                bad.append(f"{p}: unresolved {m}")
    return bad


def ingest_file(source_id: str, file_path: Path,
                registry_path: Path = SRC_REGISTRY) -> dict:
    """Upgrade a metadata-only record with a real local file: computes
    the true SHA-256 and flips access_status to FULL_TEXT_LOCAL. Also
    the source-diff tool: if the record already has a hash and the new
    content differs, refuse (same-name-different-content detection)."""
    data = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    digest = hashlib.sha256(file_path.read_bytes()).hexdigest()
    for rec in data["sources"]:
        if rec["source_id"] != source_id:
            continue
        old = rec.get("sha256")
        if old and old not in (None, "COMPUTED_AT_INGEST") \
                and old != digest:
            raise ProvenanceError(
                f"{source_id}: same-name content change "
                f"({old[:12]} -> {digest[:12]}); register a new "
                "source_id instead of silently replacing")
        rec["sha256"] = digest
        rec["local_filename"] = str(file_path)
        rec["access_status"] = "FULL_TEXT_LOCAL"
        registry_path.write_text(
            yaml.safe_dump(data, sort_keys=False,
                           allow_unicode=True), encoding="utf-8")
        return rec
    raise ProvenanceError(f"unknown source {source_id}")
