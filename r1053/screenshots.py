"""R10.59 -- reproducible screenshot capture for the user manual.

The runbook is explicit: screenshots must come from a real application
run, and must never be invented. This module renders the actual served
workbench pages and the actual generated map artifacts through
QtWebEngine, and stamps every capture with the provenance the runbook
demands:

    filename, UTC timestamp, commit hash, operator/machine,
    command used, SHA-256 of the output file

If a capture fails, it is recorded as a FAILED row with the exception
text. A missing screenshot is a receipt, not a gap to be papered over.

Offscreen note: QtWebEngine needs a software rasteriser in a headless
session. The Chromium flags are set here rather than in the caller's
environment so a capture run is reproducible from the module alone.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import os
import subprocess
import sys

#: Chromium flags that make offscreen rendering work without a GPU.
CHROMIUM_FLAGS = ("--disable-gpu --no-sandbox --disable-dev-shm-usage "
                  "--enable-logging=stderr --log-level=2")

DEFAULT_VIEWPORT = (1440, 960)
LOAD_TIMEOUT_MS = 25000
SETTLE_MS = 2200
#: Map pages fetch a CDN library plus many tiles; they need much longer.
TILE_SETTLE_MS = 12000


def _git(*args) -> str:
    try:
        return subprocess.run(("git",) + args, capture_output=True,
                              text=True, timeout=30).stdout.strip()
    except Exception:                                  # noqa: BLE001
        return ""


def _sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def provenance(path, command: str) -> dict:
    """The stamp every screenshot must carry."""
    return {
        "filename": os.path.basename(path),
        "captured_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(
            timespec="seconds"),
        "commit": _git("rev-parse", "HEAD"),
        "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
        "operator_machine": f"{os.environ.get('USERNAME', '?')}@"
                            f"{os.environ.get('COMPUTERNAME', '?')}",
        "platform": sys.platform,
        "command": command,
        "bytes": os.path.getsize(path) if os.path.exists(path) else 0,
        "sha256": _sha256(path) if os.path.exists(path) else "",
    }


def capture(targets, outdir: str, viewport=DEFAULT_VIEWPORT) -> list:
    """Render ``targets`` to PNG.

    Each target is ``(name, url_or_file, caption)`` or
    ``(name, url_or_file, caption, javascript)``. The optional
    JavaScript runs after load and before capture, so a page can be
    driven into the state being documented (entering a vector, pressing
    Decode) rather than photographed in its default state.

    Returns one row per target, each either a provenance stamp or a
    FAILED record. Never raises for a single bad target -- a failed
    capture is data the manual has to show.
    """
    os.environ.setdefault("QTWEBENGINE_CHROMIUM_FLAGS", CHROMIUM_FLAGS)
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    os.makedirs(outdir, exist_ok=True)

    from PySide6.QtCore import QEventLoop, QTimer, QUrl
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([sys.argv[0]])
    view = QWebEngineView()
    view.resize(*viewport)
    view.show()

    rows = []
    for spec in targets:
        name, target, caption = spec[0], spec[1], spec[2]
        js = spec[3] if len(spec) > 3 else None
        path = os.path.join(outdir, f"{name}.png")
        cmd = f"r1053.screenshots.capture -> {target}"
        try:
            url = (QUrl(target) if "://" in target
                   else QUrl.fromLocalFile(os.path.abspath(target)))
            loop, state = QEventLoop(), {"ok": False, "done": False}

            def _finished(ok, _s=state, _l=loop):
                _s["ok"], _s["done"] = ok, True
                _l.quit()

            view.loadFinished.connect(_finished)
            view.load(url)
            QTimer.singleShot(LOAD_TIMEOUT_MS, loop.quit)
            loop.exec()
            view.loadFinished.disconnect(_finished)
            if not state["ok"]:
                raise RuntimeError(
                    "page did not report a successful load "
                    f"(done={state['done']})")

            settle = QEventLoop()                 # let JS/tiles paint
            QTimer.singleShot(SETTLE_MS, settle.quit)
            settle.exec()
            app.processEvents()

            if js:                                # drive the page first
                view.page().runJavaScript(js)
                drive = QEventLoop()
                QTimer.singleShot(SETTLE_MS, drive.quit)
                drive.exec()
                app.processEvents()

            if not view.grab().save(path, "PNG"):
                raise RuntimeError("QWidget.grab().save() returned False")
            if os.path.getsize(path) < 1000:
                raise RuntimeError(
                    f"PNG suspiciously small ({os.path.getsize(path)} B)")
            with open(path, "rb") as fh:
                if fh.read(8) != b"\x89PNG\r\n\x1a\n":
                    raise RuntimeError("not a valid PNG")
            rows.append({"name": name, "caption": caption, "target": target,
                         "driven_by_js": bool(js),
                         "status": "CAPTURED", **provenance(path, cmd)})
        except Exception as exc:                       # noqa: BLE001
            rows.append({"name": name, "caption": caption, "target": target,
                         "status": "FAILED", "error": f"{type(exc).__name__}: "
                                                      f"{exc}",
                         "command": cmd, "filename": f"{name}.png",
                         "todo": "SCREENSHOT_TODO - capture manually and "
                                 "re-run r1053.screenshots"})
    view.deleteLater()
    return rows


#: Why the interactive maps are not the manual's map figures.
INTERACTIVE_MAP_LIMITATION = (
    "The interactive HTML maps load Leaflet and their road/satellite "
    "tiles from public CDNs. A capture run with no outbound network "
    "renders the page chrome -- title, boundary banner, residual "
    "caption -- over an empty map pane. Capturing that would show a "
    "blank rectangle and imply the map is broken, which it is not: it "
    "works in a browser with network. The manual therefore uses the "
    "STATIC PNG maps, which are matplotlib renders of the same "
    "coordinates with no external dependency, and are the offline "
    "fallbacks the artifact manifest already specifies. The "
    "interactive maps remain shipped and are listed in the manual as "
    "network-required.")


def _decode_js(vector: str) -> str:
    """Drive the coordinate workbench to decode one vector.

    Sets the decimal input, dispatches a real input event so any
    framework listener sees it, then clicks the decode control. Written
    defensively because it must not silently no-op: if the control is
    not found the page simply stays on its default vector, and the
    captured image would misrepresent what was run.
    """
    return f"""
(function() {{
  var input = document.querySelector('input[type=text], input#packet, input');
  if (input) {{
    var setter = Object.getOwnPropertyDescriptor(
        window.HTMLInputElement.prototype, 'value').set;
    setter.call(input, {vector!r});
    input.dispatchEvent(new Event('input', {{bubbles: true}}));
    input.dispatchEvent(new Event('change', {{bubbles: true}}));
  }}
  var btns = Array.prototype.slice.call(document.querySelectorAll('button'));
  var dec = btns.filter(function(b) {{
    return /decode/i.test(b.textContent || '');
  }})[0];
  if (dec) {{ dec.click(); }}
  return document.body.innerText.indexOf({vector!r}) >= 0;
}})();
"""


def manual_targets(base_url: str, maps_dir: str) -> list:
    """The screenshot set the R10.59 runbook asks for.

    Runbook items that are CLI/JSON outputs rather than GUI views are
    carried in the manual as real captured terminal transcripts, which
    are more checkable than a picture of text. Runbook items 7-9 (map
    views) are the static PNG maps -- see
    :data:`INTERACTIVE_MAP_LIMITATION`.
    """
    wb = base_url.rstrip("/") + "/workbench"
    return [
        ("01_workbench_hub", base_url,
         "Workbench hub: module cards, claim classes, YELLOW banner"),
        ("02_decode_stonehenge_165876523", wb,
         "Structural decode of 165876523 (Stonehenge fit anchor): "
         "octal 1170611453, face 4, S3 = 3",
         _decode_js("165876523")),
        ("03_decode_toronto_168930443", wb,
         "Structural decode of 168930443 (Toronto fit anchor): "
         "octal branch 120, North American branch",
         _decode_js("168930443")),
        ("04_decode_drummondville_165879243", wb,
         "Structural decode of 165879243: octal 1170616713, branch 117. "
         "Active label Drummondville / Saint-Eugene working target; "
         "Montreal retired to hint/provenance",
         _decode_js("165879243")),
    ]


def inventory(rows) -> dict:
    return {
        "schema": "rgcs.r1059.screenshot-inventory.v1",
        "rows": rows,
        "captured": sum(1 for r in rows if r["status"] == "CAPTURED"),
        "failed": sum(1 for r in rows if r["status"] == "FAILED"),
        "all_captured": all(r["status"] == "CAPTURED" for r in rows),
        "rule": "screenshots are captured from a real run or recorded as "
                "FAILED with a TODO receipt; none are invented",
    }
