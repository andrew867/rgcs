"""P39 -- CW URI, clipboard/share string, and optional QR.

A stable, shareable, tracker-free form for a CW vector:

    cw://<namespace>/<codec>/<vector>?frame=<crs>&epoch=<epoch>

The vector component is percent-encoded so a CW-GEO-1 payload (which uses ``;``
and ``=``) survives a round trip. The frame (CRS) and epoch are carried as
query parameters, so a shared link never drops the receipt a map pin needs
(System Contract invariant 9). :func:`format_cw_uri` / :func:`parse_cw_uri`
round-trip exactly.

The load-bearing privacy invariant (claim/privacy boundary): **personal data
never goes in a URL.** Every share string is scanned with
:func:`cwatlas.privacy.refuse_private_in_public` before it is emitted, and a URI
carrying a private token is a typed refusal.

QR is *optional*: :func:`make_qr` emits a QR only if the third-party ``qrcode``
package imports; otherwise it returns an unavailable result with the URI string
and a note, and never adds a hard dependency. No analytics, no shortener, no
tracking parameter is ever added.

    SOURCE_VECTOR_GEOGRAPHIC_SEMANTICS_NOT_CLAIMED
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from urllib.parse import quote, unquote, urlsplit, parse_qsl

from cwatlas import claims, privacy

MODULE_PHASE = "P39"

URI_SCHEME = "cw"

#: Characters safe to leave un-escaped inside the vector path segment. Notably
#: ``;`` and ``=`` are NOT in this set, so a CW-GEO-1 payload is fully escaped.
_VECTOR_SAFE = "-_.~"


class ShareError(ValueError):
    """Raised on a malformed share string or a privacy violation."""


@dataclass(frozen=True)
class CwUri:
    """The typed content of a CW URI (all label/receipt metadata, no secrets)."""

    namespace: str
    codec: str
    vector: str
    frame: str
    epoch: str

    def __post_init__(self) -> None:
        for name, value in (
            ("namespace", self.namespace), ("codec", self.codec),
            ("vector", self.vector), ("frame", self.frame),
            ("epoch", self.epoch),
        ):
            if not isinstance(value, str) or not value:
                raise ShareError(f"{name} must be a non-empty string")
        # Invariant 9: a shareable pin carries its CRS (frame) and epoch.
        claims.refuse_pin_without_crs_epoch(crs=self.frame, epoch=self.epoch)


def _assert_no_private(*fields: str) -> None:
    """Refuse if any field (or the whole thing) carries a private token."""
    for f in fields:
        privacy.refuse_private_in_public(f)


def format_cw_uri(uri: CwUri) -> str:
    """Format a :class:`CwUri` to its canonical string form.

    The vector is percent-encoded; the frame and epoch are query parameters.
    The final string is privacy-scanned before it is returned.
    """
    _assert_no_private(uri.namespace, uri.codec, uri.vector, uri.frame,
                       uri.epoch)
    ns = quote(uri.namespace, safe=_VECTOR_SAFE)
    codec = quote(uri.codec, safe=_VECTOR_SAFE)
    vec = quote(uri.vector, safe=_VECTOR_SAFE)
    frame = quote(uri.frame, safe=_VECTOR_SAFE)
    epoch = quote(uri.epoch, safe=_VECTOR_SAFE)
    out = f"{URI_SCHEME}://{ns}/{codec}/{vec}?frame={frame}&epoch={epoch}"
    # Defence in depth: scan the assembled URI, not just its parts.
    privacy.refuse_private_in_public(out)
    return out


def parse_cw_uri(text: str) -> CwUri:
    """Parse a ``cw://`` URI back into a :class:`CwUri`.

    Refuses a wrong scheme, a missing namespace/codec/vector path, a missing
    ``frame`` or ``epoch`` query parameter, or any private token.
    """
    if not isinstance(text, str) or not text:
        raise ShareError("share URI must be a non-empty string")
    privacy.refuse_private_in_public(text)
    parts = urlsplit(text)
    if parts.scheme != URI_SCHEME:
        raise ShareError(
            f"share URI scheme must be {URI_SCHEME!r}, got {parts.scheme!r}")
    namespace = parts.netloc
    if not namespace:
        raise ShareError("share URI missing the <namespace> authority")
    path_segments = [s for s in parts.path.split("/") if s != ""]
    if len(path_segments) != 2:
        raise ShareError(
            "share URI path must be '/<codec>/<vector>' (two segments)")
    codec, vector = unquote(path_segments[0]), unquote(path_segments[1])
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    frame = query.get("frame", "")
    epoch = query.get("epoch", "")
    if not frame or not epoch:
        raise ShareError(
            "share URI must carry both frame and epoch query parameters "
            "(a shared pin needs its CRS and epoch)")
    ns, frame, epoch = unquote(namespace), unquote(frame), unquote(epoch)
    # Scan the DECODED components too: a private token could otherwise be
    # smuggled percent-encoded past the raw-text scan above.
    _assert_no_private(ns, codec, vector, frame, epoch)
    return CwUri(namespace=ns, codec=codec, vector=vector,
                 frame=frame, epoch=epoch)


def to_clipboard_string(uri: CwUri, *, note: Optional[str] = None) -> str:
    """A human-readable share block: the URI plus a CRS/epoch line and a note.

    Deterministic and tracker-free. Privacy-scanned before return.
    """
    uri_text = format_cw_uri(uri)
    lines = [
        uri_text,
        f"codec={uri.codec} frame={uri.frame} epoch={uri.epoch}",
        "note: a CW vector is a coordinate re-expression, not a decoded place.",
    ]
    if note is not None:
        privacy.refuse_private_in_public(note)
        lines.append(f"note: {note}")
    block = "\n".join(lines)
    privacy.refuse_private_in_public(block)
    return block


@dataclass(frozen=True)
class QrResult:
    """The outcome of a QR request: available or not, always with the URI.

    ``payload`` holds an ASCII/text rendering of the QR when the optional
    ``qrcode`` package is present; otherwise it is ``None`` and ``note`` says
    QR is unavailable. The URI is always present so sharing never blocks on QR.
    """

    available: bool
    uri: str
    note: str
    payload: Optional[str] = None


def make_qr(uri: CwUri) -> QrResult:
    """Emit a QR for the CW URI iff the optional ``qrcode`` package imports.

    Never a hard dependency: an ImportError (or any qrcode failure) degrades to
    an ``available=False`` result carrying the URI string and a note. The URI is
    privacy-scanned first, so a private token is refused before any QR attempt.
    """
    uri_text = format_cw_uri(uri)  # privacy-scans the URI
    try:
        import qrcode  # type: ignore
    except Exception:  # pragma: no cover - exercised only when absent
        return QrResult(
            available=False, uri=uri_text,
            note="QR_UNAVAILABLE: optional 'qrcode' package not installed; "
                 "use the URI string.")
    try:
        qr = qrcode.QRCode(border=1)
        qr.add_data(uri_text)
        qr.make(fit=True)
        buf = []
        qr.print_ascii(out=_ListWriter(buf))
        payload = "".join(buf)
        return QrResult(available=True, uri=uri_text,
                        note="QR generated via optional 'qrcode' package.",
                        payload=payload)
    except Exception as exc:  # pragma: no cover - defensive
        return QrResult(
            available=False, uri=uri_text,
            note=f"QR_UNAVAILABLE: qrcode present but failed ({exc}); "
                 f"use the URI string.")


class _ListWriter:
    """Minimal file-like sink so ``qrcode.print_ascii`` can render to a list."""

    def __init__(self, sink: list) -> None:
        self._sink = sink

    def write(self, s) -> None:
        self._sink.append(s)


def share_report() -> dict:
    """Governance report: what this module is and, emphatically, is not."""
    try:
        import qrcode  # type: ignore  # noqa: F401
        qr_available = True
    except Exception:
        qr_available = False
    return {
        "module": "cwatlas.share",
        "phase_id": MODULE_PHASE,
        "uri_scheme": URI_SCHEME,
        "uri_form": "cw://<namespace>/<codec>/<vector>?frame=..&epoch=..",
        "crs_epoch_carried": True,
        "qr_optional": True,
        "qr_available": qr_available,
        "tracking_parameters": "NONE",
        "invariant": "PERSONAL_DATA_NEVER_IN_A_URL",
        "claim_class": claims.ClaimClass.MATHEMATICAL_TRANSLATION.value,
        "level": "SOFTWARE",
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "source_vector_geographic_semantics": "NOT_CLAIMED",
        "verdict": "CW_ATLAS_SHARE_URI_ROUND_TRIP_NO_PRIVATE_NO_TRACKING",
        "what_this_does_not_say": (
            "A cw:// URI is a portable label for a coordinate re-expression "
            "carrying its CRS and epoch. It embeds no personal data, adds no "
            "tracker, and decodes no source vector to a real location."),
    }
