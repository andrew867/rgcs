#!/usr/bin/env python3
"""Generate static hub fixtures, receipts, and module pages from live adapters."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from rgcs_lab.adapters import coordinate, frames, golay
from rgcs_lab.adapters import services
from rgcs_lab.common.status import module_catalog
from rgcs_lab.reference import predictions as pred_ref

ROOT = Path(__file__).resolve().parents[2]
HUB = ROOT / "static" / "hub"
FIX = HUB / "fixtures"
REC = HUB / "receipts"
MOD = HUB / "modules"
EXAMPLES = ROOT / "examples" / "lab"
WB = ROOT / "workbench" / "index.html"


MODULE_META = {m["id"]: m for m in module_catalog()}


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")


def module_page(mod_id: str, title: str, does: str, does_not: str,
                status: str, phys: str) -> str:
    api_paths = {
        "coordinate": ("/api/coordinate/decode", '{"raw":"165876523"}'),
        "golay": ("/api/golay/demo", '{"flips_per_block":1,"seed":1}'),
        "frames": ("/api/frames/example", '{"example":"earth-south-up"}'),
        "memory": ("/api/memory/benchmark", '{"query":"golay bit flips transport wrapper"}'),
        "dual_pole": ("/api/dual_pole/audit",
                      '{"claim":{"statement":"exact structural decode","claim_class":["EXACT_ARITHMETIC"],"evidence":["golden"]}}'),
        "lattice": ("/api/lattice/run", '{"model":"counterrotating-ring"}'),
        "metasurface": ("/api/metasurface/sweep", "{}"),
        "predictions": ("/api/predictions/freeze",
                        '{"prediction":{"prediction_id":"EXAMPLE-RESIDUAL-FORCE-001","hypothesis":"phase-dependent residual may appear","controls":["unpowered","detuned"]}}'),
        "proofs": ("/api/proofs", None),
    }
    path, body = api_paths[mod_id]
    live_note = (
        "Server mode calls the Python domain API. Static mode loads a golden fixture — "
        "no Golay/quaternion/solver math is reimplemented in the browser."
    )
    extra = ""
    if mod_id == "coordinate":
        extra = '<p><a href="../../workbench/index.html">Open approved standalone structural decoder</a></p>'
    method = "GET" if body is None else "POST"
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>{title} · RGCS Lab</title>
<link rel="stylesheet" href="../assets/hub.css">
</head>
<body>
<main class="module-page hero">
  <p><a href="../index.html">← Hub</a></p>
  <p class="brand">{title}</p>
  <div class="badges">
    <span class="badge {status}">{status}</span>
    <span class="badge YELLOW phys">PHYS {phys}</span>
  </div>
  <section>
    <h2>WHAT THIS DOES</h2>
    <p>{does}</p>
    <h2>WHAT THIS DOES NOT DO</h2>
    <p class="does-not">{does_not}</p>
    <h2>STATUS</h2>
    <p>Implementation <strong>{status}</strong>. Physical lane <strong>{phys}</strong>.</p>
    {extra}
    <h2>INPUT</h2>
    <p>{live_note}</p>
    <div class="hero-actions">
      <button class="btn" type="button" id="run">Run example</button>
      <button class="btn secondary" type="button" id="download-trace">Download trace JSON</button>
      <a class="btn secondary" href="../receipts/{mod_id}.json" download>Download receipt</a>
    </div>
    <h2>TRACE / RESULT</h2>
    <pre id="out">Press Run example.</pre>
    <h2>TESTS</h2>
    <p id="tests">Listed inside the receipt.</p>
    <h2 id="source">SOURCE</h2>
    <p>Python adapters under <code>rgcs_lab/adapters</code>; coordinate domain API is <code>rgcs_coordinate</code>.</p>
  </section>
</main>
<script src="../assets/hub.js"></script>
<script>
const PATH = {path!r};
const BODY = {body if body is not None else 'null'};
const METHOD = {method!r};
let last = null;
async function run() {{
  const out = document.getElementById('out');
  out.textContent = 'Running…';
  try {{
    if (METHOD === 'GET') {{
      if (location.protocol === 'file:') {{
        last = await fetch('../fixtures/{mod_id}.json').then(r => r.json());
      }} else {{
        try {{
          last = await fetch(PATH).then(r => r.json());
        }} catch (e) {{
          last = await fetch('../fixtures/{mod_id}.json').then(r => r.json());
        }}
      }}
    }} else {{
      last = await RGCSLab.run(PATH, BODY);
    }}
    out.textContent = JSON.stringify(last, null, 2);
    const tests = (last.tests || (last.receipt && last.receipt.tests) || []);
    document.getElementById('tests').textContent = tests.join(', ') || 'see receipt';
  }} catch (err) {{
    out.textContent = String(err);
  }}
}}
document.getElementById('run').addEventListener('click', run);
document.getElementById('download-trace').addEventListener('click', () => {{
  if (!last) return;
  RGCSLab.downloadJSON('{mod_id}-trace.json', last);
}});
</script>
</body>
</html>
"""


def main() -> None:
    FIX.mkdir(parents=True, exist_ok=True)
    REC.mkdir(parents=True, exist_ok=True)
    MOD.mkdir(parents=True, exist_ok=True)
    EXAMPLES.mkdir(parents=True, exist_ok=True)

    results = {
        "coordinate": coordinate.decode(165876523),
        "golay": golay.demo(flips_per_block=1, seed=1),
        "frames": frames.example("earth-south-up"),
        "memory": services.memory_benchmark(),
        "dual_pole": services.dual_pole_audit({
            "statement": "exact structural decode of 165876523",
            "claim_class": ["EXACT_ARITHMETIC"],
            "evidence": ["golden_vector"],
        }),
        "lattice": services.lattice_run(),
        "metasurface": services.metasurface_sweep(),
        "predictions": services.predictions_freeze({
            "prediction_id": "EXAMPLE-RESIDUAL-FORCE-001",
            "created_at": "2026-07-26T00:00:00Z",
            "hypothesis": (
                "A phase-dependent force residual may appear in a "
                "counterrotating driven resonator after conventional "
                "effects are modeled."
            ),
            "mechanism_candidate": "UNSPECIFIED_EXPLORATORY, torsion is not assumed",
            "controls": [
                "unpowered", "detuned", "dummy load",
                "phase randomized", "orientation reversed", "polarity reversed",
            ],
            "claim_boundary": [
                "A positive residual would not by itself establish gravity modification.",
                "Energy and momentum accounting remain mandatory.",
            ],
        }),
        "proofs": services.proofs_bundle(),
    }

    # Also emit golay flip ladder fixtures for static bit-flip demo.
    flip_ladder = {
        str(n): golay.demo(flips_per_block=n, seed=1).to_dict()
        for n in range(0, 5)
    }
    write_json(FIX / "golay_flip_ladder.json", flip_ladder)

    catalog = {"modules": module_catalog()}
    write_json(FIX / "catalog.json", catalog)
    write_json(REC / "hub-catalog.json", catalog)

    # AA-03: the static-mode badge catalog is GENERATED from the
    # canonical module registry — never hand-written in hub.js. Loaded
    # via <script src> so file:// mode works without fetch/CORS.
    from rgcs_lab.common.gitmeta import source_commit

    catalog_js = (
        "/* GENERATED by tools/lab/build_static_hub.py from "
        "rgcs_lab.common.status.module_catalog() at commit "
        f"{source_commit()} -- do not edit by hand. */\n"
        "window.RGCS_CATALOG = "
        + json.dumps(module_catalog(), indent=2)
        + ";\n"
    )
    (HUB / "assets" / "catalog.data.js").write_text(catalog_js,
                                                    encoding="utf-8")

    for mod_id, result in results.items():
        payload = result.to_dict()
        write_json(FIX / f"{mod_id}.json", payload)
        write_json(REC / f"{mod_id}.json", result.receipt)
        meta = MODULE_META[mod_id]
        page = module_page(
            mod_id,
            meta["title"],
            meta["purpose"],
            meta["does_not"],
            meta["status"],
            meta["physical_status"],
        )
        (MOD / f"{mod_id}.html").write_text(page, encoding="utf-8")

    # Example claim + prediction for CLI demos.
    write_json(EXAMPLES / "claim.json", {
        "statement": "exact structural decode of 165876523",
        "claim_class": ["EXACT_ARITHMETIC"],
        "evidence": ["golden_vector"],
    })
    write_json(EXAMPLES / "claim_antigravity.json", {
        "statement": "anti-gravity confirmed via torsion resonance",
        "claim_class": ["SOURCE_REPORTED"],
    })
    pred = {
        "prediction_id": "EXAMPLE-RESIDUAL-FORCE-001",
        "created_at": "2026-07-26T00:00:00Z",
        "hypothesis": (
            "A phase-dependent force residual may appear after conventional "
            "effects are modeled."
        ),
        "controls": ["unpowered", "detuned", "dummy load"],
    }
    write_json(EXAMPLES / "prediction.json", pred)
    write_json(EXAMPLES / "prediction_frozen.json",
               pred_ref.freeze_prediction(pred))

    # Mirror workbench into static hub for self-contained static distro.
    dest_wb = HUB / "workbench"
    dest_wb.mkdir(parents=True, exist_ok=True)
    if WB.is_file():
        shutil.copy2(WB, dest_wb / "index.html")

    print(f"wrote fixtures+receipts+pages under {HUB}")


if __name__ == "__main__":
    main()
