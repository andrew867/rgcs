"""Serialized resonator certificates (Agent R07; coverage R049-R056).

A certificate binds: design, material, fixture, every sweep, the full
trim history, fitted values with uncertainty, the acceptance decision
against the preregistered band, and the ledger hash-chain head — into
one canonical JSON document with a SHA-256 content hash and an HMAC
signature. Certificates supersede, never overwrite. A synthetic
certificate says SYNTHETIC in the document, the hash preimage, and the
rendered text, so the flag cannot be dropped in transit."""

from __future__ import annotations

import hashlib
import hmac
import json


class CertificateError(RuntimeError):
    pass


SCHEMA = "rgcs.resonator.certificate/1"


def issue(specimen_id: str, design: dict, fixture: dict,
          frequency: dict, trim_history: list, ledger_head: str,
          acceptance_band_hz: tuple, signing_key: bytes,
          synthetic: bool, supersedes: str | None = None) -> dict:
    """Issue a certificate. Refuses if:
    - the frequency record has no fitted value (a prediction cannot
      be certified);
    - accepted_hz is set but lies outside the preregistered band
      (an acceptance that contradicts its own band is a fraud);
    - synthetic is not explicitly passed (no default: the caller must
      state what this is)."""
    if frequency.get("fitted_hz") is None:
        raise CertificateError("cannot certify without a fitted "
                               "frequency")
    lo, hi = acceptance_band_hz
    acc = frequency.get("accepted_hz")
    if acc is not None and not (lo <= acc <= hi):
        raise CertificateError(
            f"accepted {acc} Hz outside the preregistered band "
            f"[{lo}, {hi}] — refusing to issue")
    body = {
        "schema": SCHEMA,
        "synthetic": bool(synthetic),
        "banner": ("SYNTHETIC CERTIFICATE — no physical resonator "
                   "exists; produced by the digital twin"
                   if synthetic else "PHYSICAL"),
        "specimen_id": specimen_id,
        "design": design,
        "fixture": fixture,
        "frequency": frequency,
        "acceptance_band_hz": [lo, hi],
        "trim_history": trim_history,
        "ledger_head": ledger_head,
        "supersedes": supersedes,
        "claims": {
            "made": ["frequency and Q as fitted, with uncertainty",
                     "trim history as recorded"],
            "not_made": ["therapeutic effect", "consciousness effect",
                         "anomalous field", "healing", "energy"],
        },
    }
    canonical = json.dumps(body, sort_keys=True,
                           separators=(",", ":"))
    content_hash = hashlib.sha256(canonical.encode()).hexdigest()
    sig = hmac.new(signing_key, content_hash.encode(),
                   hashlib.sha256).hexdigest()
    return {**body, "content_hash": content_hash, "hmac": sig}


def verify(cert: dict, signing_key: bytes) -> dict:
    """Recompute hash + HMAC. Any field change breaks both."""
    body = {k: v for k, v in cert.items()
            if k not in ("content_hash", "hmac")}
    canonical = json.dumps(body, sort_keys=True,
                           separators=(",", ":"))
    h = hashlib.sha256(canonical.encode()).hexdigest()
    ok_hash = h == cert.get("content_hash")
    ok_sig = hmac.compare_digest(
        hmac.new(signing_key, h.encode(), hashlib.sha256).hexdigest(),
        cert.get("hmac", ""))
    return {"hash_valid": ok_hash, "signature_valid": ok_sig,
            "valid": ok_hash and ok_sig,
            "synthetic": cert.get("synthetic")}


def supersede(old_cert: dict, **changes) -> dict:
    """Start a superseding certificate body: the old one is never
    edited; the new one names it. (The caller re-issues via issue().)"""
    if "content_hash" not in old_cert:
        raise CertificateError("cannot supersede an unissued draft")
    return {"supersedes": old_cert["content_hash"], **changes}


def compact_payload(cert: dict) -> str:
    """QR-compatible compact verification payload: id, fitted f, band,
    hash prefix, and the synthetic flag — the flag travels with even
    the shortest representation."""
    f = cert["frequency"]
    return "|".join([
        "RGCSRES1",
        cert["specimen_id"],
        f"{f['fitted_hz']:.3f}Hz",
        f"band={cert['acceptance_band_hz'][0]:.1f}-"
        f"{cert['acceptance_band_hz'][1]:.1f}",
        "SYNTHETIC" if cert["synthetic"] else "PHYSICAL",
        cert["content_hash"][:16],
    ])


def render_text(cert: dict) -> str:
    """Human-readable rendering; the banner is the first line."""
    f = cert["frequency"]
    lines = [
        cert["banner"],
        f"Resonator certificate {cert['specimen_id']}",
        f"  schema        : {cert['schema']}",
        f"  fitted        : {f['fitted_hz']:.3f} Hz "
        f"(u = {f['fitted_uncertainty_hz']:.3f} Hz)",
        f"  accepted      : {f['accepted_hz']}",
        f"  band          : {cert['acceptance_band_hz']}",
        f"  trims         : {len(cert['trim_history'])}",
        f"  ledger head   : {cert['ledger_head'][:16]}...",
        f"  content hash  : {cert['content_hash'][:16]}...",
        "  claims not made: " + ", ".join(
            cert["claims"]["not_made"]),
    ]
    return "\n".join(lines) + "\n"
