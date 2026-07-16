"""Source-lore translation companion (Agent M10; source SRC-V4-19).

Motifs from the pack's enumeration (subtitle/transcript files were not
supplied locally, DV4C-003). Literal meanings stay SRC; computational
analogues are explicit, falsifiable, and mechanically barred from
EST/DER conclusions."""

from __future__ import annotations

from dataclasses import dataclass, field

CLASSIFICATION = "SOURCE_HYPOTHESIS"


@dataclass(frozen=True)
class MotifTranslation:
    motif_id: str
    source_id: str
    source_locator: str
    motif_label: str
    literal_meaning: str          # SRC only, preserved verbatim intent
    computational_analogue: str | None
    related_module: str | None
    proposed_observable: str | None
    controls: str | None
    falsification_condition: str | None
    permitted_use: str = "hypothesis generation only"
    prohibited_inference: str = ("literal narrative claims may not "
                                 "enter EST/DER conclusions")

    def __post_init__(self):
        if not self.source_locator:
            raise ValueError("source locator required")
        if self.computational_analogue is not None and \
                not self.falsification_condition:
            raise ValueError("an analogue requires a falsification "
                             "condition")


MOTIFS: dict[str, MotifTranslation] = {m.motif_id: m for m in (
    MotifTranslation(
        "LORE-01", "SRC-V4-19", "pack 16, motif list",
        "broken net",
        "a net/web that is broken (narrative)",
        "perturbed coupling graph: remove/weaken edges of the M2 "
        "CouplingGraph or a boundary operator (M6)",
        "rscs2_core.multiphysics.coupling",
        "eigenmode shift under edge removal",
        "unperturbed graph comparison",
        "no measurable modal difference between intact and perturbed "
        "graph at declared tolerance"),
    MotifTranslation(
        "LORE-02", "SRC-V4-19", "pack 16, motif list",
        "ripple",
        "a ripple spreading (narrative)",
        "impulse response of a validated modal system (fem."
        "harmonic_response / M12 trajectory impulse)",
        "rscs2_core.fem",
        "measured FRF vs predicted impulse response",
        "no-drive null",
        "FRF disagrees with modal prediction beyond tolerance"),
    MotifTranslation(
        "LORE-03", "SRC-V4-19", "pack 16, motif list",
        "pieces moved",
        "pieces displaced from their places (narrative)",
        "coordinate/state displacement: initial-condition offset in a "
        "typed state block",
        "rscs2_core.multiphysics",
        "relaxation trajectory from displaced state",
        "undisplaced control",
        "no relaxation dynamics distinguishable from control"),
    MotifTranslation(
        "LORE-04", "SRC-V4-19", "pack 16, motif list",
        "bend toward one point",
        "everything bends toward a point (narrative)",
        "focusing functional / Green-function concentration / graph "
        "centrality maximum",
        "rscs2_core.eye",
        "localization metric (participation ratio) of computed fields",
        "symmetric-body null (eye engine)",
        "no localized region passes the eye consensus gates "
        "(NO_STABLE_CANDIDATE) — which IS the current canonical "
        "verdict family"),
    MotifTranslation(
        "LORE-05", "SRC-V4-19", "pack 16, motif list",
        "bridge",
        "a bridge between realms (narrative)",
        "coupling operator between state spaces (M2 edge)",
        "rscs2_core.multiphysics.coupling",
        "avoided-crossing splitting 2g (M4)",
        "zero-coupling exact crossing",
        "no splitting resolvable above linewidth"),
    MotifTranslation(
        "LORE-06", "SRC-V4-19", "pack 16, motif list",
        "machinery or clock",
        "great machinery / clockwork (narrative)",
        "synchronized subsystem graph (frozen v3 timing closures)",
        "rgcs_core.timing",
        "exact closure windows (golden 125 ms rows)",
        "non-closing window flags (half-spacing)",
        "claimed synchronization without integer closure"),
    MotifTranslation(
        "LORE-07", "SRC-V4-19", "pack 16, motif list",
        "loop",
        "a loop/cycle (narrative)",
        "recurrence, delay line, limit cycle, or feedback loop in the "
        "calibration/drift layer",
        "rscs2_core.calibration",
        "drift-alert recurrence statistics",
        "white-noise (no-recurrence) fixture",
        "no periodicity above noise floor"),
    MotifTranslation(
        "LORE-08", "SRC-V4-19", "pack 16, motif list",
        "repair",
        "repairing the broken structure (narrative)",
        "constrained inverse problem: recover coupling/boundary "
        "parameters from observations (M8 inverse design)",
        "rscs2_core.calibration",
        "parameter recovery error on synthetic damage",
        "non-identifiability flag",
        "recovery fails or is non-identifiable at declared noise"),
    MotifTranslation(
        "LORE-09", "SRC-V4-19", "pack 16, motif list",
        "CERN time breakage / portals / Atlantis / consciousness-"
        "causes-matter / spacetime repair",
        "literal extraordinary claims (narrative)",
        None,                       # honestly: no useful analogue
        None, None, None, None),
)}


FORBIDDEN_LORE_PHRASES = ("portal", "atlantis", "time breakage",
                          "consciousness causes", "spacetime repair",
                          "star nation")


def conclusion_linter(text: str, allow_quoted: bool = True
                      ) -> list[str]:
    """Reject lore phrases from EST/DER conclusions unless they appear
    inside explicit quotation marks (source statements)."""
    hits = []
    low = text.lower()
    for p in FORBIDDEN_LORE_PHRASES:
        i = low.find(p)
        while i != -1:
            ctx = low[max(0, i - 80):i + 80]
            quoted = ('"' in ctx[:80] and '"' in ctx[80:]) or \
                ("src quote" in ctx)
            if not (allow_quoted and quoted):
                hits.append(p)
                break
            i = low.find(p, i + 1)
    return hits


def registry_report() -> dict:
    with_analogue = [m.motif_id for m in MOTIFS.values()
                     if m.computational_analogue]
    without = [m.motif_id for m in MOTIFS.values()
               if m.computational_analogue is None]
    return {"classification": CLASSIFICATION,
            "n_motifs": len(MOTIFS),
            "with_analogue": with_analogue,
            "no_useful_analogue": without,
            "note": "motifs without analogues are recorded honestly, "
                    "not force-translated"}
