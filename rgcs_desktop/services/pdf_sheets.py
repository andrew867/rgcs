"""PDF sheet rendering — self-contained pure-Python PDF writer.

No third-party dependency and no Qt: sheets use the PDF core Helvetica
fonts (no embedding required), so output is deterministic, works fully
headless on every platform, and text extracts cleanly (pypdf-checkable
in tests).

Layouts follow the plan pack ``15_TEMPLATES/PDF_LAYOUTS.md``: header,
content sections, claim boundary, then hashes/version/date footer.
Rules: no NaN may reach a sheet; unavailable values are written as
"unavailable", never zero.
"""
from __future__ import annotations

import datetime as _dt
import math
import zlib
from pathlib import Path
from typing import Any

from rgcs_core.provenance import sha256_of_jsonable

import rgcs_desktop

# page geometry (points), A4
_PAGE_W, _PAGE_H = 595.0, 842.0
_MARGIN = 50.0
_BODY_W = _PAGE_W - 2 * _MARGIN
_LINE = 12.0          # body line height (9 pt text)
_CHAR_W = 4.6         # ~average Helvetica 9pt char width, for wrapping


def fmt(value: Any, unit: str = "") -> str:
    """Sheet-safe scalar formatting: None/NaN become 'unavailable'."""
    if value is None:
        return "unavailable"
    if isinstance(value, float) and not math.isfinite(value):
        return "unavailable"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, float):
        text = f"{value:.6g}"
    else:
        text = str(value)
    return f"{text} {unit}".strip()


# ---------------------------------------------------------------- blocks

def paragraph(text: str) -> dict:
    return {"kind": "para", "text": str(text)}


def rows_block(rows: list[tuple[str, Any]]) -> dict:
    return {"kind": "rows",
            "rows": [(str(k), fmt(v)) for k, v in rows]}


def table_block(headers: list[str], rows: list[list[Any]]) -> dict:
    return {"kind": "table", "headers": [str(h) for h in headers],
            "rows": [[fmt(v) for v in row] for row in rows]}


# ------------------------------------------------------------ pdf writer

def _esc(text: str) -> bytes:
    data = text.encode("cp1252", errors="replace")
    return (data.replace(b"\\", b"\\\\")
                .replace(b"(", b"\\(")
                .replace(b")", b"\\)"))


def _wrap(text: str, width_pt: float) -> list[str]:
    max_chars = max(8, int(width_pt / _CHAR_W))
    words = str(text).split()
    if not words:
        return [""]
    lines, cur = [], words[0]
    for word in words[1:]:
        if len(cur) + 1 + len(word) <= max_chars:
            cur += " " + word
        else:
            lines.append(cur)
            cur = word
    lines.append(cur)
    return lines


class _SheetWriter:
    """Accumulates text operations across pages, then serializes a
    complete PDF (fonts F1=Helvetica, F2=Helvetica-Bold)."""

    def __init__(self) -> None:
        self.pages: list[list[bytes]] = []
        self._new_page()

    def _new_page(self) -> None:
        self.pages.append([])
        self.y = _PAGE_H - _MARGIN

    def _need(self, height: float) -> None:
        if self.y - height < _MARGIN:
            self._new_page()

    def _text(self, x: float, size: float, text: str,
              bold: bool = False) -> None:
        font = b"/F2" if bold else b"/F1"
        self.pages[-1].append(
            b"BT " + font + b" %.1f Tf %.1f %.1f Td (" % (size, x, self.y)
            + _esc(text) + b") Tj ET\n")

    def _rule(self) -> None:
        self.pages[-1].append(
            b"0.6 0.6 0.6 RG 0.5 w %.1f %.1f m %.1f %.1f l S\n"
            % (_MARGIN, self.y + 3, _PAGE_W - _MARGIN, self.y + 3))

    def line(self, text: str, size: float = 9.0, bold: bool = False,
             x: float = _MARGIN, wrap_width: float = _BODY_W) -> None:
        for part in _wrap(text, wrap_width):
            self._need(_LINE)
            self.y -= _LINE
            self._text(x, size, part, bold)

    def heading(self, text: str) -> None:
        self._need(2.6 * _LINE)
        self.y -= 1.6 * _LINE
        self._text(_MARGIN, 11.0, text, bold=True)
        self._rule()
        self.y -= 0.4 * _LINE

    def kv_rows(self, rows: list[tuple[str, str]]) -> None:
        key_w = 180.0
        for key, value in rows:
            lines = _wrap(value, _BODY_W - key_w)
            self._need(_LINE * len(lines))
            self.y -= _LINE
            self._text(_MARGIN, 9.0, key)
            self._text(_MARGIN + key_w, 9.0, lines[0])
            for extra in lines[1:]:
                self._need(_LINE)
                self.y -= _LINE
                self._text(_MARGIN + key_w, 9.0, extra)

    def table(self, headers: list[str], rows: list[list[str]]) -> None:
        n = max(1, len(headers))
        col_w = _BODY_W / n
        self._need(_LINE)
        self.y -= _LINE
        for i, h in enumerate(headers):
            self._text(_MARGIN + i * col_w, 9.0, h, bold=True)
        self._rule()
        for row in rows:
            wrapped = [_wrap(c, col_w - 6) for c in row]
            height = max(len(w) for w in wrapped) if wrapped else 1
            self._need(_LINE * height)
            top = self.y
            for i, cell_lines in enumerate(wrapped):
                self.y = top
                for part in cell_lines:
                    self.y -= _LINE
                    self._text(_MARGIN + i * col_w, 9.0, part)
            self.y = top - _LINE * height

    def serialize(self) -> bytes:
        objs: list[bytes] = []          # 1-indexed PDF objects
        n_pages = len(self.pages)
        # 1: catalog, 2: pages, 3: F1, 4: F2, then per page: page, stream
        kids = " ".join(f"{5 + 2 * i} 0 R" for i in range(n_pages))
        objs.append(b"<< /Type /Catalog /Pages 2 0 R >>")
        objs.append((f"<< /Type /Pages /Count {n_pages} "
                     f"/Kids [{kids}] >>").encode())
        objs.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica"
                    b" /Encoding /WinAnsiEncoding >>")
        objs.append(b"<< /Type /Font /Subtype /Type1 "
                    b"/BaseFont /Helvetica-Bold"
                    b" /Encoding /WinAnsiEncoding >>")
        for i, ops in enumerate(self.pages):
            stream = zlib.compress(b"".join(ops))
            objs.append((
                f"<< /Type /Page /Parent 2 0 R "
                f"/MediaBox [0 0 {_PAGE_W:g} {_PAGE_H:g}] "
                f"/Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> "
                f"/Contents {6 + 2 * i} 0 R >>").encode())
            objs.append(b"<< /Length %d /Filter /FlateDecode >>\nstream\n"
                        % len(stream) + stream + b"\nendstream")
        out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = [0]
        for i, body in enumerate(objs, start=1):
            offsets.append(len(out))
            out += b"%d 0 obj\n" % i + body + b"\nendobj\n"
        xref_at = len(out)
        out += b"xref\n0 %d\n" % (len(objs) + 1)
        out += b"0000000000 65535 f \n"
        for off in offsets[1:]:
            out += b"%010d 00000 n \n" % off
        out += (b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n"
                b"%%%%EOF\n" % (len(objs) + 1, xref_at))
        return bytes(out)


# ------------------------------------------------------------- rendering

def render_sheet_pdf(title: str, subtitle: str,
                     sections: list[tuple[str, dict | list[dict]]],
                     boundary: str, out_path: Path,
                     *, input_hash: str | None = None) -> Path:
    """Render a sheet PDF. Each section is (heading, block) or
    (heading, [blocks]) built with :func:`paragraph`,
    :func:`rows_block`, :func:`table_block`. The claim boundary and the
    version/hash/date footer are always appended."""
    w = _SheetWriter()
    w.line(title, size=15.0, bold=True)
    w.line(subtitle, size=10.0)
    for heading, blocks in sections:
        w.heading(heading)
        if isinstance(blocks, dict):
            blocks = [blocks]
        for block in blocks:
            if block["kind"] == "para":
                w.line(block["text"])
            elif block["kind"] == "rows":
                w.kv_rows(block["rows"])
            elif block["kind"] == "table":
                w.table(block["headers"], block["rows"])
            else:  # pragma: no cover - authoring error
                raise ValueError(f"unknown block kind {block['kind']!r}")
    w.heading("Claim boundary")
    w.line(boundary)
    now = _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")
    footer = f"rgcs_desktop {rgcs_desktop.__version__} - generated {now}"
    if input_hash:
        footer += f" - input sha256 {input_hash}"
    w.y -= 0.5 * _LINE
    w.line(footer, size=7.5)

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(w.serialize())
    if out_path.stat().st_size == 0:  # pragma: no cover
        raise RuntimeError(f"PDF rendering produced no output: {out_path}")
    return out_path


def sheet_input_hash(payload: dict) -> str:
    return sha256_of_jsonable(payload)
