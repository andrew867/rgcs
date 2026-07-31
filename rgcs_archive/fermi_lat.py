"""R10.61A -- Fermi LAT LS-002 / FT1 photon adapter.

Official interpretation of the product::

    LS-002 / FT1 -- selected parameters for events considered to be
    photons detected by the LAT

"Considered to be photons" is doing real work in that sentence. FT1 rows
are *classified* events, not raw detector hits, and the classification is
a ground-processing product. Event class and event type are therefore
carried on every stream receipt, because a result that depends on which
class cut was applied is a statement about the cut.

PRIMARY SIGNAL LANE
-------------------
    photon arrival times
      -> inter-arrival intervals
      -> pulse/gap hierarchy
      -> energy-conditioned pulse/gap streams

Arrival times are the physically meaningful sequence. Everything else in
this module is derived from them and says so.
"""

from __future__ import annotations

import hashlib

import numpy as np

#: FT1 columns this adapter knows how to read. Missing ones are reported,
#: never silently defaulted.
FT1_COLUMNS = ("TIME", "ENERGY", "RA", "DEC", "L", "B",
               "EVENT_CLASS", "EVENT_TYPE", "CONVERSION_TYPE",
               "ZENITH_ANGLE", "THETA", "PHI")

REQUIRED_COLUMNS = ("TIME",)

#: Energy bands in MeV. Frozen: bands are declared, never fitted.
ENERGY_BANDS_MEV = ((30, 100), (100, 300), (300, 1000),
                    (1000, 10000), (10000, 300000))

STREAMS = ("TIME", "INTER_ARRIVAL_DELTA", "LOG_DELTA", "ENERGY",
           "SKY_DIRECTION", "EVENT_CLASS", "EVENT_TYPE", "CONVERSION_TYPE",
           "ZENITH_ANGLE", "INCIDENCE_ANGLE",
           "PER_ENERGY_BAND_ARRIVAL", "PER_SKY_REGION_ARRIVAL",
           "BURST_LOCAL_WINDOW")

CONTROLS = ("off_source_region", "time_shuffled", "delta_shuffled",
            "pre_trigger_window", "post_trigger_window")


class LatError(ValueError):
    """An FT1 product cannot be read as requested."""


def inspect_ft1(path: str) -> dict:
    """Report which FT1 columns are present. No defaults, no assumptions."""
    from astropy.io import fits
    with fits.open(path, memmap=False) as hdul:
        events = None
        for i, h in enumerate(hdul):
            if getattr(h, "columns", None) is not None and \
                    "TIME" in h.columns.names:
                events = (i, h)
                break
        if events is None:
            raise LatError("no HDU with a TIME column; is this an FT1 file?")
        idx, hdu = events
        present = list(hdu.columns.names)
        return {
            "schema": "rgcs.r1061a.ft1-inspect.v1",
            "path": path, "events_hdu": idx,
            "rows": int(len(hdu.data)),
            "columns_present": present,
            "known_columns_present": [c for c in FT1_COLUMNS if c in present],
            "known_columns_absent": [c for c in FT1_COLUMNS
                                     if c not in present],
            "required_present": all(c in present for c in REQUIRED_COLUMNS),
            "product": "LS-002 / FT1",
            "interpretation": "selected parameters for events CONSIDERED TO "
                              "BE photons detected by the LAT; rows are "
                              "classified events, not raw detector hits",
        }


def _col(hdu, name):
    if name not in hdu.columns.names:
        raise LatError(f"column {name!r} absent; "
                       f"present: {hdu.columns.names}")
    return np.asarray(hdu.data[name])


def photon_streams(path: str, tmin: float | None = None,
                   tmax: float | None = None,
                   energy_band_mev: tuple | None = None,
                   max_events: int | None = None) -> dict:
    """The primary lane: arrival times -> deltas -> log-deltas, plus context.

    Windows and bands are applied BEFORE derivation and recorded on the
    receipt, so a stream can always be traced to the cut that produced it.
    """
    from astropy.io import fits
    with fits.open(path, memmap=False) as hdul:
        ins = inspect_ft1(path)
        hdu = hdul[ins["events_hdu"]]
        t = _col(hdu, "TIME").astype(np.float64)
        order = np.argsort(t, kind="stable")
        t = t[order]
        keep = np.ones(t.size, dtype=bool)
        if tmin is not None:
            keep &= t >= tmin
        if tmax is not None:
            keep &= t <= tmax
        energy = None
        if "ENERGY" in hdu.columns.names:
            energy = _col(hdu, "ENERGY").astype(np.float64)[order]
            if energy_band_mev:
                lo, hi = energy_band_mev
                keep &= (energy >= lo) & (energy < hi)
        t = t[keep]
        if energy is not None:
            energy = energy[keep]
        if max_events:
            t = t[:max_events]
            if energy is not None:
                energy = energy[:max_events]
        extras = {}
        for name in ("RA", "DEC", "EVENT_CLASS", "EVENT_TYPE",
                     "CONVERSION_TYPE", "ZENITH_ANGLE", "THETA"):
            if name in hdu.columns.names:
                v = np.asarray(hdu.data[name])[order][keep]
                extras[name] = v[:max_events] if max_events else v

    if t.size < 2:
        raise LatError(f"only {t.size} events survive the cut; need >= 2")
    delta = np.diff(t)
    positive = delta[delta > 0]
    log_delta = np.log10(positive) if positive.size else np.array([])
    return {
        "schema": "rgcs.r1061a.ft1-streams.v1",
        "path": path,
        "source_hash": _file_sha(path),
        "events": int(t.size),
        "time_window": [float(t[0]), float(t[-1])],
        "duration_s": float(t[-1] - t[0]),
        "cut": {"tmin": tmin, "tmax": tmax,
                "energy_band_mev": list(energy_band_mev)
                if energy_band_mev else None,
                "max_events": max_events},
        "inter_arrival": {
            "count": int(delta.size),
            "min_s": float(delta.min()), "max_s": float(delta.max()),
            "median_s": float(np.median(delta)),
            "mean_s": float(delta.mean()),
            "non_positive": int((delta <= 0).sum()),
        },
        "log_delta": {
            "count": int(log_delta.size),
            "mean": float(log_delta.mean()) if log_delta.size else None,
            "std": float(log_delta.std()) if log_delta.size else None,
        },
        "energy_mev": ({"min": float(energy.min()), "max": float(energy.max()),
                        "median": float(np.median(energy))}
                       if energy is not None and energy.size else None),
        "context_columns": sorted(extras),
        "event_class_values": (sorted(set(extras["EVENT_CLASS"].tolist()))[:8]
                               if "EVENT_CLASS" in extras else None),
        "derived_from": "TIME column, stable-sorted, then differenced",
        "lossy": False,
        "note": "rows are CLASSIFIED events; any result depending on the "
                "class cut is a statement about the cut",
    }


def poisson_null(rate_hz: float, n: int, seed: int = 5) -> dict:
    """Matched Poisson control: same rate, no structure."""
    rng = np.random.default_rng(seed)
    delta = rng.exponential(1.0 / rate_hz, size=n)
    return {"control": "matched_poisson", "rate_hz": rate_hz,
            "count": n, "median_s": float(np.median(delta)),
            "mean_s": float(delta.mean())}


def time_shuffled_null(delta, seed: int = 7) -> dict:
    """Permutation control: same interval multiset, order destroyed."""
    rng = np.random.default_rng(seed)
    d = np.asarray(delta, dtype=np.float64).copy()
    rng.shuffle(d)
    return {"control": "time_shuffled", "count": int(d.size),
            "median_s": float(np.median(d)), "mean_s": float(d.mean()),
            "preserves": "interval multiset", "destroys": "order"}


def _file_sha(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()
