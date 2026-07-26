"""Memory, dual-pole, lattice, metasurface, predictions, proofs adapters.

Each adapter executes the bundled Codex core (``rgcs_lab.memory``,
``rgcs_lab.dual_pole``, ``rgcs_lab.lattice``, ``rgcs_lab.metasurface``)
and reshapes its payload into the hub envelope. The labelled reference
demos remain only as an explicit fallback mode that can never report
GREEN. Predictions has no Codex core by design: the hub demo is the
Cursor reference implementation and stays YELLOW; the authority-side
registry contract lives in ``rgcs_lab.authority.prediction_registry``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rgcs_lab.adapters import coordinate, frames, golay
from rgcs_lab.adapters import guard_fallback, resolve_core
from rgcs_lab.common.receipts import build_receipt
from rgcs_lab.common.status import ModuleResult, Status, module_catalog
from rgcs_lab.reference import predictions as pred_ref


def default_memory_corpus() -> Path:
    """Path to the packaged provenance-memory corpus."""
    from importlib import resources

    return Path(str(resources.files("rgcs_lab.data"))) / "memory_corpus"


def memory_benchmark(query: str = "golay bit flips transport wrapper") -> ModuleResult:
    core, backend = resolve_core("rgcs_lab.memory", "rgcs_lab.reference.memory")
    if backend == "codex":
        corpus = default_memory_corpus()
        rec = core.run_benchmark(corpus, query=query, top_k=3)
        payload = dict(rec["result"])
        flagship = payload["rankings"]["complete_proposed_system"]
        payload["model"] = "codex-multi-system-retrieval-v1"
        payload["top_system"] = "complete_proposed_system"
        payload["top_id"] = Path(flagship[0]).stem if flagship else None
        source = core.__name__
    else:  # labelled reference fallback (never GREEN)
        payload = core.run_benchmark(query)
        source = core.__name__
    warnings = ["CONSCIOUSNESS: not demonstrated", f"backend={source}"]
    status = guard_fallback(Status.GREEN, backend, warnings)
    receipt = build_receipt(
        module="memory",
        status=status.value,
        claim_class=["IMPLEMENTED_SOFTWARE", "EXPLORATORY_MODEL"],
        inputs={"query": query},
        models=[payload.get("model", "bag-of-tokens-overlap-v1")],
        result=payload,
        tests=["memory_benchmark_digest", "tests/rgcs_lab/test_memory_dual.py"],
        warnings=warnings,
    )
    return ModuleResult(
        module="memory",
        status=status,
        claim_class=["IMPLEMENTED_SOFTWARE", "EXPLORATORY_MODEL"],
        input={"query": query},
        models=receipt["models"],
        result=payload,
        warnings=receipt["warnings"],
        receipt=receipt,
        does="Reproducible provenance-memory retrieval benchmark.",
        does_not="Does not demonstrate consciousness.",
        tests=receipt["tests"],
        source=source,
    )


#: Codex dual-pole verdicts -> hub decision vocabulary.
_DECISION_MAP = {
    "BLOCK": "REJECT",
    "ACCEPT_GREEN": "ACCEPT",
    "ACCEPT_YELLOW": "ACCEPT_YELLOW",
}


def _redact_banned(obj: Any) -> Any:
    """Replace banned public wording in echoed text (Authority Lock).

    The dual-pole audit must be able to REJECT a claim that quotes
    banned wording without echoing that wording into its own result
    payload or receipt — otherwise the envelope's SchemaError refusal
    fires and no REJECT receipt can be produced (audit finding AA-02).
    The critic still sees the ORIGINAL text; only the echo is redacted.
    """
    from rgcs_lab.common.status_schema import BANNED_WORDING

    if isinstance(obj, str):
        low = obj.lower()
        for banned in BANNED_WORDING:
            idx = low.find(banned)
            while idx != -1:
                obj = obj[:idx] + "[REDACTED-BANNED-WORDING]" + obj[idx + len(banned):]
                low = obj.lower()
                idx = low.find(banned)
        return obj
    if isinstance(obj, dict):
        return {k: _redact_banned(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_redact_banned(v) for v in obj]
    return obj


def dual_pole_audit(claim: dict[str, Any]) -> ModuleResult:
    core, backend = resolve_core("rgcs_lab.dual_pole", "rgcs_lab.reference.dual_pole")
    if backend == "codex":
        codex_claim = dict(claim)
        if "proposal" not in codex_claim and "statement" in codex_claim:
            codex_claim["proposal"] = codex_claim["statement"]
        raw = _redact_banned(core.audit_claim(codex_claim))
        verdict = str(raw["verdict"])
        payload = dict(raw)
        payload["decision"] = _DECISION_MAP.get(verdict, "REJECT")
        payload["attacks"] = list(raw.get("findings", []))
        # The critic cannot be bypassed: a block survives unless new
        # evidence or a TYPED operator waiver is recorded — and a
        # recorded waiver is not a bypass.
        payload["critic_bypassed"] = False
        if verdict == "BLOCK":
            status = Status.RED
        elif verdict == "ACCEPT_GREEN":
            status = Status.GREEN
        else:
            status = Status.YELLOW
        source = core.__name__
    else:  # labelled reference fallback (never GREEN)
        payload = _redact_banned(core.audit_claim(claim))
        status = Status[payload.get("status", "YELLOW")]
        source = core.__name__
    warnings = ["Independent witness status: not established",
                f"backend={source}"]
    status = guard_fallback(status, backend, warnings)
    receipt = build_receipt(
        module="dual_pole",
        status=status.value,
        claim_class=["IMPLEMENTED_SOFTWARE", "EXPLORATORY_MODEL"],
        inputs={"claim": _redact_banned(claim)},
        models=["dual-pole-state-machine-v1"],
        result=payload,
        tests=["dual_pole_critic_not_bypassed",
               "tests/rgcs_lab/test_memory_dual.py"],
        warnings=warnings,
    )
    return ModuleResult(
        module="dual_pole",
        status=status,
        claim_class=["IMPLEMENTED_SOFTWARE", "EXPLORATORY_MODEL"],
        input={"claim": _redact_banned(claim)},
        models=receipt["models"],
        result=payload,
        warnings=receipt["warnings"],
        receipt=receipt,
        does="Proposer/critic loop with typed attack families.",
        does_not="Does not make two models independent witnesses.",
        tests=receipt["tests"],
        source=source,
    )


#: Named lattice examples -> Codex LatticeConfig arguments.
_LATTICE_MODELS = {
    "counterrotating-ring": {"directed_phase_rad": 0.3},
    "lossless-ring": {},
    "damped-ring": {"damping_s": 0.1},
}


def lattice_run(model: str = "counterrotating-ring") -> ModuleResult:
    core, backend = resolve_core("rgcs_lab.lattice", "rgcs_lab.reference.lattice")
    if backend == "codex":
        if model not in _LATTICE_MODELS:
            raise ValueError(
                f"unknown lattice model {model!r}; known: {sorted(_LATTICE_MODELS)}")
        import numpy as np

        cfg = core.LatticeConfig(steps=100, dt_s=0.001,
                                 **_LATTICE_MODELS[model])
        rec = core.simulate(cfg)
        payload = dict(rec["result"])
        h = core.hermitian_ring_hamiltonian(cfg)
        payload["hermitian_residual"] = float(np.max(np.abs(h - h.conj().T)))
        payload["model"] = model
        drift_ok = abs(payload["energy_ledger"]["numerical_drift"]) < 1e-6
        status = Status.GREEN if drift_ok else Status.YELLOW
        source = core.__name__
    else:  # labelled reference fallback (never GREEN)
        payload = core.run_example(model=model)
        status = Status.YELLOW
        source = core.__name__
    warnings = ["Matter transport: not claimed",
                "PHYSICAL INTERPRETATION: YELLOW",
                f"backend={source}"]
    status = guard_fallback(status, backend, warnings)
    receipt = build_receipt(
        module="lattice",
        status=status.value,
        claim_class=["IMPLEMENTED_SOFTWARE", "CONVENTIONAL_PHYSICS", "EXPLORATORY_MODEL"],
        inputs={"model": model},
        models=[model],
        result=payload,
        tests=["lattice_hermitian", "lattice_energy_ledger",
               "tests/rgcs_lab/test_lattice.py"],
        warnings=warnings,
    )
    return ModuleResult(
        module="lattice",
        status=status,
        claim_class=["IMPLEMENTED_SOFTWARE", "CONVENTIONAL_PHYSICS", "EXPLORATORY_MODEL"],
        input={"model": model},
        models=receipt["models"],
        result=payload,
        warnings=receipt["warnings"],
        receipt=receipt,
        does="64-state synthetic resonant lattice with energy ledger.",
        does_not="Does not transport matter.",
        tests=receipt["tests"],
        source=source,
    )


def metasurface_sweep(**kwargs: Any) -> ModuleResult:
    core, backend = resolve_core("rgcs_lab.metasurface",
                                 "rgcs_lab.reference.metasurface")
    if backend == "codex":
        cfg_kwargs: dict[str, Any] = {}
        unmapped: list[str] = []
        if "period_m" in kwargs:
            cfg_kwargs["period_m"] = kwargs["period_m"]
        freqs = kwargs.get("frequencies_hz")
        if freqs:
            cfg_kwargs["f_min_hz"] = float(min(freqs))
            cfg_kwargs["f_max_hz"] = float(max(freqs))
            cfg_kwargs["points"] = max(len(freqs), 2)
        for extra in ("groove_depth_m", "loss_tan"):
            if extra in kwargs:
                unmapped.append(extra)
        rec = core.sweep(core.MetasurfaceConfig(**cfg_kwargs))
        payload = dict(rec["result"])
        payload["model"] = "passive-rlcg-spoof-spp-line-v1"
        payload["max_conservation_residual"] = (
            payload["power_ledger"]["numerical_residual"])
        if unmapped:
            payload["unmapped_inputs"] = sorted(unmapped)
        source = core.__name__
    else:  # labelled reference fallback (already YELLOW)
        payload = core.sweep(**kwargs)
        source = core.__name__
    warnings = [
        "HIGH-FIDELITY SPOOF-SPP SOLVER: YELLOW UNDERDETERMINED",
        "Does not modify gravity",
        f"backend={source}",
    ]
    if backend == "codex" and payload.get("unmapped_inputs"):
        warnings.append(
            "inputs not represented in the reduced-order RLCG core: "
            + ", ".join(payload["unmapped_inputs"]))
    status = guard_fallback(Status.YELLOW, backend, warnings)
    receipt = build_receipt(
        module="metasurface",
        status=status.value,
        claim_class=["IMPLEMENTED_SOFTWARE", "CONVENTIONAL_PHYSICS", "UNDERDETERMINED"],
        inputs=kwargs or {"example": "corrugated-cell"},
        models=[payload.get("model", "corrugated-cell-sweep-v1")],
        result=payload,
        tests=["metasurface_energy_conservation",
               "tests/rgcs_lab/test_metasurface.py"],
        warnings=warnings,
    )
    return ModuleResult(
        module="metasurface",
        status=status,
        claim_class=["IMPLEMENTED_SOFTWARE", "CONVENTIONAL_PHYSICS", "UNDERDETERMINED"],
        input=kwargs or {"example": "corrugated-cell"},
        models=receipt["models"],
        result=payload,
        warnings=receipt["warnings"],
        receipt=receipt,
        does="Passive reduced-order spoof-SPP cell with energy accounting.",
        does_not="Does not modify gravity.",
        tests=receipt["tests"],
        source=source,
    )


def predictions_freeze(prediction: dict[str, Any]) -> ModuleResult:
    payload = pred_ref.freeze_prediction(prediction)
    receipt = build_receipt(
        module="predictions",
        status=Status.YELLOW.value,
        claim_class=["PROSPECTIVE_PREDICTION", "UNDERDETERMINED"],
        inputs={"prediction_id": prediction.get("prediction_id")},
        models=["prediction-freeze-v1"],
        result=payload,
        tests=["prediction_freeze_hash", "prediction_immutable_after_measure"],
        warnings=["Pending measurement — protocol frozen, mechanism not validated",
                  "backend=rgcs_lab.reference.predictions (hub demo; "
                  "authority contract: rgcs_lab.authority.prediction_registry)"],
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
        source="rgcs_lab.reference.predictions",
    )


def predictions_verify(prediction: dict[str, Any]) -> ModuleResult:
    payload = pred_ref.verify_prediction(prediction)
    receipt = build_receipt(
        module="predictions",
        status=Status.YELLOW.value,
        claim_class=["PROSPECTIVE_PREDICTION", "UNDERDETERMINED"],
        inputs={"prediction_id": prediction.get("prediction_id")},
        models=["prediction-verify-v1"],
        result=payload,
        tests=["prediction_freeze_hash"],
        warnings=["Hash match freezes protocol only",
                  "backend=rgcs_lab.reference.predictions (hub demo; "
                  "authority contract: rgcs_lab.authority.prediction_registry)"],
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
        source="rgcs_lab.reference.predictions",
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
