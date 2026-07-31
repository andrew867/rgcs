"""R10.61 -- FITS inspection and canonical stream recipes.

A FITS file's bytes are an ARCHIVE ENCODING. They are not automatically
the spacecraft's transmitted bitstream, and for Vela 5B they are
certainly not: the public archive is the All Sky Monitor X-ray product,
reduced and re-serialised decades after the fact.

Re-serialising numeric columns therefore creates a DERIVED stream, and
the recipe must be recorded exactly -- columns, rows, scaling, width,
endianness, bit order, missing-data policy -- so that any result can be
traced back to the transformation that produced it.
"""

from __future__ import annotations

import hashlib

import numpy as np

RECIPES = (
    "ARCHIVE_BYTES",
    "DECOMPRESSED_FILE_BYTES",
    "FITS_HDU_RAW_STORAGE",
    "FITS_COLUMN_RAW",
    "FITS_COLUMN_PHYSICAL",
    "TIME_ORDERED_ROWS",
    "COUNT_CHANNEL_STREAM",
    "EVENT_TIME_STREAM",
    "BITPLANE_STREAM",
    "MARK_SPACE_STREAM",
    "FRAME_OR_PACKET_BYTES",
)

#: Interleavings offered for multi-channel detectors. Each is DECLARED,
#: never searched -- searching interleavings is a hypothesis-inflation trap.
INTERLEAVINGS = ("channel_1_only", "channel_2_only", "alternating",
                 "channel_major", "row_major", "difference", "sum")

#: Frozen threshold grid for mark/space. Never widened at analysis time.
MARK_SPACE_GRID = (0.25, 0.5, 0.75)


class StreamError(ValueError):
    """A recipe cannot be applied to this product."""


def inspect_fits(path: str) -> dict:
    """Schema report for every HDU. No semantic assumptions."""
    from astropy.io import fits
    out = []
    with fits.open(path, memmap=False) as hdul:
        for i, hdu in enumerate(hdul):
            row = {"index": i, "name": hdu.name,
                   "type": type(hdu).__name__,
                   "header_cards": len(hdu.header)}
            data = getattr(hdu, "data", None)
            if data is None:
                row["rows"] = 0
                row["columns"] = []
            elif getattr(hdu, "columns", None) is not None:
                row["rows"] = int(len(data))
                row["columns"] = [
                    {"name": c.name, "format": c.format,
                     "unit": getattr(c, "unit", None),
                     "bscale": getattr(c, "bscale", None),
                     "bzero": getattr(c, "bzero", None),
                     "null": getattr(c, "null", None)}
                    for c in hdu.columns]
            else:
                row["rows"] = int(np.size(data))
                row["columns"] = []
                row["image_shape"] = list(np.shape(data))
            for k in ("TELESCOP", "INSTRUME", "OBJECT", "DATE-OBS",
                      "TSTART", "TSTOP", "MJDREF"):
                if k in hdu.header:
                    row[k] = hdu.header[k]
            out.append(row)
    return {"schema": "rgcs.r1061.fits-inspect.v1", "path": path,
            "hdus": out, "hdu_count": len(out)}


def _receipt(name: str, payload: bytes, **meta) -> dict:
    return {
        "schema": "rgcs.r1061.stream.v1",
        "recipe": name,
        "bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        **meta,
    }


def archive_bytes(path: str) -> tuple:
    """Recipe A: the exact downloaded bytes. Reversible by definition."""
    with open(path, "rb") as fh:
        data = fh.read()
    return data, _receipt("ARCHIVE_BYTES", data, source_path=path,
                          lossy=False, inverse="identity")


def fits_column_raw(path: str, hdu: int, column: str,
                    max_rows: int | None = None) -> tuple:
    """Recipe D: raw storage values, before scale/zero, big-endian.

    FITS binary tables are big-endian on disk; that is recorded rather
    than assumed by the reader's platform.
    """
    from astropy.io import fits
    with fits.open(path, memmap=False) as hdul:
        h = hdul[hdu]
        if getattr(h, "columns", None) is None:
            raise StreamError(f"HDU {hdu} is not a binary table")
        if column not in h.columns.names:
            raise StreamError(
                f"column {column!r} not in {h.columns.names}")
        arr = np.asarray(h.data[column])
        if max_rows:
            arr = arr[:max_rows]
        be = arr.astype(arr.dtype.newbyteorder(">"))
        data = be.tobytes()
    return data, _receipt(
        "FITS_COLUMN_RAW", data, source_path=path, hdu=hdu, column=column,
        rows=int(arr.size), dtype=str(arr.dtype), endianness="big",
        bit_order="MSB_first", scaling_applied=False, lossy=False,
        inverse="numpy.frombuffer with the recorded dtype and endianness")


def count_channel_stream(path: str, hdu: int, columns, interleave: str,
                         max_rows: int | None = None) -> tuple:
    """Recipe G: per-channel counts under a DECLARED interleaving."""
    if interleave not in INTERLEAVINGS:
        raise StreamError(f"undeclared interleaving {interleave!r}")
    from astropy.io import fits
    with fits.open(path, memmap=False) as hdul:
        h = hdul[hdu]
        cols = []
        for c in columns:
            if c not in h.columns.names:
                raise StreamError(f"column {c!r} not in {h.columns.names}")
            a = np.asarray(h.data[c], dtype=np.float64)
            cols.append(a[:max_rows] if max_rows else a)
    if interleave == "channel_1_only":
        vals = cols[0]
    elif interleave == "channel_2_only":
        vals = cols[1]
    elif interleave in ("alternating", "row_major"):
        vals = np.column_stack(cols).ravel()
    elif interleave == "channel_major":
        vals = np.concatenate(cols)
    elif interleave == "difference":
        vals = cols[0] - cols[1]
    else:                                            # sum
        vals = cols[0] + cols[1]
    finite = np.isfinite(vals)
    clean = np.where(finite, vals, 0.0)
    q = np.clip(np.rint(clean), 0, 65535).astype(">u2")
    data = q.tobytes()
    return data, _receipt(
        "COUNT_CHANNEL_STREAM", data, source_path=path, hdu=hdu,
        columns=list(columns), interleave=interleave,
        rows=int(vals.size), missing_policy="non-finite -> 0",
        non_finite=int((~finite).sum()),
        serialization="uint16 big-endian, rounded and clipped to 0..65535",
        lossy=True,
        inverse=None,
        lossy_reason="rounding and clipping discard sub-count precision "
                     "and any value above 65535")


def bitplane_stream(data: bytes, width_bits: int, plane: int) -> tuple:
    """Recipe I: one bit plane from fixed-width integers, plane index kept."""
    if width_bits not in (8, 16, 32, 64):
        raise StreamError(f"unsupported width {width_bits}")
    if not 0 <= plane < width_bits:
        raise StreamError(f"plane {plane} outside 0..{width_bits - 1}")
    step = width_bits // 8
    vals = [int.from_bytes(data[i:i + step], "big")
            for i in range(0, len(data) - step + 1, step)]
    bits = "".join("1" if (v >> plane) & 1 else "0" for v in vals)
    out = bits.encode()
    return out, _receipt("BITPLANE_STREAM", out, width_bits=width_bits,
                         plane=plane, symbols=len(bits), lossy=True,
                         inverse=None,
                         lossy_reason="one plane of many; the rest are discarded")


def mark_space_stream(values, threshold_quantile: float) -> tuple:
    """Recipe J: marks and spaces from a FROZEN threshold quantile."""
    if threshold_quantile not in MARK_SPACE_GRID:
        raise StreamError(
            f"threshold {threshold_quantile} is not on the frozen grid "
            f"{MARK_SPACE_GRID}; searching thresholds is not permitted")
    a = np.asarray(values, dtype=np.float64)
    a = a[np.isfinite(a)]
    if a.size == 0:
        raise StreamError("no finite values")
    thr = float(np.quantile(a, threshold_quantile))
    bits = "".join("1" if v > thr else "0" for v in a)
    out = bits.encode()
    return out, _receipt("MARK_SPACE_STREAM", out,
                         threshold_quantile=threshold_quantile,
                         threshold_value=thr, symbols=len(bits),
                         grid=list(MARK_SPACE_GRID), lossy=True,
                         inverse=None,
                         lossy_reason="thresholding discards magnitude")
