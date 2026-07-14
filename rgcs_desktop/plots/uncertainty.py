"""pyqtgraph helpers: spectra with 1-sigma uncertainty bands, time series."""
from __future__ import annotations

from typing import Sequence

import numpy as np
import pyqtgraph as pg

pg.setConfigOptions(antialias=True, background="w", foreground="k")


def make_plot(title: str = "", x_label: str = "", y_label: str = "",
              parent=None) -> pg.PlotWidget:
    w = pg.PlotWidget(parent=parent, title=title)
    if x_label:
        w.setLabel("bottom", x_label)
    if y_label:
        w.setLabel("left", y_label)
    w.showGrid(x=True, y=True, alpha=0.25)
    return w


def plot_series(plot: pg.PlotWidget, x: Sequence[float], y: Sequence[float],
                name: str = "", color: str = "#1258a8", width: float = 1.5):
    pen = pg.mkPen(color, width=width)
    return plot.plot(np.asarray(x, float), np.asarray(y, float),
                     pen=pen, name=name)


def plot_spectrum_with_bands(plot: pg.PlotWidget,
                             modes: Sequence[dict]) -> None:
    """Plot compact-mode frequencies as vertical stems with 1-sigma bands.

    ``modes``: list of dicts with keys n and frequency dict
    (mean/lo_1sigma/hi_1sigma) — the compact_mode_spectrum output. Uncertain
    values are ALWAYS drawn with their interval band, never as bare points.
    """
    plot.clear()
    ns, means, los, his = [], [], [], []
    for m in modes:
        f = m["frequency"]
        if isinstance(f, dict):
            mean, lo, hi = f["mean"], f["lo_1sigma"], f["hi_1sigma"]
        else:  # UncertainValue
            mean = f.mean
            lo, hi = f.interval(1)
        ns.append(m["n"])
        means.append(mean)
        los.append(lo)
        his.append(hi)
    ns_a = np.asarray(ns, float)
    means_a = np.asarray(means, float)
    los_a = np.asarray(los, float)
    his_a = np.asarray(his, float)
    # 1-sigma band per mode as an error bar + stem
    err = pg.ErrorBarItem(x=ns_a, y=means_a,
                          top=his_a - means_a, bottom=means_a - los_a,
                          beam=0.18, pen=pg.mkPen("#b26a00", width=2))
    plot.addItem(err)
    bar = pg.BarGraphItem(x=ns_a, height=means_a, width=0.06,
                          brush="#1258a8", pen=pg.mkPen(None))
    plot.addItem(bar)
    scatter = pg.ScatterPlotItem(x=ns_a, y=means_a, size=7,
                                 brush=pg.mkBrush("#1258a8"))
    plot.addItem(scatter)
    plot.setLabel("bottom", "mode index n")
    plot.setLabel("left", "frequency (Hz)")
