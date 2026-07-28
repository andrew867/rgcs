"""R10.13 — plain-language reports and proof bundles for one specimen.

The report leads with what was calculated and what it means, never
with raw arrays. The proof bundle is a hashed directory a third party
can verify with ``rgcs bundle verify``.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from r1013.errors import UserError
from r1013.specimen import canonical_json, validate


def _fmt_hz(f: float) -> str:
    if f >= 1e6:
        return f"{f / 1e6:.3f} MHz"
    if f >= 1e3:
        return f"{f / 1e3:.3f} kHz"
    return f"{f:.1f} Hz"


def find_latest(base=".") -> Path:
    """Resolve --from latest: newest result JSON under ./rgcs-results."""
    root = Path(base) / "rgcs-results"
    cands = sorted(root.glob("**/*.json"),
                   key=lambda p: p.stat().st_mtime) if root.is_dir() \
        else []
    if not cands:
        raise UserError("RGCS-E014", "No previous results found under "
                        "./rgcs-results; run a calculation first or "
                        "pass an explicit result directory.")
    return cands[-1]


def write_report(rec: dict, results: list[dict], out_dir) -> Path:
    """Human report: input, validation, equations/assumptions,
    frequency table, warnings, hashes."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    v = validate(rec)
    lines = []
    lines.append(f"# RGCS report for {rec.get('name')} "
                 f"({rec.get('specimen_id')})")
    lines.append("")
    lines.append("This report contains computed candidate frequencies. "
                 "A computed frequency is not a measured resonance.")
    lines.append("")
    lines.append("## Specimen")
    geo = rec.get("geometry", {})
    lines.append(f"- material: {rec.get('material', {}).get('material_id')}")
    lines.append(f"- length: {geo.get('length_mm')} mm")
    lines.append(f"- wide diameter: {geo.get('wide_diameter_mm')} mm "
                 f"({geo.get('diameter_mode')})")
    lines.append(f"- narrow diameter: {geo.get('narrow_diameter_mm')} mm")
    lines.append(f"- validation: {'PASS' if v['ok'] else 'FAIL'}, "
                 f"{len(v['warnings'])} warning(s)")
    lines.append(f"- specimen hash: {v['specimen_hash']}")
    for w in v["warnings"]:
        lines.append(f"  - warning: {w}")
    for res in results:
        kind = res.get("result_kind") or res.get("model") or "result"
        lines.append("")
        lines.append(f"## {kind}")
        ev = res.get("evidence_class")
        lines.append(f"- evidence class: {ev}")
        if "estimates" in res:
            lines.append(f"- speed used: {res['speed_m_s']:.1f} m/s")
            lines.append("")
            lines.append("| model | harmonic | frequency | +- |")
            lines.append("|---|---|---|---|")
            for e in res["estimates"]:
                lines.append(
                    f"| {e['model']} | {e['harmonic']} | "
                    f"{_fmt_hz(e['frequency_hz'])} | "
                    f"{_fmt_hz(e['uncertainty_hz'])} |")
            lines.append("")
            lines.append(f"Assumptions: {res['estimates'][0]['path_note']}; "
                         f"{res['estimates'][0]['boundary_assumption']}.")
        elif "frequencies_hz" in res:
            lines.append("")
            lines.append("| mode | frequency |")
            lines.append("|---|---|")
            for i, f in enumerate(res["frequencies_hz"], 1):
                lines.append(f"| {i} | {_fmt_hz(f)} |")
        for w in res.get("warnings", []):
            lines.append(f"- warning: {w}")
    lines.append("")
    lines.append("## Reproduction")
    lines.append("The specimen file, results, and hashes in this "
                 "folder let another RGCS install reproduce every "
                 "number. Verify with: rgcs bundle verify FOLDER")
    p = out / "REPORT.md"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    (out / "specimen.json").write_text(canonical_json(rec) + "\n",
                                       encoding="utf-8")
    (out / "results.json").write_text(
        json.dumps([{k: v2 for k, v2 in r.items()
                     if not k.startswith("_")} for r in results],
                   indent=2, default=str) + "\n", encoding="utf-8")
    return p


def write_bundle(rec: dict, result_dir, out_dir) -> dict:
    """Proof bundle: copy result dir + manifest + SHA256SUMS."""
    src = Path(result_dir)
    if not src.is_dir():
        raise UserError("RGCS-E014", f"'{src}' is not a result "
                        "directory.")
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    import shutil
    for f in src.rglob("*"):
        if f.is_file():
            rel = f.relative_to(src)
            dst = out / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, dst)
    (out / "specimen.json").write_text(canonical_json(rec) + "\n",
                                       encoding="utf-8")
    manifest = {"schema": "rgcs.proof-bundle/1.0",
                "specimen_id": rec.get("specimen_id"), "contents": {}}
    for f in sorted(out.rglob("*")):
        if f.is_file() and f.name not in ("BUNDLE_MANIFEST.json",
                                          "SHA256SUMS.txt"):
            manifest["contents"][f.relative_to(out).as_posix()] = \
                hashlib.sha256(f.read_bytes()).hexdigest()
    (out / "BUNDLE_MANIFEST.json").write_text(
        json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
    (out / "SHA256SUMS.txt").write_text(
        "\n".join(f"{h}  {n}" for n, h in manifest["contents"].items())
        + "\n", encoding="utf-8")
    return manifest


def verify_bundle(bundle_dir) -> dict:
    b = Path(bundle_dir)
    mf = b / "BUNDLE_MANIFEST.json"
    if not mf.is_file():
        raise UserError("RGCS-E014", f"'{b}' has no "
                        "BUNDLE_MANIFEST.json; it is not a proof "
                        "bundle.")
    manifest = json.loads(mf.read_text(encoding="utf-8"))
    bad, missing = [], []
    for rel, h in manifest.get("contents", {}).items():
        f = b / rel
        if not f.is_file():
            missing.append(rel)
        elif hashlib.sha256(f.read_bytes()).hexdigest() != h:
            bad.append(rel)
    return {"ok": not bad and not missing, "checked":
            len(manifest.get("contents", {})), "hash_mismatch": bad,
            "missing": missing}
