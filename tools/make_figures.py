#!/usr/bin/env python3
"""Generate every figure of the RGCS v2 manuscript from rgcs_core.

All numerical content is computed by rgcs_core (never hand-copied); the
golden coherence datasets in experiments/sample_data/golden_coherence are
read from disk and re-analysed with rgcs_core.coherence. Output: vector
PDF into manuscript/figures/ plus a fig_values.json consumed by
tools/make_tables.py so that inline manuscript numbers share the same
provenance.

Run from the repository root:  python3 tools/make_figures.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle

from rgcs_core.uncertainty import default_wave_speed
from rgcs_core.geometry import (
    SpiralGeometry,
    spiral_curve,
    spiral_metrics,
)
from rgcs_core.harmonics import axial_half_wave, ladder_length_mm
from rgcs_core.compact_modes import compact_mode_spectrum, parity_index_set
from rgcs_core.resonance import (
    NONRESONANT_CONTROL_EPSILON,
    classify_resonance,
    epsilon_q,
    linewidth_fwhm_hz,
    resonance_offset,
)
from rgcs_core.coupled_modes import (
    avoided_crossing_sweep,
    coupled_two_mode,
    integrate_stuart_landau,
)
from rgcs_core.coherence import (
    DEFAULT_HOP_S,
    DEFAULT_WINDOW_S,
    coherence_series,
    initial_phase_estimate,
    instantaneous_phase,
    model_comparison,
    noise_baseline_theory,
    rayleigh_test,
    spatial_phase_anisotropy,
    windowed_phase_rates,
)

FIG_DIR = REPO_ROOT / "manuscript" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)
GOLDEN_DIR = REPO_ROOT / "experiments" / "sample_data" / "golden_coherence"

# Consistent, print-friendly styling ------------------------------------
plt.rcParams.update(
    {
        "font.size": 9,
        "font.family": "serif",
        "axes.titlesize": 9.5,
        "axes.labelsize": 9,
        "legend.fontsize": 8,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "figure.dpi": 150,
        "savefig.bbox": "tight",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "lines.linewidth": 1.3,
    }
)
C_EST = "#17324D"   # established / structure
C_DER = "#2A7F78"   # derived
C_HYP = "#B4582E"   # hypothesis
C_SRC = "#7A6A9E"   # source claim
C_BAND = "#9BB8CE"
C_GRAY = "#8A8F98"

VALUES: dict[str, object] = {}


def save(fig, name: str) -> None:
    out = FIG_DIR / name
    fig.savefig(out)
    plt.close(fig)
    print(f"wrote {out.relative_to(REPO_ROOT)}")


def box(ax, x, y, w, h, text, fc, ec=None, fontsize=8, tc="white", lw=1.0):
    p = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.012,rounding_size=0.015",
        fc=fc, ec=ec or fc, lw=lw, mutation_aspect=1.0,
    )
    ax.add_patch(p)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fontsize, color=tc, wrap=True)
    return (x, y, w, h)


def arrow(ax, a, b, color=C_GRAY, style="-|>", lw=1.2, rad=0.0):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle=style, color=color,
                                 lw=lw, mutation_scale=11,
                                 connectionstyle=f"arc3,rad={rad}"))


def uv(x) -> dict:
    """Normalize an UncertainValue or its to_dict() form to a plain dict."""
    if isinstance(x, dict):
        return x
    return x.to_dict()


def load_iq(path: Path) -> tuple[np.ndarray, np.ndarray]:
    d = np.genfromtxt(path, delimiter=",", names=True)
    return d["t_s"], d["I"] + 1j * d["Q"]


# ----------------------------------------------------------------------
# Figure 1 — system architecture
# ----------------------------------------------------------------------
def fig_architecture():
    fig, ax = plt.subplots(figsize=(6.7, 4.4))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 7)
    ax.axis("off")

    # column 1: static inputs
    box(ax, 0.2, 5.4, 2.3, 1.1, "Crystal geometry $\\mathcal{G}$:\n$L$, $D_w$, $D_n$, $N_f$, $\\alpha_f$, $\\alpha_m$,\n$\\rho$, $v_L(1\\pm u_v)$", C_EST, fontsize=7)
    box(ax, 0.2, 3.9, 2.3, 1.1, "Spiral state $\\mathcal{S}_{sp}$:\n$q$, $T$, $R_0$, $H$, $p_z$, $\\Omega_s$", C_EST, fontsize=7)
    box(ax, 0.2, 2.4, 2.3, 1.1, "Boundary / parity $\\mathcal{B}$:\n$P^\\pm$, zero-mode flag", C_DER, fontsize=7)
    box(ax, 0.2, 0.6, 2.3, 1.3, "Drive branches\n(source presets):\nelectrode, sound key,\nopposed coil", C_SRC, fontsize=7)

    # column 2: spectra
    box(ax, 3.3, 5.4, 2.6, 1.1, "4096 ladder\n$f_{ax}=v_L/2L$, $L_N=v_L/2Nf_0$\nset-valued harmonic class", C_DER, fontsize=7)
    box(ax, 3.3, 3.9, 2.6, 1.1, "Compact spectrum (H-01)\n$f_n^2=f_b^2+(n\\kappa_\\chi)^2$\n$\\kappa_\\chi = v_\\chi/2\\pi R_\\chi$", C_HYP, fontsize=7)
    box(ax, 3.3, 2.4, 2.6, 1.1, "Spiral path $\\ell_{3D}$ (numeric)\n$\\rightarrow R_\\chi^{(s)}$ prior (H-06a)", C_HYP, fontsize=7)
    box(ax, 3.3, 0.6, 2.6, 1.3, "Pulse timing;\nexact-cycle families;\nphase residue $r_\\phi$", C_DER, fontsize=7)

    # column 3: interaction
    box(ax, 6.7, 5.4, 3.0, 1.1, "Resonance offset $\\epsilon_R^{(f)}$;\n$Q$-derived classes;\nsigned ledger $\\delta_k$", C_DER, fontsize=7)
    box(ax, 6.7, 3.9, 3.0, 1.1, "Coupled modes: $\\mathbf{H}$, $f_\\pm$,\n$2g$ splitting, $R_g$;\nStuart–Landau $z_n(t)$ (H-09)", C_HYP, fontsize=7)
    box(ax, 6.7, 2.4, 3.0, 1.1, "Coherence & anisotropy:\n$(\\mathcal{C}_w, w, b_w)$, $\\Sigma_\\phi$, $\\sigma_\\phi^2$;\ndecay-law comparison (H-10)", C_HYP, fontsize=7)
    box(ax, 6.7, 0.6, 3.0, 1.3, "Experiments $\\mathcal{O}(t)$:\ncontrols, $G_c$, $d_c$,\nartifact & negative-result\nregisters", C_EST, fontsize=7)

    for a, b in [((2.5, 5.95), (3.3, 5.95)), ((2.5, 4.45), (3.3, 4.45)),
                 ((2.5, 2.95), (3.3, 2.95)), ((2.5, 1.25), (3.3, 1.25)),
                 ((5.9, 5.95), (6.7, 5.95)), ((5.9, 4.45), (6.7, 4.45)),
                 ((5.9, 2.95), (6.7, 2.95)), ((5.9, 1.25), (6.7, 1.25))]:
        arrow(ax, a, b)
    arrow(ax, (4.6, 3.9), (4.6, 3.5), rad=0.0)          # compact <- spiral prior
    arrow(ax, (8.2, 5.4), (8.2, 5.0), rad=0.0)
    arrow(ax, (8.2, 3.9), (8.2, 3.5), rad=0.0)
    arrow(ax, (8.2, 2.4), (8.2, 1.9), rad=0.0)
    # calibration loop back
    arrow(ax, (6.7, 1.0), (1.35, 5.4), color=C_HYP, rad=-0.32, lw=1.4)
    ax.text(2.9, 2.08, "measured $\\hat{x}_e$, $\\delta_k$, fitted $\\kappa_\\chi$, $\\tau_c$: calibration loop",
            fontsize=7.2, color=C_HYP, ha="center")

    # legend
    for i, (c, t) in enumerate([(C_EST, "Established"), (C_DER, "Derived"),
                                (C_HYP, "Hypothesis"), (C_SRC, "Source claim")]):
        ax.add_patch(Rectangle((0.3 + i * 2.0, 6.75), 0.28, 0.2, fc=c, ec="none"))
        ax.text(0.66 + i * 2.0, 6.85, t, fontsize=7.5, va="center")
    save(fig, "fig_architecture.pdf")


# ----------------------------------------------------------------------
# Figure 2 — compact-mode ladder with uncertainty bands
# ----------------------------------------------------------------------
def fig_compact_ladder():
    fig, axes = plt.subplots(1, 2, figsize=(6.7, 3.1), sharey=True)
    for ax, fb in zip(axes, (0.0, 6000.0)):
        spec = compact_mode_spectrum(base_frequency_hz=fb, v_chi=default_wave_speed(),
                                     compact_radius_mm=100.0, n_max=8,
                                     parity="all", include_zero_mode=True,
                                     u_base_frequency_hz=0.0)
        for m in spec["modes"]:
            f = uv(m["frequency"])
            n = m["n"]
            col = C_DER if m["parity"] == "even" else C_HYP
            ax.errorbar([n], [f["mean"] / 1000.0],
                        yerr=[[(f["mean"] - f["lo_1sigma"]) / 1000.0],
                              [(f["hi_1sigma"] - f["mean"]) / 1000.0]],
                        fmt="o", ms=4, color=col, capsize=3, lw=1.1)
        nn = np.linspace(0, 8.4, 200)
        kap = uv(spec["kappa_chi_hz"])["mean"]
        ax.plot(nn, np.sqrt(fb**2 + (nn * kap) ** 2) / 1000.0, "--",
                color=C_GRAY, lw=0.9, zorder=0)
        ax.set_xlabel("compact mode index $n$")
        ax.set_title(f"$f_b = {fb:.0f}$ Hz" + ("  (zero mode excluded)" if fb == 0 else "  (zero mode at $f_b$)"),
                     fontsize=9)
        ax.set_xticks(range(0, 9))
        VALUES[f"compact_kappa_fb{int(fb)}"] = kap
    axes[0].set_ylabel("$f_n$ (kHz)")
    h1 = plt.Line2D([], [], marker="o", ls="", color=C_HYP, label="odd family $P^-$")
    h2 = plt.Line2D([], [], marker="o", ls="", color=C_DER, label="even family $P^+$")
    axes[0].legend(handles=[h1, h2], loc="upper left", frameon=False)
    fig.suptitle("", y=1.0)
    save(fig, "fig_compact_ladder.pdf")


# ----------------------------------------------------------------------
# Figure 3 — parity families (mode functions and index sets)
# ----------------------------------------------------------------------
def fig_parity_families():
    chi = np.linspace(0, 2 * np.pi, 600)
    odd = parity_index_set("odd", 5)
    even = parity_index_set("even", 6, include_zero_mode=True)
    fig, axes = plt.subplots(2, 1, figsize=(6.7, 3.6), sharex=True)
    for n in odd:
        axes[0].plot(chi, np.sin(n * chi / 2), color=C_HYP,
                     alpha=1.0 - 0.16 * odd.index(n), label=f"$n={n}$")
    axes[0].set_ylabel("$u_n^-(\\chi)\\propto\\sin(n\\chi/2)$")
    axes[0].set_title(f"odd (antisymmetric) family $P^-$, $\\mathbb{{I}}^-=\\{{{', '.join(map(str, odd))}\\}}$ — never contains $n=0$", fontsize=8.7)
    for n in even:
        axes[1].plot(chi, np.cos(n * chi / 2), color=C_DER,
                     alpha=1.0 - 0.14 * even.index(n), label=f"$n={n}$")
    axes[1].set_ylabel("$u_n^+(\\chi)\\propto\\cos(n\\chi/2)$")
    axes[1].set_title(f"even (symmetric) family $P^+$, $\\mathbb{{I}}^+=\\{{{', '.join(map(str, even))}\\}}$ — $n=0$ gated by the zero-mode flag", fontsize=8.7)
    axes[1].set_xlabel("compact coordinate $\\chi$ (rad)")
    axes[1].set_xticks([0, np.pi, 2 * np.pi])
    axes[1].set_xticklabels(["0", "$\\pi$", "$2\\pi$"])
    for ax in axes:
        ax.legend(ncol=len(odd) + 1, frameon=False, fontsize=7, loc="lower left")
        ax.axhline(0, color="k", lw=0.4)
    VALUES["parity_odd_set"] = odd
    VALUES["parity_even_set"] = even
    save(fig, "fig_parity_families.pdf")


# ----------------------------------------------------------------------
# Figure 4 — epsilon resonance map with Q-derived classes
# ----------------------------------------------------------------------
def fig_epsilon_map():
    f_x = 20480.0
    q_m, q_x = 1000.0, 800.0
    eq = epsilon_q(q_m, q_x)
    VALUES["epsilon_q_example"] = eq
    fm = np.linspace(0.90 * 2 * f_x, 1.12 * 2 * f_x, 900)
    eps = np.array([resonance_offset(f, f_x) for f in fm])

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(6.7, 3.0),
                                  gridspec_kw={"width_ratios": [1.35, 1.0]})
    ax.plot(fm / 1000.0, eps, color=C_EST)
    for k, (lo, hi, c, lab) in enumerate([
            (0, 1, "#2A7F78", "within linewidth"),
            (1, 5, "#7fb2ac", "near"),
            (5, 50, "#c9dedb", "moderate")]):
        ax.axhspan(lo * eq, hi * eq, color=c, alpha=0.55, lw=0)
        ax.axhspan(-hi * eq, -lo * eq, color=c, alpha=0.55, lw=0)
    ax.axhline(0, color="k", lw=0.5)
    ax.set_xlabel("bridge frequency $f_m$ (kHz)   [$f_x = 20.48$ kHz, $p=2$]")
    ax.set_ylabel("$\\epsilon_R^{(f)}$")
    ax.set_ylim(-0.2, 0.25)
    ax.set_title(f"$Q_m=1000$, $Q_x=800$ $\\Rightarrow$ $\\epsilon_Q = 1/Q_{{\\rm eff}} = {eq:.3e}$", fontsize=8.6)

    # zoom near zero: class bands on log scale of |eps|
    d = np.linspace(-6e-3, 6e-3, 800)
    eps2 = (1 + d) ** 2 - 1
    ax2.plot(d * 1e3, eps2 * 1e3, color=C_EST)
    for lo, hi, c in [(0, 1, "#2A7F78"), (1, 5, "#7fb2ac"), (5, 50, "#c9ded b".replace(" ", ""))]:
        ax2.axhspan(lo * eq * 1e3, hi * eq * 1e3, color=c, alpha=0.55, lw=0)
        ax2.axhspan(-hi * eq * 1e3, -lo * eq * 1e3, color=c, alpha=0.55, lw=0)
    ax2.set_xlabel("linear detuning $d_{\\rm lin}\\times 10^{3}$")
    ax2.set_ylabel("$\\epsilon_R^{(f)}\\times 10^{3}$")
    ax2.set_title("zoom: $\\epsilon \\approx 2d_{\\rm lin}$; classes at $1/5/50\\,\\epsilon_Q$", fontsize=8.6)
    # far-detuned control convention
    ax.plot([], [])
    ax.annotate(f"far-detuned control convention $\\epsilon = {NONRESONANT_CONTROL_EPSILON}$\n(off-scale; control convention, not physics)",
                xy=(0.02, 0.965), xycoords="axes fraction", fontsize=7.2,
                va="top", color=C_SRC)
    ex = classify_resonance(resonance_offset(40970.0, f_x), q_m, q_x, u_eps=2e-4)
    VALUES["class_example_eps"] = resonance_offset(40970.0, f_x)
    VALUES["class_example_label"] = str(ex.get("resonance_class", ex))
    save(fig, "fig_epsilon_map.pdf")


# ----------------------------------------------------------------------
# Figure 5 — avoided crossing
# ----------------------------------------------------------------------
def fig_avoided_crossing():
    f_b, g = 20480.0, 25.0
    q_a = q_b = 1000.0
    grid = np.linspace(f_b - 250, f_b + 250, 601)
    sw = avoided_crossing_sweep(grid, f_b, g)
    two = coupled_two_mode(f_b, f_b, g, q_a, q_b)
    VALUES["ac_splitting_hz"] = two["splitting_hz"]
    VALUES["ac_rg"] = two["strong_coupling_ratio"]
    gam = linewidth_fwhm_hz(f_b, q_a)
    VALUES["ac_linewidth_hz"] = gam

    fig, ax = plt.subplots(figsize=(4.6, 3.4))
    lo = np.asarray(sw["lower_hz"])
    hi = np.asarray(sw["upper_hz"])
    ax.fill_between((grid - f_b), (lo - gam / 2 - f_b), (lo + gam / 2 - f_b),
                    color=C_BAND, alpha=0.45, lw=0, label="FWHM $\\Gamma=f/Q$")
    ax.fill_between((grid - f_b), (hi - gam / 2 - f_b), (hi + gam / 2 - f_b),
                    color=C_BAND, alpha=0.45, lw=0)
    ax.plot(grid - f_b, lo - f_b, color=C_EST, label="hybrid $f_-$")
    ax.plot(grid - f_b, hi - f_b, color=C_DER, label="hybrid $f_+$")
    ax.plot(grid - f_b, grid - f_b, ":", color=C_GRAY, lw=0.9, label="uncoupled")
    ax.plot(grid - f_b, np.zeros_like(grid), ":", color=C_GRAY, lw=0.9)
    ax.annotate("", xy=(0, g), xytext=(0, -g),
                arrowprops=dict(arrowstyle="<->", color=C_HYP, lw=1.3))
    ax.text(6, 0, f"$2g = {two['splitting_hz']:.0f}$ Hz\n$R_g = {two['strong_coupling_ratio']:.2f}$",
            fontsize=8, color=C_HYP, va="center")
    ax.set_xlabel("detuning $f_A - f_B$ (Hz)   [$f_B = 20480$ Hz]")
    ax.set_ylabel("$f_\\pm - f_B$ (Hz)")
    ax.legend(frameon=False, loc="upper left", fontsize=7.4)
    save(fig, "fig_avoided_crossing.pdf")


# ----------------------------------------------------------------------
# Figure 6 — 4D spiral projection + per-turn compact radius
# ----------------------------------------------------------------------
def fig_spiral():
    g = SpiralGeometry()
    curve = spiral_curve(g, samples=2400)
    met = spiral_metrics(g)
    for k in ("path_length_3d_mm", "planar_arc_length_mm", "compact_radius_prior_mm",
              "retired_closed_form_mm", "retired_closed_form_rel_error",
              "pitch_parameter_a", "curvature_invariant_rkappa"):
        VALUES[f"spiral_{k}"] = met[k]
    VALUES["spiral_per_turn_radius_mm"] = list(np.asarray(met["per_turn_compact_radius_mm"], dtype=float))

    fig = plt.figure(figsize=(6.7, 3.2))
    ax = fig.add_subplot(1, 2, 1, projection="3d")
    chi = np.mod(curve["chi"], 2 * np.pi)
    p = ax.scatter(curve["x"], curve["y"], curve["z"], c=chi, cmap="twilight",
                   s=1.6, lw=0)
    ax.set_xlabel("x (mm)", labelpad=-4)
    ax.set_ylabel("y (mm)", labelpad=-4)
    ax.set_zlabel("z (mm)", labelpad=-4)
    ax.tick_params(pad=-2, labelsize=6.5)
    cb = fig.colorbar(p, ax=ax, shrink=0.62, pad=0.10)
    cb.set_label("$\\chi\;\\mathrm{mod}\;2\\pi$ (rad)", fontsize=7.5)
    cb.ax.tick_params(labelsize=6.5)
    ax.set_title("3D projection of $X(\\theta)$, colour = compact phase $\\chi$", fontsize=8.4)

    ax2 = fig.add_subplot(1, 2, 2)
    per_turn = np.asarray(met["per_turn_compact_radius_mm"], dtype=float)
    ks = np.arange(1, per_turn.size + 1)
    ax2.bar(ks, per_turn, color=C_DER, width=0.6, label="per-turn $R_{\\chi,k}=\\ell_k/2\\pi$")
    ax2.axhline(met["compact_radius_prior_mm"], color=C_HYP, ls="--",
                label=f"mean prior $R_\\chi^{{(s)}} = {met['compact_radius_prior_mm']:.2f}$ mm")
    ax2.set_xlabel("turn $k$")
    ax2.set_ylabel("$R_{\\chi}$ candidate (mm)")
    ax2.set_xticks(list(ks))
    ax2.legend(frameon=False, fontsize=7.5)
    ax2.set_title("competing compact-radius definitions (H-06a)", fontsize=8.4)
    save(fig, "fig_spiral_projection.pdf")


# ----------------------------------------------------------------------
# Figure 7 — phase randomization to coherence (golden case d)
# ----------------------------------------------------------------------
def fig_phase_randomization():
    d = np.genfromtxt(GOLDEN_DIR / "case_d_random_phase_runs.csv",
                      delimiter=",", names=True)
    runs = np.unique(d["run"].astype(int))
    fs = 100000.0
    # Unified per-run initial-phase estimator (QA-D-03): arg z(0) mod 2pi,
    # via rgcs_core.coherence.initial_phase_estimate — the same estimator
    # used by tools/make_tables.py, so Fig. 8 and Table 8 agree exactly.
    first_phases = []
    coh_curves = []
    for r in runs:
        m = d["run"].astype(int) == r
        z = d["I"][m] + 1j * d["Q"][m]
        first_phases.append(initial_phase_estimate(z))
        tc, c = coherence_series(z, fs)
        coh_curves.append((tc, c))
    first_phases = np.asarray(first_phases)
    rt = rayleigh_test(first_phases)
    VALUES["cased_n_runs"] = int(runs.size)
    VALUES["cased_rayleigh_z"] = float(rt["z"]) if "z" in rt else float(rt.get("Z", np.nan))
    VALUES["cased_rayleigh_p"] = float(rt.get("p_value", rt.get("p", np.nan)))
    nw = int(round(DEFAULT_WINDOW_S * fs))
    VALUES["baseline_nw200"] = noise_baseline_theory(nw)

    fig = plt.figure(figsize=(6.7, 3.0))
    axp = fig.add_subplot(1, 2, 1, projection="polar")
    axp.hist(first_phases, bins=12, color=C_DER, alpha=0.85)
    axp.set_title(f"per-run initial phase $\\varphi_0 = \\arg z(0)$, $n_s={runs.size}$ runs\nRayleigh $Z_R={VALUES['cased_rayleigh_z']:.2f}$, $p={VALUES['cased_rayleigh_p']:.2f}$",
                  fontsize=8.2, pad=12)
    axp.tick_params(labelsize=6.5)

    ax = fig.add_subplot(1, 2, 2)
    for i, (tc, c) in enumerate(coh_curves):
        ax.plot(tc * 1e3, c, color=C_EST, alpha=0.35, lw=0.8)
    ax.axhline(VALUES["baseline_nw200"], color=C_GRAY, ls="--", lw=0.9,
               label=f"noise baseline $b_w \\approx {VALUES['baseline_nw200']:.3f}$")
    ax.set_ylim(0, 1.05)
    ax.set_xlabel("time (ms)")
    ax.set_ylabel("$\\mathcal{C}_w(t)$  ($w=2$ ms)")
    ax.set_title("per-run coherence: high in every run,\nensemble phase uniform (KOS-06 pattern)", fontsize=8.2)
    ax.legend(frameon=False, fontsize=7.5, loc="lower right")
    save(fig, "fig_phase_randomization.pdf")


# ----------------------------------------------------------------------
# Figure 8 — coherence versus amplitude (golden case c)
# ----------------------------------------------------------------------
def fig_coherence_vs_amplitude():
    t, z = load_iq(GOLDEN_DIR / "case_c_decaying_sinusoid.csv")
    fs = 1.0 / (t[1] - t[0])
    amp = np.abs(z)
    tc, c = coherence_series(z, fs)
    nw = int(round(DEFAULT_WINDOW_S * fs))
    bw = noise_baseline_theory(nw)
    VALUES["casec_coh_late_mean"] = float(np.mean(c[int(0.8 * c.size):]))
    VALUES["casec_amp_ratio_late"] = float(np.mean(amp[int(0.8 * amp.size):]) / amp.max())

    fig, ax = plt.subplots(figsize=(5.4, 3.1))
    ax.plot(t * 1e3, amp / amp.max(), color=C_GRAY, lw=0.9,
            label="normalised amplitude $|z|$")
    ax.plot(tc * 1e3, c, color=C_EST, lw=1.5,
            label="coherence $\\mathcal{C}_w(t)$")
    ax.axhline(bw, color=C_DER, ls="--", lw=0.9,
               label=f"noise baseline $b_w={bw:.3f}$ ($N_w={nw}$)")
    ax.set_xlabel("time (ms)")
    ax.set_ylabel("normalised value")
    ax.set_ylim(0, 1.08)
    ax.legend(frameon=False, fontsize=7.6, loc="center right")
    ax.set_title("amplitude decays; phase order persists (KOS-10 metric property)",
                 fontsize=8.6)
    save(fig, "fig_coherence_vs_amplitude.pdf")


# ----------------------------------------------------------------------
# Figure 9 — anisotropy-decay model comparison (GAN-11 layout)
# ----------------------------------------------------------------------
def fig_anisotropy_decay():
    # Three-channel synthetic phase records with a KNOWN exponential
    # relaxation of the per-axis rate differences (ground truth
    # tau_sigma = tau_rate/2 for the squared scalar), plus seeded phase
    # jitter. Analysis is pure rgcs_core: windowed phase rates (COH-M13
    # normative estimator), the GAN-05-adapted shear scalar combination,
    # and the pre-registered four-model AIC comparison (COH-M14).
    fs = 50000.0
    n = 25000
    tau_rate = 0.12          # s; ground-truth rate-relaxation time
    rng = np.random.default_rng(20260714)
    t = np.arange(n) / fs
    c_off = np.array([90.0, -40.0, -50.0]) * 2 * np.pi   # rad/s initial offsets
    phases = (2 * np.pi * 5000.0 * t[None, :]
              + c_off[:, None] * tau_rate * (1 - np.exp(-t[None, :] / tau_rate))
              + rng.normal(0, 0.02, (3, n)).cumsum(axis=1) * 0.05)
    win_s, hop_s = 0.008, 0.002
    w = windowed_phase_rates(phases, fs, window_s=win_s, hop_s=hop_s)
    sig = ((w[0] - w[1]) ** 2 + (w[1] - w[2]) ** 2 + (w[2] - w[0]) ** 2) / 3.0
    tsig = np.arange(sig.size) * hop_s
    y = sig / np.nanmax(sig)
    good = np.isfinite(y)
    mc = model_comparison(tsig[good], y[good])
    VALUES["aniso_tau_truth_ms"] = tau_rate / 2 * 1e3
    VALUES["aniso_best_model"] = mc["best_by_AIC"]
    VALUES["aniso_aic"] = {k: float(v["AIC"]) for k, v in mc.items()
                           if isinstance(v, dict) and "AIC" in v}
    VALUES["aniso_tau_s"] = float(mc["exponential"]["params"]["tau_s"])

    fig, ax = plt.subplots(figsize=(5.6, 3.3))
    ax.semilogy(tsig * 1e3, y, "o", ms=2.5, color=C_EST, alpha=0.6,
                label="synthetic $\\sigma_\\phi^2(t)$ (normalised)")
    tt = np.linspace(tsig[good][0], tsig[good][-1], 400)
    p = mc["exponential"]["params"]
    ax.semilogy(tt * 1e3, p["A"] * np.exp(-tt / p["tau_s"]), color=C_HYP,
                label=f"exponential fit ($\\tau_c={p['tau_s']*1e3:.1f}$ ms), AIC={mc['exponential']['AIC']:.0f}")
    pp = mc["power_law"]["params"]
    ax.semilogy(tt * 1e3, pp["A"] * (1 + tt / pp["t0_s"]) ** (-pp["p"]), "--",
                color=C_DER,
                label=f"power law, AIC={mc['power_law']['AIC']:.0f}")
    pc = mc["no_change"]["params"]
    ax.semilogy(tt * 1e3, np.full_like(tt, pc["c"]), ":", color=C_GRAY,
                label=f"no-change null, AIC={mc['no_change']['AIC']:.0f}")
    ax.set_xlabel("post-drive time (ms)")
    ax.set_ylabel("normalised $\\sigma_\\phi^2$")
    ax.legend(frameon=False, fontsize=7.2, loc="lower left")
    ax.set_title(f"decay-law adjudication on a seeded synthetic ringdown; best by AIC: {mc['best_by_AIC'].replace('_', ' ')}",
                 fontsize=8.2)
    save(fig, "fig_anisotropy_decay.pdf")


# ----------------------------------------------------------------------
# Figure 10 — experimental control matrix
# ----------------------------------------------------------------------
def fig_control_matrix():
    branches = ["1 modal survey", "2 electrode pulse", "3 sound key",
                "4 opposed coil", "5 human loading", "6 spiral cone",
                "7 water (exploratory)", "8 spatial mapping"]
    controls = ["instrument-\nonly", "no-specimen /\ndummy load", "matched\nspecimen",
                "matched off-\nfrequency", "sham\n(zero drive)", "positive\ninjection",
                "randomised +\nblinded", "sensor swap /\nreposition"]
    # 2 = required_before_claim gate, 1 = required, 0 = n/a
    M = np.array([
        [1, 2, 2, 0, 0, 1, 1, 1],
        [2, 2, 1, 0, 2, 2, 1, 0],
        [2, 2, 0, 2, 2, 2, 1, 0],
        [2, 2, 1, 0, 1, 2, 1, 0],
        [1, 2, 1, 0, 1, 2, 1, 0],
        [1, 2, 2, 0, 0, 1, 1, 0],
        [1, 2, 0, 0, 2, 2, 1, 0],
        [2, 1, 0, 0, 1, 2, 1, 2],
    ])
    fig, ax = plt.subplots(figsize=(6.7, 3.4))
    cmap = matplotlib.colors.ListedColormap(["#f2f3f5", "#9BB8CE", "#17324D"])
    ax.imshow(M, cmap=cmap, aspect="auto", vmin=0, vmax=2)
    ax.set_xticks(range(len(controls)))
    ax.set_xticklabels(controls, fontsize=7)
    ax.set_yticks(range(len(branches)))
    ax.set_yticklabels(branches, fontsize=7.5)
    ax.set_xticks(np.arange(-0.5, len(controls)), minor=True)
    ax.set_yticks(np.arange(-0.5, len(branches)), minor=True)
    ax.grid(which="minor", color="white", lw=1.4)
    ax.tick_params(which="both", length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    handles = [Rectangle((0, 0), 1, 1, fc=c) for c in ["#f2f3f5", "#9BB8CE", "#17324D"]]
    ax.legend(handles, ["not applicable", "required", "gates any claim\n(required before claim)"],
              loc="upper left", bbox_to_anchor=(1.01, 1.0), frameon=False, fontsize=7.2)
    ax.set_title("control classes per experimental branch (CONTROL_MATRIX v1.0.0)", fontsize=8.6)
    save(fig, "fig_control_matrix.pdf")


# ----------------------------------------------------------------------
# Figure 11 — complete forward hierarchy (landscape page)
# ----------------------------------------------------------------------
def fig_forward_hierarchy():
    # live numbers from the core
    v = default_wave_speed()
    L5 = ladder_length_mm(5)
    fax110 = axial_half_wave(110.0)
    spec = compact_mode_spectrum(v_chi=v, compact_radius_mm=100.0, n_max=1)
    f1 = uv(spec["modes"][0]["frequency"])
    g = SpiralGeometry()
    met = spiral_metrics(g)
    two = coupled_two_mode(1000.0, 1000.0, 10.0, 1000.0, 1000.0)
    eq = epsilon_q(1000.0, 800.0)

    fig, ax = plt.subplots(figsize=(10.4, 6.4))
    ax.set_xlim(0, 15.2)
    ax.set_ylim(0, 9)
    ax.axis("off")
    fs = 6.6

    box(ax, 0.2, 7.2, 3.4, 1.5,
        f"INPUTS  [EST/SRC]\n$v_L = {v.mean:.0f}$ m/s $\\pm{v.u_rel*100:.0f}\\%$\n(Bechmann 1958 band);\n$f_0 = 4096$ Hz (source claim);\ngeometry $\\mathcal{{G}}$",
        C_EST, fontsize=fs)
    box(ax, 0.2, 5.0, 3.4, 1.5,
        f"SPIRAL STATE  [EST math]\n$q=e$, $T=4$, $R_0=60$ mm,\n$H=80$ mm, $p_z=1.5$;\n$a={met['pitch_parameter_a']:.5f}$, $r\\kappa={met['curvature_invariant_rkappa']:.5f}$",
        C_EST, fontsize=fs)
    box(ax, 0.2, 2.8, 3.4, 1.5,
        "DRIVE PRESETS  [SRC]\n20 Hz electrode; 1496 Hz key;\n4096 Hz coil, exact-cycle\nfamilies 2261 / 1508 / 1131",
        C_SRC, fontsize=fs)

    box(ax, 4.4, 7.2, 3.6, 1.5,
        f"4096 LADDER  [DER]\n$L_5 = {L5.mean:.3f}$ mm $\\pm{L5.u_rel*100:.0f}\\%$;\n$f_{{ax}}(110$ mm$) = {fax110.mean:.1f}$ Hz $\\pm{fax110.u_rel*100:.0f}\\%$;\nset-valued class $\\mathcal{{N}}$",
        C_DER, fontsize=fs)
    box(ax, 4.4, 5.0, 3.6, 1.5,
        f"COMPACT SPECTRUM  [HYP H-01]\n$f_n^2 = f_b^2+(n\\kappa_\\chi)^2$;\n$n=1$: {f1['mean']:.1f} Hz $\\pm{f1['u_rel']*100:.0f}\\%$\n($R_\\chi = 100$ mm placeholder)",
        C_HYP, fontsize=fs)
    box(ax, 4.4, 2.8, 3.6, 1.5,
        f"SPIRAL PATH  [DER + HYP H-06a]\n$\\ell_{{3D}} = {met['path_length_3d_mm']:.2f}$ mm (numeric,\nauthoritative); $R_\\chi^{{(s)}} = {met['compact_radius_prior_mm']:.2f}$ mm;\nclosed form {met['retired_closed_form_rel_error']*100:.2f}% (retired)",
        C_HYP, fontsize=fs)

    box(ax, 8.8, 7.2, 3.3, 1.5,
        f"RESONANCE OFFSET  [DER]\n$\\epsilon_R^{{(f)}} = [f_m^2-(pf_x)^2]/(pf_x)^2$;\nclasses at $1/5/50 \\times \\epsilon_Q$;\n$\\epsilon_Q = 1/Q_{{\\mathrm{{eff}}}} = ${eq:.2e}",
        C_DER, fontsize=fs)
    box(ax, 8.8, 5.0, 3.3, 1.5,
        f"COUPLED MODES  [EST]\n$f_A = f_B = 1000$ Hz, $g = 10$ Hz\n$\\Rightarrow f_\\pm = {two['lower_hybrid_hz']:.0f}$ / {two['upper_hybrid_hz']:.0f} Hz;\nsplitting $2g$; ratio $R_g$",
        C_EST, fontsize=fs)
    box(ax, 8.8, 2.8, 3.3, 1.5,
        "DYNAMICS  [HYP H-09]\n$\\dot z_n = (G_n-\\gamma_n+i\\omega_n)z_n$\n$- \\Sigma\\beta_{nm}|z_m|^2z_n + \\Sigma K_{nm}z_m$;\nconsistency $|K| = 2\\pi g$ ($K = i2\\pi g$)",
        C_HYP, fontsize=fs)

    box(ax, 12.9, 6.1, 2.1, 2.6,
        "MEASUREMENT  [EST]\nI/Q single-shot,\nshared clock;\n$(\\mathcal{C}_w, w, b_w)$\n+ amplitude;\n$\\Sigma_\\phi$, $\\sigma_\\phi^2$;\nRayleigh $Z_R$",
        C_EST, fontsize=fs)
    box(ax, 12.9, 2.8, 2.1, 2.6,
        "VERDICTS\ncontrols first;\n$G_c$, $d_c$;\nAIC/BIC model\ncomparison;\nH-01..H-14\nfailure conditions",
        C_DER, fontsize=fs)

    box(ax, 4.4, 0.4, 7.7, 1.6,
        "CALIBRATION LEDGER  [DER]\n$f_\\mathrm{meas} = f_\\mathrm{0,pred}(1+\\delta_\\mathrm{geom}+\\delta_\\mathrm{aniso}+\\delta_\\mathrm{load}+\\delta_T+\\delta_\\mathrm{fixt}+\\delta_\\mathrm{drive})+\\epsilon_{ns}$\nsigned corrections can move $\\epsilon_R^{(f)}$ through zero (Lee–Tsai Eqs. (11)–(13)\ntemplate); repeated $\\delta_k$ stability gates every $\\epsilon$ interpretation",
        "#5c5f66", fontsize=fs)

    for a, b in [((3.6, 7.95), (4.4, 7.95)), ((3.6, 5.75), (4.4, 5.75)),
                 ((3.6, 3.55), (4.4, 3.55)),
                 ((8.0, 7.95), (8.8, 7.95)), ((8.0, 5.75), (8.8, 5.75)),
                 ((8.0, 3.55), (8.8, 3.55)),
                 ((6.2, 4.3), (6.2, 5.0)),    # spiral prior -> compact
                 ((6.2, 7.2), (6.2, 6.5)),    # ladder -> compact context
                 ((12.1, 7.95), (12.9, 7.6)), ((12.1, 5.75), (12.9, 6.6)),
                 ((12.1, 3.55), (12.9, 3.9)),
                 ((13.95, 6.1), (13.95, 5.4))]:
        arrow(ax, a, b)
    arrow(ax, (4.4, 1.2), (1.9, 2.8), color=C_HYP, rad=-0.25)
    arrow(ax, (12.1, 1.2), (13.4, 2.8), color=C_HYP, rad=-0.2)
    ax.set_title("RGCS v2 complete forward hierarchy — every number computed by rgcs_core 2.0.0 at build time",
                 fontsize=9)
    save(fig, "fig_forward_hierarchy.pdf")


def main() -> None:
    fig_architecture()
    fig_compact_ladder()
    fig_parity_families()
    fig_epsilon_map()
    fig_avoided_crossing()
    fig_spiral()
    fig_phase_randomization()
    fig_coherence_vs_amplitude()
    fig_anisotropy_decay()
    fig_control_matrix()
    fig_forward_hierarchy()
    with open(FIG_DIR / "fig_values.json", "w") as fh:
        json.dump(VALUES, fh, indent=1, default=float)
    print(f"wrote {FIG_DIR / 'fig_values.json'}")


if __name__ == "__main__":
    main()
