"""Scripted RGCS v4 demo (Agent 12).

From a clean workspace, in order: (1) detect CPU/iGPU devices,
(2) generate the ideal and nominal crystal records, (3) create meshes,
(4) run validated modal solves, (5) compute supported coupled fields
(static piezo), (6) compute eye diagnostics, (7) render screenshots
offscreen, (8) build the proof bundle, (9) verify its checksums,
(10) exit 0 — recording runtime, peak memory, device, artifact paths,
and hashes in demo_out/demo_run_record.json.

    python tools/demo_v4.py [--fast]
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

import matplotlib
matplotlib.use("Agg")                       # offscreen, mandatory
import matplotlib.pyplot as plt
import numpy as np


def peak_memory_mb() -> float | None:
    try:
        import ctypes
        import ctypes.wintypes as wt

        class PMC(ctypes.Structure):
            _fields_ = [("cb", wt.DWORD), ("PageFaultCount", wt.DWORD),
                        ("PeakWorkingSetSize", ctypes.c_size_t),
                        ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t),
                        ("PeakPagefileUsage", ctypes.c_size_t)]
        pmc = PMC()
        pmc.cb = ctypes.sizeof(PMC)
        k32 = ctypes.windll.kernel32
        fn = getattr(k32, "K32GetProcessMemoryInfo", None) \
            or ctypes.windll.psapi.GetProcessMemoryInfo
        fn.argtypes = [wt.HANDLE, ctypes.POINTER(PMC), wt.DWORD]
        fn.restype = wt.BOOL
        ok = fn(k32.GetCurrentProcess(), ctypes.byref(pmc), pmc.cb)
        return pmc.PeakWorkingSetSize / 1e6 if ok else None
    except Exception:
        try:
            import resource
            return resource.getrusage(
                resource.RUSAGE_SELF).ru_maxrss / 1e3
        except Exception:
            return None


def main() -> int:
    fast = "--fast" in sys.argv[1:]
    t0 = time.perf_counter()
    outdir = REPO / "demo_out"
    outdir.mkdir(exist_ok=True)
    record: dict = {"steps": [], "fast": fast}

    def step(name, fn):
        ts = time.perf_counter()
        result = fn()
        record["steps"].append({"step": name,
                                "seconds": round(time.perf_counter()
                                                 - ts, 2)})
        print(f"[demo] {name} ({record['steps'][-1]['seconds']}s)")
        return result

    # 1. devices
    from rscs2_core import accel
    caps = step("detect devices", accel.capability_report)
    record["devices"] = caps

    # 2. geometry
    from rscs2_core import crystal110 as c110
    ideal = c110.build_crystal("ideal_n7")
    nominal = c110.build_crystal("nominal")
    step("generate crystals", lambda: (
        (outdir / "ideal.json").write_text(
            json.dumps(ideal.record(), indent=2)),
        (outdir / "nominal.json").write_text(
            json.dumps(nominal.record(), indent=2))))

    # 3. meshes
    cl = 11.0 if fast else 8.0
    mesh_i = step("mesh ideal", lambda: c110.mesh_crystal(
        ideal, cl, workdir=outdir / "work"))
    record["mesh_manifest"] = {
        k: mesh_i["manifest"][k]
        for k in ("n_nodes", "n_tets", "nodes_sha256", "tets_sha256")}

    # 4. modes
    from skfem import MeshTet
    from rgcs_core.anisotropy import (ALPHA_QUARTZ_DENSITY_KG_M3,
                                      alpha_quartz_stiffness_pa)
    from rscs_core.propagation import voigt_to_tensor
    from rscs2_core import fem
    C_FULL = voigt_to_tensor(alpha_quartz_stiffness_pa())
    prob = fem.assemble_anisotropic(
        MeshTet(mesh_i["nodes_m"].T, mesh_i["tets"].T), C_FULL,
        ALPHA_QUARTZ_DENSITY_KG_M3)
    sol = step("modal solve", lambda: fem.solve_modes(prob, 10))
    assert sol["n_rigid_modes"] == 6, "free body must have 6 rigid modes"
    record["first_elastic_hz"] = \
        sol["elastic_frequencies_hz"][:4].tolist()

    # 5. coupled fields (static piezo)
    from rscs2_core import piezo, quartz as qz
    L = ideal.length_mm * 1e-3
    pz = piezo.PiezoProblem(
        MeshTet(mesh_i["nodes_m"].T, mesh_i["tets"].T), C_FULL,
        np.array(qz.quartz_piezo_tensor_c_m2()),
        np.array(qz.quartz_dielectric_f_m()),
        ALPHA_QUARTZ_DENSITY_KG_M3)
    st = step("static piezo solve", lambda: piezo.static_potential_response(
        pz, lambda x: (x[0] > 0) & (x[2] > 0.35 * L) & (x[2] < 0.65 * L),
        lambda x: (x[0] < 0) & (x[2] > 0.35 * L) & (x[2] < 0.65 * L),
        10.0, pz.u_basis.get_dofs(lambda x: x[2] < 0.002).flatten()))
    record["piezo_max_u_m"] = float(np.max(np.abs(st["u"])))

    # 6. diagnostics
    from rscs2_core import eye
    flds = step("eye diagnostics", lambda: eye.evaluate_elastic_diagnostics(
        prob, sol, 0, C_FULL, pair_index=1))
    record["diagnostics"] = {d: f.raw_max for d, f in flds.items()}

    # 7. offscreen screenshots
    def shots():
        for did in ("D1", "D2"):
            f = flds[did]
            fig, ax = plt.subplots(figsize=(8, 3), dpi=110)
            sl = np.abs(f.points_mm[:, 1]) < 4.0
            ax.scatter(f.points_mm[sl, 2], f.points_mm[sl, 0],
                       c=f.values[sl], s=4, cmap="inferno")
            ax.set_title(f"{did} mode 1 (demo)")
            fig.savefig(outdir / f"screenshot_{did}.png")
            plt.close(fig)
    step("render screenshots", shots)

    # 8. proof bundle
    from rscs2_core.proofbundle import build_bundle
    bundle = step("build proof bundle", lambda: build_bundle(
        outdir / "proof_bundle_110mm", fast=fast))

    # 9. verify checksums
    from rscs2_core.cli import main as cli_main
    rc = step("verify checksums", lambda: cli_main(
        ["verify-checksums", "--bundle", str(bundle)]))
    assert rc == 0, "checksum verification failed"

    # 10. record + exit
    record["runtime_s"] = round(time.perf_counter() - t0, 2)
    record["peak_memory_mb"] = peak_memory_mb()
    record["artifacts"] = sorted(
        str(p.relative_to(REPO)) for p in outdir.rglob("*")
        if p.is_file() and "work" not in p.parts)[:50]
    record["verdict"] = json.loads(
        (bundle / "VERDICT.json").read_text())["verdict"]
    record["screenshot_hashes"] = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in outdir.glob("screenshot_*.png")}
    (outdir / "demo_run_record.json").write_text(
        json.dumps(record, indent=2, default=str))
    print(f"[demo] COMPLETE in {record['runtime_s']}s, peak mem "
          f"{record['peak_memory_mb']} MB, verdict {record['verdict']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
