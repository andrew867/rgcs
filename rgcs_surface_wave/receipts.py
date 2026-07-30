"""R10.15 Phase F33 — hash-addressed evidence receipts and bundles.

Every public command emits a receipt carrying inputs, input hashes,
software and environment versions, the evidence class, limitations,
and the standing nonclaim. Bundles are content-addressed so a third
party can verify that the outputs match the declared inputs.
"""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

from rgcs_surface_wave import NONCLAIM, PUBLICATION_STATUS, __version__
from rgcs_surface_wave.evidence import ClaimClass


def _pkg_versions() -> dict:
    out = {"python": platform.python_version(),
           "rgcs_surface_wave": __version__}
    for mod in ("numpy", "scipy"):
        try:
            out[mod] = __import__(mod).__version__
        except Exception:                       # pragma: no cover
            out[mod] = "unavailable"
    return out


def canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      default=str, allow_nan=False)


def content_hash(obj) -> str:
    return hashlib.sha256(canonical(obj).encode()).hexdigest()


def source_commit() -> str | None:
    try:
        r = subprocess.run(["git", "rev-parse", "HEAD"],
                           capture_output=True, text=True, timeout=30,
                           cwd=Path(__file__).resolve().parents[1])
        return r.stdout.strip() or None
    except Exception:                           # pragma: no cover
        return None


def make_receipt(command: str, inputs: dict, outputs: dict,
                 claim_class: str, limitations: list[str],
                 uncertainty: dict | None = None) -> dict:
    cc = ClaimClass(claim_class)
    body = {
        "schema": "rgcs.r1015.receipt.v1",
        "command": command,
        "inputs": inputs,
        "input_hash": content_hash(inputs),
        "outputs": outputs,
        "evidence_class": cc.value,
        "limitations": limitations,
        "uncertainty": uncertainty or {},
        "software": _pkg_versions(),
        "source_commit": source_commit(),
        "publication_status": PUBLICATION_STATUS,
        "nonclaim": NONCLAIM,
    }
    body["receipt_hash"] = content_hash(
        {k: v for k, v in body.items() if k != "receipt_hash"})
    return body


def verify_receipt(receipt: dict) -> dict:
    stored = receipt.get("receipt_hash")
    recomputed = content_hash(
        {k: v for k, v in receipt.items() if k != "receipt_hash"})
    input_ok = receipt.get("input_hash") == content_hash(
        receipt.get("inputs", {}))
    required = ("command", "evidence_class", "software", "nonclaim",
                "limitations")
    missing = [k for k in required if k not in receipt]
    return {"hash_ok": stored == recomputed, "input_hash_ok": input_ok,
            "missing_fields": missing,
            "ok": stored == recomputed and input_ok and not missing}


def write_bundle(out_dir, receipts: list[dict],
                 extra_files: dict | None = None) -> dict:
    d = Path(out_dir)
    d.mkdir(parents=True, exist_ok=True)
    for i, r in enumerate(receipts):
        (d / f"receipt_{i:02d}_{r['command'].replace(' ', '_')}.json") \
            .write_text(json.dumps(r, indent=2, default=str) + "\n",
                        encoding="utf-8")
    for name, content in (extra_files or {}).items():
        p = d / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content if isinstance(content, str)
                     else json.dumps(content, indent=2, default=str)
                     + "\n", encoding="utf-8")
    manifest = {"schema": "rgcs.r1015.bundle.v1",
                "publication_status": PUBLICATION_STATUS,
                "upload": "FORBIDDEN",
                "nonclaim": NONCLAIM, "contents": {}}
    for f in sorted(d.rglob("*")):
        if f.is_file() and f.name not in ("BUNDLE_MANIFEST.json",
                                          "SHA256SUMS.txt"):
            manifest["contents"][f.relative_to(d).as_posix()] = \
                hashlib.sha256(f.read_bytes()).hexdigest()
    (d / "BUNDLE_MANIFEST.json").write_text(
        json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
    (d / "SHA256SUMS.txt").write_text(
        "\n".join(f"{h}  {n}" for n, h in manifest["contents"].items())
        + "\n", encoding="utf-8")
    return manifest


def verify_bundle(bundle_dir) -> dict:
    d = Path(bundle_dir)
    mf = d / "BUNDLE_MANIFEST.json"
    if not mf.is_file():
        return {"ok": False, "error": f"no BUNDLE_MANIFEST.json in {d}"}
    manifest = json.loads(mf.read_text(encoding="utf-8"))
    bad, missing = [], []
    for rel, h in manifest.get("contents", {}).items():
        f = d / rel
        if not f.is_file():
            missing.append(rel)
        elif hashlib.sha256(f.read_bytes()).hexdigest() != h:
            bad.append(rel)
    receipts_ok = True
    for f in d.glob("receipt_*.json"):
        r = json.loads(f.read_text(encoding="utf-8"))
        if not verify_receipt(r)["ok"]:
            receipts_ok = False
    return {"ok": not bad and not missing and receipts_ok,
            "checked": len(manifest.get("contents", {})),
            "hash_mismatch": bad, "missing": missing,
            "receipts_valid": receipts_ok}
