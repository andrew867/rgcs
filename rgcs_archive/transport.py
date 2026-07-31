"""R10.61 -- resumable downloads, hashing, and compression handling.

Source artifacts are never mutated. A download lands in a temporary
partial file, is hashed, and is atomically renamed into a
content-addressed cache. Decompression produces a NEW artifact and both
the compressed and decompressed bytes are hashed.

Compression is detected by MAGIC BYTES, not by extension: the Vela 5B
archive uses legacy Unix ``.Z`` (LZW), which is not gzip, and a file
named ``.Z`` that is actually gzip would otherwise be mis-handled.
"""

from __future__ import annotations

import gzip
import hashlib
import os
import time

from rgcs_archive.catalog import (DEFAULT_DELAY_S, DEFAULT_MAX_RETRIES,
                                  DEFAULT_TIMEOUT_S, USER_AGENT,
                                  assert_allowed)

#: Magic bytes -> format name.
MAGIC = (
    (b"\x1f\x9d", "compress_z"),      # legacy Unix compress (.Z)
    (b"\x1f\x8b", "gzip"),
    (b"PK\x03\x04", "zip"),
    (b"BZh", "bzip2"),
    (b"\xfd7zXZ", "xz"),
    (b"SIMPLE  =", "fits"),
)

#: Refuse to expand a bomb.
MAX_DECOMPRESSED_BYTES = 2 * 1024 ** 3


class TransportError(RuntimeError):
    """A download or decompression failed in a way worth stopping for."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def detect_format(data: bytes) -> str:
    """Identify a payload by magic bytes. Extension is never trusted."""
    for magic, name in MAGIC:
        if data.startswith(magic):
            return name
    return "unknown"


def safe_name(name: str) -> str:
    """Strip path separators and traversal from a remote filename."""
    base = os.path.basename(name.replace("\\", "/"))
    base = base.replace("..", "_")
    keep = "-_.()[]"
    cleaned = "".join(c for c in base if c.isalnum() or c in keep)
    return cleaned or "unnamed"


def decompress(data: bytes, fmt: str | None = None) -> dict:
    """Decompress by detected format. Returns bytes plus both hashes."""
    fmt = fmt or detect_format(data)
    if fmt == "compress_z":
        import unlzw3
        out = bytes(unlzw3.unlzw(data))
    elif fmt == "gzip":
        out = gzip.decompress(data)
    elif fmt == "bzip2":
        import bz2
        out = bz2.decompress(data)
    elif fmt == "xz":
        import lzma
        out = lzma.decompress(data)
    else:
        out = data                                   # already plain
    if len(out) > MAX_DECOMPRESSED_BYTES:
        raise TransportError(
            f"decompressed size {len(out)} exceeds the "
            f"{MAX_DECOMPRESSED_BYTES} byte limit")
    return {
        "input_format": fmt,
        "compressed_bytes": len(data),
        "decompressed_bytes": len(out),
        "compressed_sha256": sha256_bytes(data),
        "decompressed_sha256": sha256_bytes(out),
        "ratio": (len(out) / len(data)) if data else 0.0,
        "data": out,
    }


def cache_path(root: str, sha: str, name: str) -> str:
    """Content-addressed location: identical bytes collide, never duplicate."""
    d = os.path.join(root, sha[:2], sha[2:4])
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, f"{sha}-{safe_name(name)}")


def head(url: str, client=None) -> dict:
    """HEAD a URL, falling back to a 1-byte ranged GET if HEAD is refused."""
    u = assert_allowed(url)
    import httpx
    own = client is None
    client = client or httpx.Client(timeout=DEFAULT_TIMEOUT_S,
                                    headers={"User-Agent": USER_AGENT},
                                    follow_redirects=True)
    try:
        r = client.head(u)
        if r.status_code >= 400 or "content-length" not in r.headers:
            r = client.get(u, headers={"Range": "bytes=0-0"})
        size = r.headers.get("content-range", "").split("/")[-1] \
            or r.headers.get("content-length", "")
        return {"url": u, "status": r.status_code,
                "size": int(size) if size.isdigit() else None,
                "content_type": r.headers.get("content-type", ""),
                "last_modified": r.headers.get("last-modified", ""),
                "accepts_ranges": r.headers.get("accept-ranges", "") == "bytes"}
    finally:
        if own:
            client.close()


def download(url: str, dest_dir: str, client=None, quota_bytes: int | None = None,
             delay_s: float = DEFAULT_DELAY_S,
             max_retries: int = DEFAULT_MAX_RETRIES) -> dict:
    """Resumable, hashed, atomic download into a content-addressed cache."""
    u = assert_allowed(url)
    import httpx
    os.makedirs(dest_dir, exist_ok=True)
    name = safe_name(os.path.basename(u))
    part = os.path.join(dest_dir, f".{name}.partial")
    own = client is None
    client = client or httpx.Client(timeout=DEFAULT_TIMEOUT_S,
                                    headers={"User-Agent": USER_AGENT},
                                    follow_redirects=True)
    try:
        for attempt in range(1, max_retries + 1):
            have = os.path.getsize(part) if os.path.exists(part) else 0
            headers = {"Range": f"bytes={have}-"} if have else {}
            try:
                with client.stream("GET", u, headers=headers) as r:
                    if have and r.status_code == 200:
                        have = 0                        # server ignored Range
                        open(part, "wb").close()
                    elif r.status_code not in (200, 206):
                        raise TransportError(f"HTTP {r.status_code} for {u}")
                    total = have
                    with open(part, "ab" if have else "wb") as fh:
                        for chunk in r.iter_bytes(1 << 16):
                            total += len(chunk)
                            if quota_bytes and total > quota_bytes:
                                raise TransportError(
                                    f"quota {quota_bytes} exceeded for {u}")
                            fh.write(chunk)
                break
            except TransportError:
                raise
            except Exception as exc:                   # noqa: BLE001
                if attempt == max_retries:
                    raise TransportError(
                        f"{type(exc).__name__} after {attempt} attempts: {exc}")
                time.sleep(delay_s * (2 ** (attempt - 1)))
        sha = sha256_file(part)
        final = cache_path(dest_dir, sha, name)
        os.replace(part, final)                        # atomic
        with open(final, "rb") as fh:
            magic = fh.read(16)
        time.sleep(delay_s)
        return {
            "schema": "rgcs.r1061.download.v1",
            "url": u, "path": final, "name": name,
            "bytes": os.path.getsize(final),
            "sha256": sha,
            "detected_format": detect_format(magic),
            "source_artifact_mutated": False,
        }
    finally:
        if own:
            client.close()
