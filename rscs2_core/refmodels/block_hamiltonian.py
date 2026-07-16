"""Generic phonon-magnon-exciton block Hamiltonian (Agent M4).

Typed blocks + capability-gated construction through the M2 coupling
graph; Hermitian and dissipative variants with stability checks;
export hook for future microscopic solver adapters (INTERFACE_ONLY)."""

from __future__ import annotations

import numpy as np

from ..multiphysics import (CouplingEdge, CouplingGraph, get_material)

_BLOCK_CAPABILITY = {"phonon_internal": "spin_phonon_coupling",
                     "magnon": "magnon_modes",
                     "exciton": "exciton_frenkel",
                     "spin": "magnetic_order"}


class BlockHamiltonian:
    """Blocks: name -> mode frequencies (Hz). Couplings: capability-
    checked scalar g between named blocks (single-mode per block pair
    coupling in this reduced model)."""

    def __init__(self, material_id: str):
        self.material = get_material(material_id)
        self.blocks: dict[str, np.ndarray] = {}
        self.graph = CouplingGraph(self.material)
        self._pairs: list = []

    def add_block(self, name: str, freqs_hz, gamma_hz=None):
        if name not in _BLOCK_CAPABILITY:
            raise ValueError(f"unknown block '{name}'")
        # adding a block itself requires the capability (gate E5)
        edge = CouplingEdge(
            name, name, f"op.block.{name}", "Hz", "diagonal",
            _BLOCK_CAPABILITY[name], "REDUCED_ORDER_VALIDATED",
            null_behavior="isolated block")
        self.graph.add_edge(edge)     # raises CouplingRejected if barred
        f = np.atleast_1d(np.asarray(freqs_hz, float))
        g = np.zeros_like(f) if gamma_hz is None else \
            np.atleast_1d(np.asarray(gamma_hz, float))
        self.blocks[name] = (f, g)
        return self

    def couple(self, a: str, b: str, g_hz: float):
        for n in (a, b):
            if n not in self.blocks:
                raise ValueError(f"block '{n}' not added")
        self._pairs.append((a, b, float(g_hz)))
        return self

    def matrix(self, dissipative: bool = True) -> np.ndarray:
        names, offs, n = [], {}, 0
        for name, (f, _) in self.blocks.items():
            offs[name] = n
            names.append(name)
            n += len(f)
        H = np.zeros((n, n), complex)
        for name, (f, gam) in self.blocks.items():
            i = offs[name]
            for k in range(len(f)):
                H[i + k, i + k] = f[k] - (1j * gam[k] / 2 if
                                          dissipative else 0.0)
        for a, b, g in self._pairs:
            ia, ib = offs[a], offs[b]
            H[ia, ib] += g
            H[ib, ia] += g
        return H

    def eigenmodes(self, dissipative: bool = True) -> dict:
        H = self.matrix(dissipative)
        vals, vecs = np.linalg.eig(H)
        order = np.argsort(vals.real)
        vals = vals[order]
        stable = bool(np.all(vals.imag <= 1e-12))
        if dissipative and not stable:
            raise ArithmeticError(
                "dissipative block Hamiltonian produced a growing "
                "pole — unstable parameterization rejected")
        hermitian_check = None
        if not dissipative:
            hermitian_check = float(np.max(np.abs(vals.imag)))
        return {"poles_hz": vals, "stable": stable,
                "hermitian_residual_hz": hermitian_check}

    def export_interface(self) -> dict:
        """INTERFACE_ONLY export for future microscopic solvers."""
        return {"classification": "INTERFACE_ONLY",
                "material_id": self.material.material_id,
                "blocks": {k: {"freqs_hz": v[0].tolist(),
                               "gamma_hz": v[1].tolist()}
                           for k, v in self.blocks.items()},
                "couplings": [{"a": a, "b": b, "g_hz": g}
                              for a, b, g in self._pairs],
                "note": "schema export; no microscopic computation "
                        "is implemented or implied"}
