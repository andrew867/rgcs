"""P23b — a tomographic reconstruction model for the emission field, and
why a few coplanar views underdetermine it.

Where :mod:`r13.sixangle` reads one plane at six azimuths, this module
asks what an *image* of the emission field would take: a forward
projection (a Radon transform of a synthetic phantom), a filtered
back-projection that inverts it, and an honest account of what happens
when only a handful of angles are available.

**The round trip is the correctness test.** :func:`forward_project`
computes parallel-beam line integrals of a 2-D phantom at declared
angles; :func:`reconstruct` inverts them by ramp-filtered back-projection.
Given a full set of angles, a simple phantom -- a centred disk, or two
disks -- is recovered to within a small error. That the forward and
inverse transforms compose back to the phantom is what makes the model
correct, and it is the POWER control: a reconstruction that could not
recover a known phantom would be worthless.

**Few coplanar views underdetermine the field.** Reconstruct the same
phantom from only six angles -- the number the six-detector ring provides
-- and the result is streaky and misses features: the reconstruction
error rises sharply as the angle count falls, and the point-spread
function of a reconstructed point source broadens. :func:`error_vs_angles`
and :func:`psf_width` quantify both. This is the imaging statement of the
same limit :mod:`r13.sixangle` states for a single ring: a few coplanar
views do not determine a field.

**Synthetic throughout, and never promoted.** Every phantom is generated
here; no beam, detector, or sample exists. A reconstruction of numbers
this module made is not an image of a real source
(:func:`refuse_reconstruction_as_measured`), and a six-angle
reconstruction is a limited-angle slice, not a complete three-dimensional
field (:func:`refuse_fewangle_as_complete`). The standing verdict is
``IMAGING_RECONSTRUCTION_MODEL``.
"""

from __future__ import annotations

import math

import numpy as np

from r13.claimtypes import ClaimClass


class ImagingError(RuntimeError):
    """Raised on a malformed image, sinogram, or angle set, and -- load
    bearing -- on any attempt to read a synthetic reconstruction as a
    measurement or a few-angle slice as a complete 3-D field."""


CLAIM_CLASS = ClaimClass.NUMERICAL_SIMULATION.name
PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"
VERDICT = "IMAGING_RECONSTRUCTION_MODEL"


# --- synthetic phantoms ------------------------------------------------

def _disk(size: int, cx: float, cy: float, radius: float,
          amp: float = 1.0) -> np.ndarray:
    xs = np.arange(size, dtype=float)
    X, Y = np.meshgrid(xs, xs, indexing="ij")
    img = np.zeros((size, size), dtype=float)
    img[(X - cx) ** 2 + (Y - cy) ** 2 <= radius ** 2] = amp
    return img


def centered_disk_phantom(size: int = 64,
                          radius: float | None = None) -> np.ndarray:
    """A single centred disk -- the simplest recoverable phantom."""
    if size < 8:
        raise ImagingError("phantom size must be at least 8")
    c = (size - 1) / 2.0
    r = size * 0.18 if radius is None else float(radius)
    return _disk(size, c, c, r)


def two_disk_phantom(size: int = 64) -> np.ndarray:
    """Two small disks -- structure that few-angle streaks destroy."""
    if size < 8:
        raise ImagingError("phantom size must be at least 8")
    c = (size - 1) / 2.0
    r = size * 0.08
    off = size * 0.20
    return _disk(size, c - off, c, r) + _disk(size, c + off, c, r)


def point_phantom(size: int = 64) -> np.ndarray:
    """A small centred blob, for measuring the point-spread function."""
    if size < 8:
        raise ImagingError("phantom size must be at least 8")
    c = (size - 1) / 2.0
    return _disk(size, c, c, max(1.0, size * 0.02))


# --- bilinear sampling -------------------------------------------------

def _bilinear(image: np.ndarray, x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Sample ``image`` at fractional row ``x`` / column ``y``; 0 outside."""
    n_rows, n_cols = image.shape
    x0 = np.floor(x).astype(int)
    y0 = np.floor(y).astype(int)
    x1, y1 = x0 + 1, y0 + 1
    wx, wy = x - x0, y - y0

    def gather(ix: np.ndarray, iy: np.ndarray) -> np.ndarray:
        valid = (ix >= 0) & (ix < n_rows) & (iy >= 0) & (iy < n_cols)
        ixc = np.clip(ix, 0, n_rows - 1)
        iyc = np.clip(iy, 0, n_cols - 1)
        return np.where(valid, image[ixc, iyc], 0.0)

    return (gather(x0, y0) * (1 - wx) * (1 - wy)
            + gather(x1, y0) * wx * (1 - wy)
            + gather(x0, y1) * (1 - wx) * wy
            + gather(x1, y1) * wx * wy)


# --- forward projection (Radon) ----------------------------------------

def forward_project(image, angles_deg, *, n_detectors: int | None = None,
                    n_steps: int | None = None) -> np.ndarray:
    """Parallel-beam line-integral projections of ``image`` at ``angles``.

    Returns a sinogram of shape ``(n_angles, n_detectors)``. For each
    projection angle and detector offset ``s``, the ray is integrated
    along ``t`` by bilinear sampling of the phantom. This is a discrete
    Radon transform of a synthetic image -- nothing is measured.
    """
    img = np.asarray(image, dtype=float)
    if img.ndim != 2 or img.shape[0] != img.shape[1]:
        raise ImagingError("image must be a square 2-D array")
    angles = np.asarray(angles_deg, dtype=float)
    if angles.ndim != 1 or angles.size < 1:
        raise ImagingError("angles must be a 1-D array of at least one angle")
    n = img.shape[0]
    center = (n - 1) / 2.0
    reach = n / 2.0 * math.sqrt(2.0)                # covers the corners
    n_det = int(n_detectors) if n_detectors else n
    n_t = int(n_steps) if n_steps else n
    if n_det < 2 or n_t < 2:
        raise ImagingError("need at least 2 detectors and 2 integration steps")
    s = np.linspace(-reach, reach, n_det)
    t = np.linspace(-reach, reach, n_t)
    dt = (2.0 * reach) / (n_t - 1)
    S, T = np.meshgrid(s, t, indexing="ij")         # (n_det, n_t)
    sino = np.zeros((angles.size, n_det), dtype=float)
    for k, ang in enumerate(np.radians(angles)):
        cos, sin = math.cos(ang), math.sin(ang)
        x = center + S * cos - T * sin
        y = center + S * sin + T * cos
        sino[k] = _bilinear(img, x, y).sum(axis=1) * dt
    return sino


# --- filtered back-projection ------------------------------------------

def _ramp_filter(sino: np.ndarray) -> np.ndarray:
    n_det = sino.shape[1]
    ramp = 2.0 * np.abs(np.fft.rfftfreq(n_det))
    out = np.empty_like(sino)
    for k in range(sino.shape[0]):
        out[k] = np.fft.irfft(np.fft.rfft(sino[k]) * ramp, n=n_det)
    return out


def reconstruct(sinogram, angles_deg, *,
                image_size: int | None = None) -> np.ndarray:
    """Filtered back-projection inverse of :func:`forward_project`.

    Ramp-filters each projection and smears it back across the image
    grid. With a full set of angles this recovers the phantom; with a few
    it is the streaky, feature-poor image the limited-angle problem is
    known for.
    """
    sino = np.asarray(sinogram, dtype=float)
    if sino.ndim != 2:
        raise ImagingError("sinogram must be 2-D (n_angles, n_detectors)")
    angles = np.asarray(angles_deg, dtype=float)
    if angles.ndim != 1 or angles.size != sino.shape[0]:
        raise ImagingError("number of angles must match the sinogram rows")
    n_det = sino.shape[1]
    n = int(image_size) if image_size else n_det
    center = (n - 1) / 2.0
    reach = n / 2.0 * math.sqrt(2.0)
    s = np.linspace(-reach, reach, n_det)
    filtered = _ramp_filter(sino)
    coords = np.arange(n, dtype=float) - center
    X, Y = np.meshgrid(coords, coords, indexing="ij")
    recon = np.zeros((n, n), dtype=float)
    for k, ang in enumerate(np.radians(angles)):
        proj = X * math.cos(ang) + Y * math.sin(ang)
        recon += np.interp(proj.ravel(), s, filtered[k],
                           left=0.0, right=0.0).reshape(n, n)
    recon *= math.pi / angles.size
    return recon


# --- error and resolution metrics --------------------------------------

def reconstruction_error(recon, reference) -> float:
    """Scale-invariant reconstruction error: ``1 - correlation``.

    Zero is a perfect match of the reconstructed shape to the phantom;
    larger values mean the reconstruction has lost or smeared the
    structure. Correlation is used so the absolute brightness scale of
    back-projection (which depends on detector spacing) does not confound
    the comparison.
    """
    a = np.asarray(recon, dtype=float).ravel()
    b = np.asarray(reference, dtype=float).ravel()
    if a.size != b.size:
        raise ImagingError("recon and reference must have the same size")
    a = a - a.mean()
    b = b - b.mean()
    denom = math.sqrt(float((a * a).sum()) * float((b * b).sum()))
    if denom == 0.0:
        raise ImagingError("degenerate image; correlation is undefined")
    return 1.0 - float((a * b).sum()) / denom


def psf_width(recon, center: float | None = None) -> float:
    """Radius of gyration of ``|recon|`` about the centre.

    For a reconstructed point source this is a point-spread-function
    width: streaks and blur from too few angles push energy outward and
    raise it, so fewer angles give a broader PSF.
    """
    r = np.abs(np.asarray(recon, dtype=float))
    n = r.shape[0]
    c = (n - 1) / 2.0 if center is None else float(center)
    coords = np.arange(n, dtype=float) - c
    X, Y = np.meshgrid(coords, coords, indexing="ij")
    total = float(r.sum())
    if total <= 0.0:
        raise ImagingError("reconstruction has no positive mass")
    w = r / total
    return float(np.sqrt((w * (X ** 2 + Y ** 2)).sum()))


def error_vs_angles(phantom, angle_counts, *,
                    span_deg: float = 180.0) -> list[dict]:
    """Reconstruction error at each angle count -- error rises as it drops.

    For each count ``k`` the phantom is projected at ``k`` angles evenly
    spread over ``span_deg`` and reconstructed; the error is recorded.
    The sequence quantifies the limited-angle degradation directly.
    """
    img = np.asarray(phantom, dtype=float)
    n = img.shape[0]
    rows: list[dict] = []
    for k in angle_counts:
        k = int(k)
        if k < 1:
            raise ImagingError("angle count must be positive")
        angles = np.linspace(0.0, span_deg, k, endpoint=False)
        sino = forward_project(img, angles)
        recon = reconstruct(sino, angles, image_size=n)
        rows.append({
            "n_angles": k,
            "error": reconstruction_error(recon, img),
            "psf_width": psf_width(recon),
        })
    return rows


# --- the load-bearing refusals -----------------------------------------

def refuse_reconstruction_as_measured(*_a, **_k) -> None:
    """Refuse to read a synthetic reconstruction as an image of a source.

    Filtered back-projection here inverts projections of a phantom this
    module generated. No beam illuminated a sample, no detector recorded a
    count, and no source was imaged. The reconstruction is a
    NUMERICAL_SIMULATION, not a measurement. Always raises.
    """
    raise ImagingError(
        "refused: a filtered back-projection of a SYNTHETIC phantom is a "
        "reconstruction of numbers this module generated, not an image of "
        "a real source. No beam, detector, or sample existed and nothing "
        "was measured; the result is a NUMERICAL_SIMULATION.")


def refuse_fewangle_as_complete(n_angles=None, *_a, **_k) -> None:
    """Refuse to call a few-angle reconstruction a complete 3-D field.

    A handful of coplanar projections is a limited-angle, underdetermined
    problem: the reconstruction is streaky, misses features, and lies in
    the plane of the views. It is not a complete three-dimensional
    emission field. Always raises.
    """
    count = "a few" if n_angles is None else str(n_angles)
    raise ImagingError(
        f"refused: a reconstruction from {count} coplanar angles is "
        "limited-angle and underdetermined -- streaky, feature-poor, and "
        "confined to the plane of the views. It samples one plane at a "
        "few directions and is not a complete three-dimensional field; a "
        "full angular set, and out-of-plane views, would be needed for "
        "that.")


# --- report ------------------------------------------------------------

def imaging_report(size: int = 48) -> dict:
    phantom = two_disk_phantom(size)
    full_angles = np.linspace(0.0, 180.0, 90, endpoint=False)
    few_angles = np.linspace(0.0, 180.0, 6, endpoint=False)
    rec_full = reconstruct(forward_project(phantom, full_angles),
                           full_angles, image_size=size)
    rec_few = reconstruct(forward_project(phantom, few_angles),
                          few_angles, image_size=size)
    point = point_phantom(size)
    psf_full = psf_width(reconstruct(
        forward_project(point, full_angles), full_angles, image_size=size))
    psf_few = psf_width(reconstruct(
        forward_project(point, few_angles), few_angles, image_size=size))
    return {
        "what_this_is": (
            "a Radon forward projection and filtered back-projection "
            "reconstruction model for a synthetic emission field, with a "
            "full-angle recovery check and a limited-angle degradation "
            "analysis tied to the six-angle ring"),
        "image_size": size,
        "n_full_angles": int(full_angles.size),
        "n_few_angles": int(few_angles.size),
        "full_angle_error": reconstruction_error(rec_full, phantom),
        "few_angle_error": reconstruction_error(rec_few, phantom),
        "psf_width_full_angle": psf_full,
        "psf_width_few_angle": psf_few,
        "few_angle_is_worse": bool(
            reconstruction_error(rec_few, phantom)
            > reconstruction_error(rec_full, phantom)),
        "psf_broadens_with_fewer_angles": bool(psf_few > psf_full),
        "refusals": [
            "refuse_reconstruction_as_measured",
            "refuse_fewangle_as_complete",
        ],
        "claim_class": CLAIM_CLASS,
        "measured_here": "nothing",
        "physical_validation": PHYSICAL_VALIDATION,
        "what_this_does_not_say": (
            "It does not say any reconstruction here is an image of a real "
            "source. Every phantom is synthetic, no beam or detector "
            "exists, and a filtered back-projection of generated numbers "
            "is a NUMERICAL_SIMULATION, not a measurement. It does not say "
            "a six-angle reconstruction is complete: few coplanar views "
            "are limited-angle and underdetermined, so the image is "
            "streaky, loses features, and stays in the plane of the "
            "views. The full-angle round trip recovering the phantom is a "
            "correctness check on the transform pair, not evidence about "
            "any physical emitter."),
        "verdict": VERDICT,
    }
