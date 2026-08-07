"""Design Studio workflow registry, navigation metadata, and
claim-boundary text provider.

Design Studio is the guided, task-first layer over the workbench. This
module is Qt-free: panels and headless exports both read from it so the
UI cards, the docs, and the exported artifacts stay in agreement.
"""
from __future__ import annotations

import uuid

#: Verbatim claim-boundary blocks (plan pack 15_TEMPLATES). Every exported
#: user-facing artifact embeds exactly one of these.
CLAIM_BOUNDARIES: dict[str, str] = {
    "certification": (
        "This sheet records measured inputs, derived geometry, model "
        "estimates, and provenance. It does not by itself validate an "
        "anomalous physical effect."),
    "build_sheet": (
        "This build sheet is an engineering plan and reproducibility "
        "record. Predictions are model outputs. Measurements decide."),
    "frequency_key": (
        "Frequency keys are recorded as sourced values, mathematical "
        "relations, or project candidates. Audio or modulation recipes "
        "are test recipes, not proof of outcome."),
    "ring_design": (
        "This annular ring design records geometry, masks, phase tables, "
        "probe layouts, and model outputs. It is not evidence of physical "
        "performance until measured."),
}

#: Classification tag carried by every Design Studio computed output
#: (matches the phyrll/terra lane vocabulary).
MODEL_OUTPUT = "MODEL_OUTPUT"
MEASURED_INPUT = "MEASURED_INPUT"

#: Workflow registry: home-page task cards and navigation metadata.
#: ``panel`` is the tab title the card navigates to.
WORKFLOWS: list[dict] = [
    {
        "key": "crystal_validator",
        "card": "Validate a crystal",
        "panel": "Crystal Validator",
        "inputs": "length, width/diameter, material, uncertainty",
        "outputs": "geometry receipt, derived values, certification PDF",
    },
    {
        "key": "certification_sheet",
        "card": "Generate a certification sheet",
        "panel": "Crystal Validator",
        "inputs": "a validated specimen",
        "outputs": "certification PDF with receipt hash",
    },
    {
        "key": "phyrll_generator",
        "card": "Design a Phyrll generator",
        "panel": "Phyrll Generator Designer",
        "inputs": "validated specimen, clearance, wall thickness",
        "outputs": "SCAD, STL (if OpenSCAD), build PDF, receipt JSON",
    },
    {
        "key": "phryll_v2",
        "card": "Design a crystal-first Phryll cone (v2)",
        "panel": "Phryll Generator v2",
        "inputs": "measured crystal profile, Eye coordinate, fit + "
                  "coil settings",
        "outputs": "custom cone + coil sleeve: SCAD, STL, 3MF, DXF, "
                   "SVG, PDFs, receipts, bundle",
    },
    {
        "key": "coil_pulse",
        "card": "Design coils and pulse settings",
        "panel": "Coil / Pulse Designer",
        "inputs": "assembly, wire gauge, coil geometry, pulse mode",
        "outputs": "wire estimates, pulse table, sidebands, build PDF",
    },
    {
        "key": "annular_ring",
        "card": "Design an annular ring prototype",
        "panel": "Annular Ring Designer",
        "inputs": "OD/ID, cell count, masks, probes",
        "outputs": "ring diagram, masks CSV, SCAD, engineering PDF",
    },
    {
        "key": "frequency_key_studio",
        "card": "Make binaural / frequency-key audio",
        "panel": "Frequency Key Studio",
        "inputs": "carrier or frequency key, beat target, layers",
        "outputs": "WAV, recipe JSON, session PDF, YouTube sheet",
    },
    {
        "key": "frequency_keys",
        "card": "Open Frequency Key Library",
        "panel": "Frequency Key Library",
        "inputs": "—",
        "outputs": "sourced key list, sidebands, key relations",
    },
    {
        "key": "advanced",
        "card": "Open Advanced Scientific Workbench",
        "panel": "Workspace",
        "inputs": "—",
        "outputs": "the full research workbench",
    },
]


def claim_boundary(kind: str) -> str:
    """The claim-boundary block for an artifact kind (KeyError = a new
    artifact kind shipped without deciding its boundary text)."""
    return CLAIM_BOUNDARIES[kind]


def workflow_by_key(key: str) -> dict:
    for wf in WORKFLOWS:
        if wf["key"] == key:
            return wf
    raise KeyError(key)


def new_object_id(prefix: str) -> str:
    """A fresh display ID like ``CRY-3F2A9C``. IDs are identity, not
    provenance — hashes carry provenance."""
    return f"{prefix}-{uuid.uuid4().hex[:6].upper()}"
