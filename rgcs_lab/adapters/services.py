"""Memory, dual-pole, lattice, metasurface, predictions, proofs adapters."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rgcs_lab.adapters import coordinate, frames, golay
from rgcs_lab.adapters import resolve
from rgcs_lab.common.receipts import build_receipt
from rgcs_lab.common.status import ModuleResult, Status, module_catalog
from rgcs_lab.reference import dual_pole as dual_ref
from rgcs_lab.reference import lattice as lattice_ref
from rgcs_lab.reference import memory as memory_ref
from rgcs_lab.reference import metasurface as meta_ref
from rgcs_lab.reference import predictions as pred_ref


def memory_benchmark(query: str = "golay bit flips transport wrapper") -> ModuleResult:
    mod = resolve("rgcs_memory", "rgcs_lab.reference.memory")
    payload = mod.run_benchmark(query) if hasattr(mod, "run_benchmark") else memory_ref.run_benchmark(query)
    receipt = build_receipt(
        module="memory",
        status=Status.GREEN.value,
        claim_class=["IMPLEMENTED_SOFTWARE", "EXPLORATORY_MODEL"],
        inputs={"query": query},
        models=[payload.get("model", "bag-of-tokens-overlap-v1")],
        result=payload,
        tests=["memory_benchmark_digest"],
        warnings=["CONSCIOUSNESS: not demonstrated"],
    )
    return ModuleResult(
        module="memory",
        status=Status.GREEN,
        claim_class=["IMPLEMENTED_SOFTWARE", "EXPLORATORY_MODEL"],
        input={"query": query},
        models=receipt["models"],
        result=payload,
        warnings=receipt["warnings"],
        receipt=receipt,
        does="Reproducible provenance-memory retrieval benchmark.",
        does_not="Does not demonstrate consciousness.",
        tests=receipt["tests"],
        source=getattr(mod, "__name__", "rgcs_lab.reference.memory"),
    )


def dual_pole_audit(claim: dict[str, Any]) -> ModuleResult:
    mod = resolve("rgcs_dual_pole", "rgcs_lab.reference.dual_pole")
    payload = mod.audit_claim(claim) if hasattr(mod, "audit_claim") else dual_ref.audit_claim(claim)
    status = Status[payload.get("status", "YELLOW")]
    receipt = build_receipt(
        module="dual_pole",
        status=status.value,
        claim_class=["IMPLEMENTED_SOFTWARE", "EXPLORATORY_MODEL"],
        inputs={"claim": claim},
        models=["dual-pole-state-machine-v1"],
        result=payload,
        tests=["dual_pole_critic_not_bypassed"],
        warnings=["Independent witness status: not established"],
    )
    return ModuleResult(
        module="dual_pole",
        status=status,
        claim_class=["IMPLEMENTED_SOFTWARE", "EXPLORATORY_MODEL"],
        input={"claim": claim},
        models=receipt["models"],
        result=payload,
        warnings=receipt["warnings"],
        receipt=receipt,
        does="Proposer/critic loop with typed attack families.",
        does_not="Does not make two models independent witnesses.",
        tests=receipt["tests"],
        source=getattr(mod, "__name__", "rgcs_lab.reference.dual_pole"),
    )


def lattice_run(model: str = "counterrotating-ring") -> ModuleResult:
    mod = resolve("rgcs_lattice", "rgcs_lab.reference.lattice")
    payload = mod.run_example(model=model) if hasattr(mod, "run_example") else lattice_ref.run_example(model=model)
    receipt = build_receipt(
        module="lattice",
        status=Status.GREEN.value,
        claim_class=["IMPLEMENTED_SOFTWARE", "CONVENTIONAL_PHYSICS", "EXPLORATORY_MODEL"],
        inputs={"model": model},
        models=[model],
        result=payload,
        tests=["lattice_hermitian", "lattice_energy_ledger"],
        warnings=["Matter transport: not claimed", "PHYSICAL INTERPRETATION: YELLOW"],
    )
    return ModuleResult(
        module="lattice",
        status=Status.GREEN,
        claim_class=["IMPLEMENTED_SOFTWARE", "CONVENTIONAL_PHYSICS", "EXPLORATORY_MODEL"],
        input={"model": model},
        models=receipt["models"],
        result=payload,
        warnings=receipt["warnings"],
        receipt=receipt,
        does="64-state synthetic resonant lattice with energy ledger.",
        does_not="Does not transport matter.",
        tests=receipt["tests"],
        source=getattr(mod, "__name__", "rgcs_lab.reference.lattice"),
    )


def metasurface_sweep(**kwargs: Any) -> ModuleResult:
    mod = resolve("rgcs_metasurface", "rgcs_lab.reference.metasurface")
    payload = mod.sweep(**kwargs) if hasattr(mod, "sweep") else meta_ref.sweep(**kwargs)
    receipt = build_receipt(
        module="metasurface",
        status=Status.YELLOW.value,
        claim_class=["IMPLEMENTED_SOFTWARE", "CONVENTIONAL_PHYSICS", "UNDERDETERMINED"],
        inputs=kwargs or {"example": "corrugated-cell"},
        models=[payload.get("model", "corrugated-cell-sweep-v1")],
        result=payload,
        tests=["metasurface_energy_conservation"],
        warnings=[
            "HIGH-FIDELITY SPOOF-SPP SOLVER: YELLOW UNDERDETERMINED",
            "Does not modify gravity",
        ],
    )
    return ModuleResult(
        module="metasurface",
        status=Status.YELLOW,
        claim_class=["IMPLEMENTED_SOFTWARE", "CONVENTIONAL_PHYSICS", "UNDERDETERMINED"],
        input=kwargs or {"example": "corrugated-cell"},
        models=receipt["models"],
        result=payload,
        warnings=receipt["warnings"],
        receipt=receipt,
        does="Passive reduced-order spoof-SPP cell with energy accounting.",
        does_not="Does not modify gravity.",
        tests=receipt["tests"],
        source=getattr(mod, "__name__", "rgcs_lab.reference.metasurface"),
    )


def predictions_freeze(prediction: dict[str, Any]) -> ModuleResult:
    mod = resolve("rgcs_predictions", "rgcs_lab.reference.predictions")
    payload = (
        mod.freeze_prediction(prediction)
        if hasattr(mod, "freeze_prediction")
        else pred_ref.freeze_prediction(prediction)
    )
    receipt = build_receipt(
        module="predictions",
        status=Status.YELLOW.value,
        claim_class=["PROSPECTIVE_PREDICTION", "UNDERDETERMINED"],
        inputs={"prediction_id": prediction.get("prediction_id")},
        models=["prediction-freeze-v1"],
        result=payload,
        tests=["prediction_freeze_hash", "prediction_immutable_after_measure"],
        warnings=["Pending measurement — protocol frozen, mechanism not validated"],
    )
    return ModuleResult(
        module="predictions",
        status=Status.YELLOW,
        claim_class=["PROSPECTIVE_PREDICTION", "UNDERDETERMINED"],
        input={"prediction_id": prediction.get("prediction_id")},
        models=receipt["models"],
        result=payload,
        warnings=receipt["warnings"],
        receipt=receipt,
        does="Freeze prospective predictions and null controls before measurement.",
        does_not="Does not validate a mechanism merely because one outcome matches.",
        tests=receipt["tests"],
        source=getattr(mod, "__name__", "rgcs_lab.reference.predictions"),
    )


def predictions_verify(prediction: dict[str, Any]) -> ModuleResult:
    mod = resolve("rgcs_predictions", "rgcs_lab.reference.predictions")
    payload = (
        mod.verify_prediction(prediction)
        if hasattr(mod, "verify_prediction")
        else pred_ref.verify_prediction(prediction)
    )
    receipt = build_receipt(
        module="predictions",
        status=Status.YELLOW.value,
        claim_class=["PROSPECTIVE_PREDICTION", "UNDERDETERMINED"],
        inputs={"prediction_id": prediction.get("prediction_id")},
        models=["prediction-verify-v1"],
        result=payload,
        tests=["prediction_freeze_hash"],
        warnings=["Hash match freezes protocol only"],
    )
    return ModuleResult(
        module="predictions",
        status=Status.YELLOW,
        claim_class=["PROSPECTIVE_PREDICTION", "UNDERDETERMINED"],
        input={"prediction_id": prediction.get("prediction_id")},
        models=receipt["models"],
        result=payload,
        warnings=receipt["warnings"],
        receipt=receipt,
        does="Verify a frozen prediction hash.",
        does_not="Does not validate a physical mechanism.",
        tests=receipt["tests"],
        source=getattr(mod, "__name__", "rgcs_lab.reference.predictions"),
    )


def proofs_bundle() -> ModuleResult:
    """Aggregate catalog + sample receipts from live adapters."""
    samples = {
        "coordinate": coordinate.decode(165876523).receipt,
        "golay": golay.demo(flips_per_block=1).receipt,
        "frames": frames.example().receipt,
        "catalog": module_catalog(),
    }
    receipt = build_receipt(
        module="proofs",
        status=Status.GREEN.value,
        claim_class=["IMPLEMENTED_SOFTWARE"],
        inputs={},
        models=["hub-proof-aggregate-v1"],
        result=samples,
        tests=["hub_nine_modules", "receipt_schema"],
        warnings=["A green UI is not a physical proof"],
    )
    return ModuleResult(
        module="proofs",
        status=Status.GREEN,
        claim_class=["IMPLEMENTED_SOFTWARE"],
        input={},
        models=receipt["models"],
        result=samples,
        warnings=receipt["warnings"],
        receipt=receipt,
        does="Aggregate receipts, hashes, and claim-boundary surfaces.",
        does_not="Does not convert a green UI into a physical proof.",
        tests=receipt["tests"],
        source="rgcs_lab.adapters",
    )


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))
