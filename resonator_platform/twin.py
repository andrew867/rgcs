"""Digital twin: a simulator-backed resonator for dry runs (R007).

The twin is a modal model of a trim-capable disk resonator built from
the validated cymatic plate physics, with:

- fabrication variation (thickness, density, copper) drawn from
  declared tolerances with a seed;
- fixture coupling (boundary-condition stiffness shifts the spectrum);
- trim response: removing a sacrificial cell's mass shifts each mode
  by its local modal sensitivity, plus execution noise;
- measurement synthesis: a swept response with Lorentzian modes,
  noise, and instrument transfer function.

Everything it produces is SYNTHETIC and flagged so. The twin exists so
the control loop can be exercised and its guards proven BEFORE any
laser is ever pointed at a real board.
"""

from __future__ import annotations

import math

import numpy as np

from rscs2_core.cymatic_disk import (clamped_plate_lambdas,
                                     composite_plate, plate_mode_hz)


class TwinError(RuntimeError):
    pass


class ResonatorTwin:
    """A disk resonator with N sacrificial trim cells."""

    def __init__(self, radius_m: float = 0.05,
                 t_sub_m: float = 1.6e-3,
                 n_trim_cells: int = 16,
                 fab_tolerance: float = 0.02,
                 seed: int = 0):
        rng = np.random.default_rng(seed)
        # fabrication variation: thickness and stiffness within the
        # declared tolerance (R008 "simulated fabrication variation")
        self.thickness_error = 1.0 + fab_tolerance * \
            rng.standard_normal() * 0.5
        self.density_error = 1.0 + fab_tolerance * \
            rng.standard_normal() * 0.25
        self.radius_m = radius_m
        self.t_sub_m = t_sub_m * self.thickness_error
        self.plate = composite_plate(radius_m, self.t_sub_m)
        self.n_cells = n_trim_cells
        self.removed: list[int] = []
        self._rng = rng
        # per-cell modal sensitivity (Hz per cell removed, per mode):
        # cells sit at declared radii; sensitivity follows the mode
        # shape magnitude at the cell (outer cells move f more for
        # the fundamental because relative mass at large r matters
        # more for the (0,1) clamped mode's effective mass)
        self.cell_radius_frac = 0.55 + 0.4 * (
            np.arange(n_trim_cells) % 4) / 4.0
        self.cell_angle_rad = 2 * math.pi * \
            np.arange(n_trim_cells) / n_trim_cells
        self.fixture_shift_hz = 0.0
        self.cell_sensitivity_hz = np.zeros(n_trim_cells)
        base = self.mode_hz(0, 1)
        cell_mass_frac = 0.0018          # each cell ~0.18% of mass
        self.cell_sensitivity_hz = base * 0.5 * cell_mass_frac * \
            (0.5 + self.cell_radius_frac)     # df = f/2 * dm/m * w(r)
        self.synthetic = True

    # --- modes ---------------------------------------------------------------

    def mode_hz(self, n: int, m: int) -> float:
        f = plate_mode_hz(self.plate, n, m) / \
            math.sqrt(self.density_error)
        # trim: removing mass RAISES frequency (mass-dominated cells)
        f += sum(self.cell_sensitivity_hz[i] for i in self.removed) \
            * (1.0 if (n, m) == (0, 1) else 0.6)
        return f + self.fixture_shift_hz

    def mount(self, fixture_stiffness_factor: float = 1.0,
              remount_scatter_hz: float = 0.4) -> dict:
        """Fixture coupling: boundary stiffness shifts the spectrum;
        every remount adds scatter. The fixture is part of the
        instrument (R03)."""
        f0 = self.mode_hz(0, 1)
        systematic = f0 * 0.002 * (fixture_stiffness_factor - 1.0)
        scatter = remount_scatter_hz * self._rng.standard_normal()
        self.fixture_shift_hz = systematic + scatter
        return {"systematic_shift_hz": systematic,
                "remount_scatter_hz": scatter, "synthetic": True}

    # --- trims ----------------------------------------------------------------

    def execute_trim(self, cell_index: int,
                     execution_noise: float = 0.08) -> dict:
        """Irreversibly remove one sacrificial cell. The realized
        frequency shift differs from the predicted one by execution
        noise — that mismatch is what the empirical-update loop
        exists to learn (R039)."""
        if cell_index in self.removed:
            raise TwinError(f"cell {cell_index} already removed — "
                            "trims are irreversible")
        if not 0 <= cell_index < self.n_cells:
            raise TwinError("no such cell")
        before = self.mode_hz(0, 1)
        self.removed.append(cell_index)
        # execution noise: the laser removes slightly more or less
        noise = 1.0 + execution_noise * self._rng.standard_normal()
        self.cell_sensitivity_hz[cell_index] *= noise
        after = self.mode_hz(0, 1)
        return {"cell": cell_index, "before_hz": before,
                "after_hz": after,
                "realized_shift_hz": after - before,
                "synthetic": True, "irreversible": True}

    # --- synthetic measurement -------------------------------------------------

    def sweep(self, f_lo_hz: float, f_hi_hz: float, n_points: int,
              noise_floor: float = 0.01,
              drive_clipping: bool = False) -> dict:
        """Synthesize a swept magnitude response: Lorentzian modes on
        a noise floor, through a mild instrument transfer function.
        Optionally clipped, so the DAQ's artifact detector has
        something real to catch."""
        f = np.linspace(f_lo_hz, f_hi_hz, n_points)
        resp = np.full(n_points, noise_floor)
        modes = [(self.mode_hz(0, 1), 180.0, 1.0),
                 (self.mode_hz(1, 1), 150.0, 0.55),
                 (self.mode_hz(2, 1), 120.0, 0.35)]
        for f0, q, amp in modes:
            resp = resp + amp / np.sqrt(
                1.0 + (2 * q * (f - f0) / f0) ** 2)
        # instrument transfer function: gentle high-side tilt
        resp = resp * (1.0 + 0.05 * (f - f.mean()) / f.mean())
        resp = resp + noise_floor * 0.3 * \
            self._rng.standard_normal(n_points)
        clipped = False
        if drive_clipping:
            lim = 0.8 * resp.max()
            clipped = bool(np.any(resp > lim))
            resp = np.minimum(resp, lim)
        return {"f_hz": f, "magnitude": resp,
                "true_modes_hz": [m[0] for m in modes],
                "clipped": clipped, "synthetic": True}
