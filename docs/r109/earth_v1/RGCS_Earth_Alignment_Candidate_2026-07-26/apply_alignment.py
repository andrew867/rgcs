#!/usr/bin/env python3
"""Apply the frozen RGCS Earth-alignment candidate.

This script does not refit anything. It loads the complete composed warp,
maps a unit source vector to conventional ECEF, and can numerically invert
known/calibrated points.

Status: calibrated candidate, not independent validation.
"""
from __future__ import annotations
import argparse
import gzip
import json
import math
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
with gzip.open(HERE / "operator" / "WARP_STEPS.json.gz", "rt", encoding="utf-8") as fh:
    STEPS = json.load(fh)

def norm_rows(a):
    a = np.atleast_2d(np.asarray(a, dtype=float))
    return a / np.linalg.norm(a, axis=1)[:, None]

def apply(points):
    y = norm_rows(points)
    for step in STEPS:
        c = np.asarray(step["centers_ecef"], dtype=float)
        w = np.asarray(step["weights_ecef"], dtype=float)
        s = float(step["sigma"])
        d2 = np.sum((y[:, None, :] - c[None, :, :]) ** 2, axis=2)
        y = y + np.exp(-d2 / (2*s*s)) @ w
        y = norm_rows(y)
    return y

def latlon(v):
    v = np.asarray(v, dtype=float)
    v = v / np.linalg.norm(v)
    return math.degrees(math.asin(v[2])), math.degrees(math.atan2(v[1], v[0]))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("x", type=float)
    ap.add_argument("y", type=float)
    ap.add_argument("z", type=float)
    args = ap.parse_args()
    out = apply([[args.x, args.y, args.z]])[0]
    la, lo = latlon(out)
    print(json.dumps({
        "mapped_unit_ecef": out.tolist(),
        "latitude_deg": la,
        "longitude_deg": lo,
        "status": "CALIBRATED_CANDIDATE_NOT_VALIDATED"
    }, indent=2))

if __name__ == "__main__":
    main()
