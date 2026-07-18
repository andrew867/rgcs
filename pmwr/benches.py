"""A55-A68 — preregistered bench definitions. PLANS ONLY.

Reuses the v4.6 preregistration type (``cspc.experiments``). Every
bench: both crystal orientations, the full null set from the source
claims, the sham-drive control (the source's own power-not-engaged
episode makes this non-negotiable), synchronized ordinary-output
matrix, and energy accounting. No apparatus exists; no data exists.
"""

from __future__ import annotations

from cspc.experiments import Preregistration
from .crystal import OUTPUT_CHANNELS

#: The null/control set demanded by the source-claims document.
NULL_SET = (
    "same crystal reversed", "straight quartz",
    "ordinary quartz prism", "fused silica or glass",
    "same mass/length different angles", "fixture without crystal",
    "dummy electrical network", "no-drive", "sham-drive",
    "nearby frequencies", "feedback loop open",
    "blocked optical pump", "matched thermal input",
)


def directional_transfer_bench() -> Preregistration:
    """A57: does ANY output channel depend on crystal orientation?"""
    return Preregistration(
        id="PMWR-BENCH-DIRECTIONAL",
        question="Does any ordinary output channel differ between "
                 "top-up and top-down orientations of the same "
                 "asymmetrically terminated crystal under identical "
                 "drive?",
        target_hz=(4096,),
        control_hz=(4000, 4200),
        n_per_condition=20,
        randomisation="orientation order randomised per block, seeded",
        blinding="analyst blind to orientation labels; sensor logs "
                 "carry coded ids",
        stopping_rule="fixed N; no extension on a promising trend",
        primary_outcome="per-channel difference (all "
                        f"{len(OUTPUT_CHANNELS)} ordinary channels) "
                        "between orientations",
        analysis="preregistered two-sided per channel with "
                 "Holm-Bonferroni across channels and conditions",
        correction="Holm-Bonferroni",
        safety=("isolated low-voltage drive", "no open RF radiator",
                "enclosed optics", "thermal channel instrumented",
                "stop on heating, arcing, fracture"),
    )


def self_oscillation_containment_bench() -> Preregistration:
    """A58: active feedback with the loop-open control."""
    return Preregistration(
        id="PMWR-BENCH-SELFOSC",
        question="Does a closed feedback loop sustain oscillation, "
                 "and does EVERY oscillation cease when the loop is "
                 "opened or the supply is removed?",
        target_hz=(32768,),
        control_hz=(30000,),
        n_per_condition=10,
        randomisation="loop state order randomised, seeded",
        blinding="analysis on coded logs",
        stopping_rule="fixed N",
        primary_outcome="oscillation amplitude vs loop state and "
                        "supply state; energy ledger per run",
        analysis="oscillation persisting without a supply is treated "
                 "as instrumentation error and investigated as such",
        correction="Holm-Bonferroni",
        safety=("current-limited supply", "loop gain capped",
                "containment: no output stage connected"),
    )


def sham_drive_bench() -> Preregistration:
    """A60/A65: the expectation-effect control elevated to its own
    bench, because the source narrative itself contains the failure."""
    return Preregistration(
        id="PMWR-BENCH-SHAM",
        question="Do observers report effects when the drive is "
                 "visibly 'on' but the output stage is disconnected?",
        target_hz=(4096,),
        control_hz=(4096,),          # identical: only the sham varies
        n_per_condition=20,
        randomisation="sham/live interleaved by seeded schedule "
                      "unknown to observers",
        blinding="double-blind: neither operator nor analyst knows "
                 "the schedule until analysis is locked",
        stopping_rule="fixed N",
        primary_outcome="reported-effect rate sham vs live",
        analysis="a sham-equal effect rate bounds the expectation "
                 "contribution for every other bench",
        correction="none needed (single comparison)",
        safety=("no drive reaches any transducer during sham runs",),
    )


REGISTERED_BENCHES = {
    "PMWR-BENCH-DIRECTIONAL": directional_transfer_bench,
    "PMWR-BENCH-SELFOSC": self_oscillation_containment_bench,
    "PMWR-BENCH-SHAM": sham_drive_bench,
}


def compile_benches() -> dict:
    plans = {k: f().to_dict() for k, f in REGISTERED_BENCHES.items()}
    return {
        "n_benches": len(plans),
        "benches": plans,
        "null_set": list(NULL_SET),
        "apparatus_status": "NOT BUILT",
        "data_status": "NO DATA COLLECTED",
        "physical_status": "UNTESTED",
        "evidence_class": "ANALYTIC_MODEL",
        "claim_boundary":
            "Preregistered plans only. Hardware absence BLOCKS every "
            "physical row (acceptance R29); nothing here is a bench "
            "result.",
    }
