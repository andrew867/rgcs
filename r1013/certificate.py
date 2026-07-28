"""R10.13 Phase 18 — result certificates (rgcs.result-certificate/1.0).

Every calculation can be sealed into a certificate carrying the
specimen hash, material record, fixture, orientation, mesh manifest,
solver identity, uncertainty, evidence class, warnings, refusals, and
a content hash. Software output can never carry the MEASUREMENT class.
"""

from __future__ import annotations

import hashlib
import json
import platform
from pathlib import Path

from r1013 import (CERTIFICATE_SCHEMA_VERSION, SOFTWARE_EMITTABLE,
                   __version__)
from r1013.errors import UserError
from r1013.specimen import specimen_hash


def build_certificate(rec: dict, result: dict, result_kind: str,
                      mesh_manifest: dict | None = None,
                      fixture: dict | None = None) -> dict:
    ev = result.get("evidence_class")
    if ev not in SOFTWARE_EMITTABLE:
        raise UserError("RGCS-E015",
                        f"evidence class {ev!r} cannot be emitted by "
                        "software; computed output is never a "
                        "measurement.")
    body = {
        "schema_version": CERTIFICATE_SCHEMA_VERSION,
        "result_id": f"{rec.get('specimen_id', 'unknown')}-{result_kind}",
        "status": "COMPLETED",
        "evidence_class": ev,
        "result_kind": result_kind,
        "specimen": {"specimen_id": rec.get("specimen_id"),
                     "hash": specimen_hash(rec)},
        "material": rec.get("material"),
        "orientation": rec.get("orientation"),
        "fixture": fixture,
        "mesh_manifest": mesh_manifest,
        "input_hashes": {"specimen_sha256": specimen_hash(rec)},
        "software": {"package": "rgcs", "module": "r1013",
                     "version": __version__,
                     "python": platform.python_version(),
                     "numerical_authority": "CPU float64 (DV4-004)"},
        "frequencies_hz": result.get("frequencies_hz")
        or [e["frequency_hz"] for e in result.get("estimates", [])],
        "warnings": result.get("warnings", []),
        "refusals": result.get("refusals", []),
        "result": {k: v for k, v in result.items()
                   if not k.startswith("_")},
    }
    canon = json.dumps(body, sort_keys=True, separators=(",", ":"),
                       default=str)
    body["certificate_sha256"] = hashlib.sha256(canon.encode()).hexdigest()
    return body


def verify_certificate(cert: dict) -> dict:
    stored = cert.get("certificate_sha256")
    body = {k: v for k, v in cert.items() if k != "certificate_sha256"}
    canon = json.dumps(body, sort_keys=True, separators=(",", ":"),
                       default=str)
    ok = hashlib.sha256(canon.encode()).hexdigest() == stored
    missing = [k for k in ("schema_version", "result_id", "status",
                           "evidence_class", "input_hashes", "software")
               if k not in cert]
    return {"hash_ok": ok, "missing_required": missing,
            "ok": ok and not missing}


def load_certificate(path) -> dict:
    p = Path(path)
    if not p.is_file():
        raise UserError("RGCS-E014", f"No certificate at '{p}'.")
    return json.loads(p.read_text(encoding="utf-8"))
