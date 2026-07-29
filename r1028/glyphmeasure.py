"""R10.42 — actual pixel measurement of crop-glyph diagrams.

WHY THIS EXISTS
---------------
Every ratio claim so far has rested on eyeballed pixel values, and the
null makes eyeballing useless: simple ratios p/q with +-5% windows cover
86% of the range 1-4. A measurement that is only good to +-5% cannot
distinguish a real ratio from noise.

Pre-specified targets are different. phi and sqrt2 are named in the
source's own check formula BEFORE measurement, and a +-2% window round
just those two covers only 4% of the range. So the whole question is
whether we can measure to about +-1-2%.

PRECISION BUDGET, which decides what images are worth measuring
---------------------------------------------------------------
Edge localisation on a clean vector diagram is roughly +-1 px. So the
relative error on a radius r is about 1/r:

    r =  20 px  ->  +-5.0%    useless
    r =  35 px  ->  +-2.9%    marginal
    r =  50 px  ->  +-2.0%    borderline
    r = 100 px  ->  +-1.0%    usable
    r = 200 px  ->  +-0.5%    good

A 575-px-wide archive diagram gives radii of roughly 20-50 px, i.e.
+-2-5%. That is NOT enough to test phi against sqrt2 (they differ by
14%, so it is enough to tell those two apart, but not enough to claim
either against a generic simple ratio).

CONCLUSION: request diagrams at >= 2000 px wide, or measure the FIELD
PHOTOS against a known ground scale. Otherwise the measurement cannot
beat its own null no matter how careful the analysis is.

USAGE
    python -m r1028.glyphmeasure <image.png> [--min-radius N]
"""

from __future__ import annotations

import math
import sys

PHI = (1 + 5 ** 0.5) / 2
SQRT2 = 2 ** 0.5

#: Targets named by the SOURCE before any measurement. Only these count
#: as pre-specified; anything else is post-hoc.
PRESPECIFIED = {"phi": PHI, "sqrt2": SQRT2, "sqrt2_over_phi": SQRT2 / PHI,
                "2": 2.0, "phi_squared": PHI ** 2}


def precision_budget(radius_px: float, edge_error_px: float = 1.0) -> dict:
    rel = edge_error_px / radius_px if radius_px else float("inf")
    return {
        "radius_px": radius_px, "edge_error_px": edge_error_px,
        "relative_error": rel, "percent": 100 * rel,
        "can_test_prespecified_at_2pct": rel <= 0.02,
        "can_distinguish_phi_from_sqrt2": rel <= 0.07,
        "verdict": ("USABLE" if rel <= 0.02 else
                    "MARGINAL" if rel <= 0.05 else "TOO_COARSE"),
    }


def required_radius_px(target_pct: float = 2.0,
                       edge_error_px: float = 1.0) -> float:
    return 100.0 * edge_error_px / target_pct


def detect_circles(path: str, min_radius: int = 8):
    """Measure circles from a diagram. Requires numpy + PIL.

    Returns (cx, cy, r) triples. Works on the flat-colour archive
    diagrams by thresholding to ink and finding connected components,
    then fitting a radius from component area and extent.
    """
    try:
        import numpy as np
        from PIL import Image
    except ImportError as exc:                     # pragma: no cover
        raise RuntimeError(
            "needs numpy and pillow: pip install numpy pillow") from exc

    img = np.asarray(Image.open(path).convert("L"), dtype=float)
    ink = img < (img.max() * 0.75)                 # dark-on-light
    h, w = ink.shape
    seen = np.zeros_like(ink, dtype=bool)
    out = []
    for y in range(h):
        for x in range(w):
            if not ink[y, x] or seen[y, x]:
                continue
            # iterative flood fill
            stack, pts = [(y, x)], []
            seen[y, x] = True
            while stack:
                cy, cx = stack.pop()
                pts.append((cy, cx))
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = cy + dy, cx + dx
                    if (0 <= ny < h and 0 <= nx < w and ink[ny, nx]
                            and not seen[ny, nx]):
                        seen[ny, nx] = True
                        stack.append((ny, nx))
            if len(pts) < 20:
                continue
            ys = [p[0] for p in pts]
            xs = [p[1] for p in pts]
            cy, cx = sum(ys) / len(ys), sum(xs) / len(xs)
            ry, rx = (max(ys) - min(ys)) / 2, (max(xs) - min(xs)) / 2
            r = (ry + rx) / 2
            circularity = min(ry, rx) / max(ry, rx) if max(ry, rx) else 0
            if r >= min_radius and circularity > 0.80:
                out.append({"cx": round(cx, 2), "cy": round(cy, 2),
                            "r": round(r, 2), "pixels": len(pts),
                            "circularity": round(circularity, 3)})
    return sorted(out, key=lambda c: c["cx"])


def pairwise_geometry(circles) -> list:
    rows = []
    for i in range(len(circles)):
        for j in range(i + 1, len(circles)):
            a, b = circles[i], circles[j]
            d = math.hypot(b["cx"] - a["cx"], b["cy"] - a["cy"])
            ang = math.degrees(math.atan2(-(b["cy"] - a["cy"]),
                                          b["cx"] - a["cx"]))
            ratio = max(a["r"], b["r"]) / min(a["r"], b["r"])
            best = min(PRESPECIFIED,
                       key=lambda k: abs(PRESPECIFIED[k] - ratio))
            off = abs(PRESPECIFIED[best] - ratio) / ratio
            rows.append({
                "a": i, "b": j, "r_a": a["r"], "r_b": b["r"],
                "radius_ratio": round(ratio, 4),
                "centre_distance_px": round(d, 2),
                "angle_deg": round(ang, 2),
                "d_over_r_a": round(d / a["r"], 4) if a["r"] else None,
                "nearest_prespecified": best,
                "percent_off": round(100 * off, 2),
                "hits_prespecified_at_2pct": off <= 0.02,
            })
    return rows


def measure(path: str, min_radius: int = 8) -> dict:
    circles = detect_circles(path, min_radius)
    pairs = pairwise_geometry(circles)
    budgets = [precision_budget(c["r"]) for c in circles]
    usable = [b for b in budgets if b["verdict"] == "USABLE"]
    return {
        "schema": "rgcs.r1042.glyph-measure.v1",
        "image": path,
        "circles": circles, "circle_count": len(circles),
        "pairs": pairs,
        "precision": budgets,
        "usable_circles": len(usable),
        "measurement_is_trustworthy": len(usable) == len(circles) and circles,
        "required_radius_for_2pct_px": required_radius_px(2.0),
        "prespecified_targets": PRESPECIFIED,
        "note": "only 'hits_prespecified_at_2pct' on circles whose "
                "precision verdict is USABLE should be treated as "
                "evidence; anything coarser is inside the null",
    }


if __name__ == "__main__":                          # pragma: no cover
    import json
    if len(sys.argv) < 2:
        print(__doc__)
        print(f"\nradius needed for +-2%: "
              f"{required_radius_px(2.0):.0f} px")
        for r in (20, 35, 50, 100, 200):
            b = precision_budget(r)
            print(f"  r={r:4d}px -> +-{b['percent']:4.1f}%  {b['verdict']}")
        sys.exit(0)
    print(json.dumps(measure(sys.argv[1]), indent=2))
