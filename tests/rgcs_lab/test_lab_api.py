"""API and package smoke tests for rgcs_lab."""

from __future__ import annotations

import json

import pytest

fastapi = pytest.importorskip("fastapi")
httpx = pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from rgcs_lab.api import create_app


@pytest.fixture
def client():
    return TestClient(create_app())


def test_health_and_modules(client):
    h = client.get("/api/health").json()
    assert h["ok"] is True
    assert h["telemetry"] is False
    mods = client.get("/api/modules").json()["modules"]
    assert len(mods) == 9


def test_coordinate_and_receipt_download(client):
    r = client.post("/api/coordinate/decode", json={"raw": "165876523"})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "GREEN"
    assert body["result"]["physical_projection_status"] == "UNDERDETERMINED"
    receipt = client.get("/api/receipts/coordinate")
    assert receipt.status_code == 200
    assert "attachment" in receipt.headers.get("content-disposition", "")
    payload = json.loads(receipt.text)
    assert payload["module"] == "coordinate"


def test_yellow_modules_stay_yellow(client):
    meta = client.post("/api/metasurface/sweep", json={}).json()
    assert meta["status"] == "YELLOW"
    pred = client.post("/api/predictions/freeze", json={
        "prediction": {
            "prediction_id": "API-1",
            "hypothesis": "residual may appear",
            "controls": ["unpowered"],
        }
    }).json()
    assert pred["status"] == "YELLOW"


def test_hub_index_served(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "Recursive Infrastructure Lab" in r.text
