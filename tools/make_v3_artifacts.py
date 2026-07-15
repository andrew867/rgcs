#!/usr/bin/env python3
"""Generate every numeric table, macro value, and figure of the four RGCS
v3 manuscripts from the tested libraries (Agent 09).

No number in any v3 manuscript is hand-copied: this script emits .tex
include files into manuscripts/<name>/tables/ and PDFs into
manuscripts/<name>/figures/, exactly mirroring the v2 discipline
(tools/make_tables.py / make_figures.py).

Run:  python tools/make_v3_artifacts.py
Deterministic given the repository state (no clocks, no RNG).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

import os
# D-V3-02: byte-reproducible figure PDFs (matplotlib honors
# SOURCE_DATE_EPOCH for the embedded CreationDate).
os.environ.setdefault("SOURCE_DATE_EPOCH", "0")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

import yaml  # noqa: E402

MAN = REPO / "manuscripts"


def _esc(s: str) -> str:
    return (str(s).replace("\\", "/").replace("&", "\\&")
            .replace("%", "\\%").replace("_", "\\_").replace("#", "\\#")
            .replace("^", "\\^{}").replace("~", "\\~{}"))


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {path.relative_to(REPO)}")


def _macro(name: str, value: str) -> str:
    return f"\\newcommand{{\\{name}}}{{{value}}}\n"


# ----------------------------------------------------------------------
# RSCS Foundations
# ----------------------------------------------------------------------

def foundations() -> None:
    out = MAN / "rscs_foundations"
    reg = yaml.safe_load((REPO / "rscs_core" / "registry" /
                          "rscs_registry.yaml").read_text(encoding="utf-8"))

    rows = []
    for c in reg["coordinates"]:
        # allow line breaks after '/' so long composite unit strings wrap
        units = _esc(c["units"]).replace("/", "/\\allowbreak{}")
        rows.append(f"{c['id']} & {_esc(c['name'])} & {_esc(c['class'])} & "
                    f"{units} & {_esc(c.get('manifold', '--'))} \\\\")
    _write(out / "tables" / "coordinates.tex",
           "\\begin{longtable}{@{}l p{4.2cm} l p{4.6cm} l@{}}\n"
           "\\caption{RSCS coordinates (machine registry "
           "\\texttt{rscs\\_registry.yaml}); RSCS-C.15 is defined in the "
           "memory application layer.}\\label{tab:coords}\\\\\n"
           "\\toprule ID & Name & Class & Units & Manifold \\\\ \\midrule\n"
           "\\endfirsthead\n\\toprule ID & Name & Class & Units & Manifold "
           "\\\\ \\midrule\n\\endhead\n"
           + "\n".join(rows) + "\n\\bottomrule\n\\end{longtable}\n")

    rows = []
    for o in reg["operators"]:
        v2 = ", ".join(o.get("v2_reproduces") or []) or "--"
        rows.append(f"{o['id']} & {_esc(o['name'])} & {_esc(o['class'])} & "
                    f"{_esc(v2)} \\\\")
    _write(out / "tables" / "operators.tex",
           "\\begin{longtable}{@{}l p{6.4cm} l p{3.4cm}@{}}\n"
           "\\caption{RSCS operators; the last column names the frozen v2 "
           "results each operator must reproduce (machine-tested).}"
           "\\label{tab:ops}\\\\\n"
           "\\toprule ID & Name & Class & Reproduces \\\\ \\midrule\n"
           "\\endfirsthead\n\\toprule ID & Name & Class & Reproduces \\\\ "
           "\\midrule\n\\endhead\n"
           + "\n".join(rows) + "\n\\bottomrule\n\\end{longtable}\n")

    # CEP battery + coupling golden numbers
    from rscs_core import embedding as emb
    from rscs_core.coupling import couple_modes
    cep = emb.run_all_cep()
    rows = [f"\\texttt{{{_esc(chk['property'])}}} & "
            f"{'pass' if chk.get('ok') else 'FAIL'} \\\\"
            for chk in cep["checks"]]
    _write(out / "tables" / "cep.tex",
           "\\begin{table}[H]\\centering\n"
           "\\caption{Conservative Extension Property battery "
           "(\\texttt{rscs\\_core.embedding.run\\_all\\_cep}); tolerances "
           "rtol $10^{-9}$, atol $10^{-12}$ (D3-011).}\\label{tab:cep}\n"
           "\\begin{tabular}{@{}l l@{}}\\toprule Check & Result \\\\ "
           "\\midrule\n" + "\n".join(rows)
           + "\n\\bottomrule\\end{tabular}\\end{table}\n")

    cm = couple_modes([1000.0, 1000.0], [[0.0, 10.0], [10.0, 0.0]])
    hyb = cm["hybrid_frequencies_hz"]

    macros = (
        # D-V3-01 fix: C.15 is a registry row; count rows directly.
        _macro("gvNumCoords", str(len(reg["coordinates"])))
        + _macro("gvNumOps", str(len(reg["operators"])))
        + _macro("gvCepAllOk", "all pass" if cep["all_ok"] else "FAILURES")
        + _macro("gvHybridLower", f"{hyb[0]:.1f}")
        + _macro("gvHybridUpper", f"{hyb[-1]:.1f}")
        + _macro("gvSplitting", f"{cm['splitting_hz']:.1f}")
    )
    _write(out / "tables" / "generated_values.tex", macros)

    # ATS lineshape figure (weak vs strong)
    from rscs_core.observation import autler_townes_response
    kappa = 2 * np.pi * 2.0e3
    d = np.linspace(-2 * np.pi * 60e3, 2 * np.pi * 60e3, 4001)
    fig, ax = plt.subplots(figsize=(5.4, 3.2))
    for g_hz, style, label in ((0.5e3, "--", "weak ($G \\ll \\kappa$)"),
                               (40e3, "-", "strong ($G \\gg \\kappa$)")):
        r = autler_townes_response(d, kappa, 2 * np.pi * g_hz)
        ax.plot(d / (2 * np.pi * 1e3), r / r.max(), style, label=label)
    ax.set_xlabel("detuning (kHz)")
    ax.set_ylabel("normalized $|\\chi|^2$")
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    (out / "figures").mkdir(parents=True, exist_ok=True)
    fig.savefig(out / "figures" / "ats_lineshape.pdf")
    plt.close(fig)
    print("wrote manuscripts/rscs_foundations/figures/ats_lineshape.pdf")


# ----------------------------------------------------------------------
# RGCS Crystal Application
# ----------------------------------------------------------------------

def crystal() -> None:
    out = MAN / "rgcs_crystal_application"
    from rgcs_core.anisotropy import (ALPHA_QUARTZ_DENSITY_KG_M3, AXIS_X,
                                      AXIS_Z, axis_speeds, wave_speeds)
    from rgcs_core.optics import (QUARTZ_N_E, QUARTZ_N_O,
                                  QUARTZ_PHOTOELASTIC,
                                  photoelastic_index_shift,
                                  quartz_acousto_optic_m2)
    from rgcs_core.uncertainty import default_wave_speed

    ax_sp = axis_speeds()
    rows = []
    for axis in ("X", "Y", "Z"):
        s = ax_sp[axis]
        rows.append(f"{axis} & {s['v_quasi_long_m_s']:.0f} & "
                    f"{s['v_quasi_shear1_m_s']:.0f} & "
                    f"{s['v_quasi_shear2_m_s']:.0f} \\\\")
    _write(out / "tables" / "axis_speeds.tex",
           "\\begin{table}[H]\\centering\n"
           "\\caption{$\\alpha$-quartz bulk wave speeds along the crystal "
           "axes (\\si{\\meter\\per\\second}), Christoffel eigenproblem "
           "\\eqid{RSCS-O.17} with the handbook constants (D5-002).}"
           "\\label{tab:axisspeeds}\n"
           "\\begin{tabular}{@{}l S[table-format=4.0] S[table-format=4.0] "
           "S[table-format=4.0]@{}}\\toprule Axis & {$v_{qL}$} & "
           "{$v_{qS1}$} & {$v_{qS2}$} \\\\ \\midrule\n" + "\n".join(rows)
           + "\n\\bottomrule\\end{tabular}\\end{table}\n")

    p11 = QUARTZ_PHOTOELASTIC["p11"]
    dn = photoelastic_index_shift(QUARTZ_N_O, p11, 1e-7)
    m2 = quartz_acousto_optic_m2()
    v2b = default_wave_speed()
    lo, hi = v2b.interval(k=1.0)
    zql = ax_sp["Z"]["v_quasi_long_m_s"]
    xql = ax_sp["X"]["v_quasi_long_m_s"]

    macros = (
        _macro("gvNo", f"{QUARTZ_N_O:.4f}")
        + _macro("gvNe", f"{QUARTZ_N_E:.4f}")
        + _macro("gvBirefringence", f"{QUARTZ_N_E - QUARTZ_N_O:.4f}")
        + _macro("gvPelDn", f"{dn:.2e}")
        + _macro("gvMTwo", f"{m2:.2e}")
        + _macro("gvDensity", f"{ALPHA_QUARTZ_DENSITY_KG_M3:.0f}")
        + _macro("gvZql", f"{zql:.0f}")
        + _macro("gvXql", f"{xql:.0f}")
        + _macro("gvVtwoLo", f"{lo:.0f}")
        + _macro("gvVtwoHi", f"{hi:.0f}")
        + _macro("gvVtwoMean", f"{v2b.mean:.0f}")
        + _macro("gvZqlDevPct",
                 f"{100.0 * abs(zql - v2b.mean) / v2b.mean:.1f}")
    )
    _write(out / "tables" / "generated_values.tex", macros)

    # anisotropy sweep X -> Z
    from rgcs_core.anisotropy import wave_speeds as ws
    angles = np.linspace(0.0, 90.0, 91)
    vql = []
    for a in angles:
        n = np.array([np.cos(np.radians(a)), 0.0, np.sin(np.radians(a))])
        vql.append(ws(n)["v_quasi_long_m_s"])
    fig, ax = plt.subplots(figsize=(5.4, 3.2))
    ax.plot(angles, vql, label="$v_{qL}(\\theta)$ (RSCS-O.17)")
    ax.axhspan(lo, hi, alpha=0.15, label="v2 scalar $v_L$ $\\pm5\\%$ band")
    ax.axhline(v2b.mean, ls=":", lw=1)
    ax.set_xlabel("angle from X toward Z (deg)")
    ax.set_ylabel("$v_{qL}$ (m/s)")
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    (out / "figures").mkdir(parents=True, exist_ok=True)
    fig.savefig(out / "figures" / "anisotropy_sweep.pdf")
    plt.close(fig)
    print("wrote manuscripts/rgcs_crystal_application/figures/"
          "anisotropy_sweep.pdf")


# ----------------------------------------------------------------------
# Software & Hardware Architecture and Roadmap
# ----------------------------------------------------------------------

def software() -> None:
    out = MAN / "software_hardware_plan"
    from rgcs_core.timing import (MODULATION_FAMILIES, SAFETY_LIMITS,
                                  key_closures, modulation_family_report)
    kc = key_closures()
    rows = []
    for key_hz, v in kc["keys"].items():
        rows.append(f"{key_hz:.0f} & {v['closure_window_s'] * 1000:.0f} & "
                    f"{v['key_cycles']} & {v['carrier_cycles']} \\\\")
    _write(out / "tables" / "timing_closures.tex",
           "\\begin{table}[H]\\centering\n"
           "\\caption{Exact-cycle closures of the source key frequencies "
           "\\SRC{} against the \\SI{4096}{\\hertz} carrier "
           "(\\texttt{rgcs\\_core.timing.key\\_closures}); the closure "
           "arithmetic is \\DER{} and confers no truth value on the keys.}"
           "\\label{tab:closures}\n"
           "\\begin{tabular}{@{}S[table-format=4.0] S[table-format=4.0] "
           "S[table-format=4.0] S[table-format=4.0]@{}}\\toprule "
           "{Key (\\si{\\hertz})} & {Window (\\si{\\milli\\second})} & "
           "{Key cycles} & {Carrier cycles} \\\\ \\midrule\n"
           + "\n".join(rows)
           + "\n\\bottomrule\\end{tabular}\\end{table}\n")

    rep = modulation_family_report()
    rows = []
    for name in sorted(MODULATION_FAMILIES):
        r = rep[name]
        exact = "yes" if r["exact_subharmonic"] else "no"
        rows.append(f"{r['frequency_hz']:.2f} & {_esc(r['origin'])} & "
                    f"{exact} & {r['closure_window_s'] * 1000:.3f} \\\\")
    _write(out / "tables" / "modulation_families.tex",
           "\\begin{table}[H]\\centering\n"
           "\\caption{Modulation families: source rates vs.\\ exact-cycle "
           "engineering variants (carrier subharmonics).}"
           "\\label{tab:modfam}\n\\small\n"
           "\\begin{tabular}{@{}r l l r@{}}\\toprule $f$ (\\si{\\hertz}) & "
           "Origin & Exact & Closure (\\si{\\milli\\second}) \\\\ "
           "\\midrule\n" + "\n".join(rows)
           + "\n\\bottomrule\\end{tabular}\\end{table}\n")

    from rgcs_desktop.services.provenance_graph import build_provenance_graph
    g = build_provenance_graph()
    macros = (
        _macro("gvGraphNodes", str(g["counts"]["nodes"]))
        + _macro("gvGraphEdges", str(g["counts"]["edges"]))
        + _macro("gvVmax", f"{SAFETY_LIMITS['voltage_v_max']:.0f}")
        + _macro("gvImax", f"{SAFETY_LIMITS['current_a_max']:.0f}")
        + _macro("gvEmax", f"{SAFETY_LIMITS['pulse_energy_mj_max']:.0f}")
        + _macro("gvLaserMax", f"{SAFETY_LIMITS['laser_power_mw_max']:.0f}")
    )
    _write(out / "tables" / "generated_values.tex", macros)

    # macro envelope timing figure (three frozen modes)
    from rgcs_desktop.services.waveform_preview import preview_macro_envelope
    fig, axes = plt.subplots(3, 1, figsize=(6.0, 3.4), sharex=True)
    for axi, mode in zip(axes, ("standard", "half_spacing", "double_rate")):
        env = preview_macro_envelope(mode)
        for t0, t1, state in env["segments"]:
            if state == "on":
                axi.axvspan(t0, t1, color="#17324D")
            elif state == "pause":
                axi.axvspan(t0, t1, color="#EEF4F8")
        axi.set_yticks([])
        axi.set_ylabel(mode.replace("_", "\n"), rotation=0, ha="right",
                       va="center", fontsize=8)
        axi.set_xlim(0, 560)
    axes[-1].set_xlabel("time (ms)")
    fig.tight_layout()
    (out / "figures").mkdir(parents=True, exist_ok=True)
    fig.savefig(out / "figures" / "macro_envelopes.pdf")
    plt.close(fig)
    print("wrote manuscripts/software_hardware_plan/figures/"
          "macro_envelopes.pdf")


# ----------------------------------------------------------------------
# Historical and Source Companion
# ----------------------------------------------------------------------

def historical() -> None:
    out = MAN / "historical_source_companion"
    prov = yaml.safe_load((REPO / "references" /
                           "equation_provenance.yaml").read_text(
                               encoding="utf-8"))
    srcs = yaml.safe_load((REPO / "references" /
                           "source_registry.yaml").read_text(
                               encoding="utf-8"))
    rows = []
    for eq in prov["equations"]:
        rows.append(
            f"{eq['prov_id']} & {_esc(eq['source_id'])} & "
            f"{_esc(eq['name'])} & "
            f"{_esc(eq['forbidden_transfer'][:180])} \\\\ \\addlinespace")
    _write(out / "tables" / "adaptation_ledger.tex",
           "\\begin{landscape}\n\\begin{longtable}{@{}l l p{7.2cm} "
           "p{11.5cm}@{}}\n"
           "\\caption{Equation-level adaptation ledger: every reused piece "
           "of source mathematics with its binding forbidden transfer "
           "(\\texttt{references/equation\\_provenance.yaml}, frozen).}"
           "\\label{tab:ledger}\\\\\n"
           "\\toprule EP id & Source & Adapted mathematics & Forbidden "
           "transfer (binding) \\\\ \\midrule\n\\endfirsthead\n"
           "\\toprule EP id & Source & Adapted mathematics & Forbidden "
           "transfer (binding) \\\\ \\midrule\n\\endhead\n"
           + "\n".join(rows)
           + "\n\\bottomrule\n\\end{longtable}\n\\end{landscape}\n")

    n_src = len(srcs["sources"])
    macros = (_macro("gvNumSources", str(n_src))
              + _macro("gvNumEp", str(len(prov["equations"]))))
    _write(out / "tables" / "generated_values.tex", macros)


def main() -> int:
    foundations()
    crystal()
    software()
    historical()
    print("OK: all v3 manuscript artifacts generated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
