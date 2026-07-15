#!/usr/bin/env python3
"""Generate the README PNG figures (docs/images/) from the tested
libraries — the same math as the manuscript figures, rendered for GitHub.

Run:  python tools/make_readme_images.py
Deterministic (SOURCE_DATE_EPOCH pinned; PNGs carry no timestamp text).
Fixes D-V3-05: the original one-off shell generation escaped the ``$``
characters, so matplotlib rendered the mathtext markup literally.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("SOURCE_DATE_EPOCH", "0")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
OUT = REPO / "docs" / "images"


def anisotropy_sweep() -> None:
    from rgcs_core.anisotropy import wave_speeds
    from rgcs_core.uncertainty import default_wave_speed
    v2b = default_wave_speed()
    lo, hi = v2b.interval(k=1.0)
    angles = np.linspace(0.0, 90.0, 91)
    vql = [wave_speeds(np.array([np.cos(np.radians(a)), 0.0,
                                 np.sin(np.radians(a))]))["v_quasi_long_m_s"]
           for a in angles]
    fig, ax = plt.subplots(figsize=(6.4, 3.4), dpi=130)
    ax.plot(angles, vql,
            label=r"$v_{qL}(\theta)$ anisotropic (RSCS-O.17)")
    ax.axhspan(lo, hi, alpha=0.15,
               label=r"v2 scalar $v_L \pm 5\%$ band")
    ax.axhline(v2b.mean, ls=":", lw=1)
    ax.set_xlabel("propagation angle from X toward Z (deg)")
    ax.set_ylabel("quasi-longitudinal speed (m/s)")
    ax.set_title("Anisotropic model recovers the v2 scalar as its "
                 "special case")
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "anisotropy_sweep.png")
    plt.close(fig)
    print("wrote docs/images/anisotropy_sweep.png")


def macro_envelopes() -> None:
    from rgcs_desktop.services.waveform_preview import preview_macro_envelope
    fig, axes = plt.subplots(3, 1, figsize=(7.0, 3.2), sharex=True,
                             dpi=130)
    for axi, mode in zip(axes, ("standard", "half_spacing",
                                "double_rate")):
        env = preview_macro_envelope(mode)
        for t0, t1, state in env["segments"]:
            if state == "on":
                axi.axvspan(t0, t1, color="#17324D")
            elif state == "pause":
                axi.axvspan(t0, t1, color="#C9DAE7")
        axi.set_yticks([])
        axi.set_ylabel(mode, rotation=0, ha="right", va="center",
                       fontsize=8)
        axi.set_xlim(0, 560)
    axes[0].set_title("The three frozen macro drive envelopes "
                      "(cycle-exact)")
    axes[-1].set_xlabel("time (ms)")
    fig.tight_layout()
    fig.savefig(OUT / "macro_envelopes.png")
    plt.close(fig)
    print("wrote docs/images/macro_envelopes.png")


def main() -> int:
    OUT.mkdir(exist_ok=True)
    anisotropy_sweep()
    macro_envelopes()
    return 0


if __name__ == "__main__":
    sys.exit(main())
