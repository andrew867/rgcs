"""FastAPI application for the Recursive Infrastructure Lab."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from rgcs_lab import PRODUCT_HEADLINE, PRODUCT_NAME, __version__
from rgcs_lab.adapters import coordinate, frames, golay
from rgcs_lab.adapters import services
from rgcs_lab.common.privacy import PrivacyDefaults, privacy_banner
from rgcs_lab.common.status import module_catalog

REPO_ROOT = Path(__file__).resolve().parents[2]
STATIC_HUB = REPO_ROOT / "static" / "hub"
WORKBENCH = REPO_ROOT / "workbench"


class DecodeBody(BaseModel):
    raw: str | int = "165876523"


class GolayBody(BaseModel):
    flips_per_block: int = 1
    seed: int = 1


class FramesBody(BaseModel):
    example: str = "earth-south-up"


class MemoryBody(BaseModel):
    query: str = "golay bit flips transport wrapper"


class DualPoleBody(BaseModel):
    claim: dict[str, Any] = Field(default_factory=dict)


class LatticeBody(BaseModel):
    model: str = "counterrotating-ring"


class MetasurfaceBody(BaseModel):
    frequencies_hz: list[float] | None = None
    groove_depth_m: float = 2.0e-3
    period_m: float = 5.0e-3
    loss_tan: float = 0.01


class PredictionBody(BaseModel):
    prediction: dict[str, Any]


def create_app() -> FastAPI:
    privacy = PrivacyDefaults()
    app = FastAPI(
        title=PRODUCT_NAME,
        version=__version__,
        description=PRODUCT_HEADLINE,
    )

    @app.get("/api/health")
    def health() -> dict[str, Any]:
        return {
            "ok": True,
            "product": PRODUCT_NAME,
            "version": __version__,
            "privacy": privacy_banner(),
            "bind_default": f"{privacy.bind_host}:{privacy.bind_port}",
            "telemetry": privacy.telemetry,
        }

    @app.get("/api/modules")
    def modules() -> dict[str, Any]:
        return {"modules": module_catalog()}

    @app.post("/api/coordinate/decode")
    def api_coordinate_decode(body: DecodeBody) -> dict[str, Any]:
        try:
            return coordinate.decode(body.raw).to_dict()
        except Exception as exc:  # noqa: BLE001 — surface as 400
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/golay/demo")
    def api_golay(body: GolayBody) -> dict[str, Any]:
        return golay.demo(body.flips_per_block, body.seed).to_dict()

    @app.post("/api/frames/example")
    def api_frames(body: FramesBody) -> dict[str, Any]:
        try:
            return frames.example(body.example).to_dict()
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/memory/benchmark")
    def api_memory(body: MemoryBody) -> dict[str, Any]:
        return services.memory_benchmark(body.query).to_dict()

    @app.post("/api/dual_pole/audit")
    def api_dual(body: DualPoleBody) -> dict[str, Any]:
        return services.dual_pole_audit(body.claim).to_dict()

    @app.post("/api/lattice/run")
    def api_lattice(body: LatticeBody) -> dict[str, Any]:
        try:
            return services.lattice_run(body.model).to_dict()
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/metasurface/sweep")
    def api_meta(body: MetasurfaceBody) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "groove_depth_m": body.groove_depth_m,
            "period_m": body.period_m,
            "loss_tan": body.loss_tan,
        }
        if body.frequencies_hz is not None:
            kwargs["frequencies_hz"] = body.frequencies_hz
        return services.metasurface_sweep(**kwargs).to_dict()

    @app.post("/api/predictions/freeze")
    def api_pred_freeze(body: PredictionBody) -> dict[str, Any]:
        try:
            return services.predictions_freeze(body.prediction).to_dict()
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/predictions/verify")
    def api_pred_verify(body: PredictionBody) -> dict[str, Any]:
        return services.predictions_verify(body.prediction).to_dict()

    @app.get("/api/proofs")
    def api_proofs() -> dict[str, Any]:
        return services.proofs_bundle().to_dict()

    @app.get("/api/receipts/{module}")
    def api_receipt(module: str) -> Response:
        mapping = {
            "coordinate": lambda: coordinate.decode(165876523),
            "golay": lambda: golay.demo(1),
            "frames": lambda: frames.example(),
            "memory": lambda: services.memory_benchmark(),
            "dual_pole": lambda: services.dual_pole_audit({
                "statement": "exact structural decode of 165876523",
                "claim_class": ["EXACT_ARITHMETIC"],
                "evidence": ["golden_vector"],
            }),
            "lattice": lambda: services.lattice_run(),
            "metasurface": lambda: services.metasurface_sweep(),
            "predictions": lambda: services.predictions_freeze({
                "prediction_id": "EXAMPLE-RESIDUAL-FORCE-001",
                "hypothesis": "phase-dependent residual may appear",
                "controls": ["unpowered", "detuned"],
            }),
            "proofs": services.proofs_bundle,
        }
        if module not in mapping:
            raise HTTPException(status_code=404, detail="unknown module")
        result = mapping[module]()
        payload = json.dumps(result.receipt, indent=2) + "\n"
        return Response(
            content=payload,
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="{module}-receipt.json"'
            },
        )

    if STATIC_HUB.is_dir():
        app.mount("/hub", StaticFiles(directory=str(STATIC_HUB), html=True),
                  name="hub")

    @app.get("/")
    def root() -> HTMLResponse:
        index = STATIC_HUB / "index.html"
        if index.is_file():
            return HTMLResponse(index.read_text(encoding="utf-8"))
        return HTMLResponse(
            f"<h1>{PRODUCT_NAME}</h1><p>{PRODUCT_HEADLINE}</p>"
            "<p>Static hub not built yet. See /api/health.</p>"
        )

    @app.get("/workbench")
    def workbench() -> FileResponse:
        path = WORKBENCH / "index.html"
        if not path.is_file():
            raise HTTPException(status_code=404, detail="workbench missing")
        return FileResponse(path)

    return app


app = create_app()
