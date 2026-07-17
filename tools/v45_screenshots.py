"""Deterministic offscreen screenshots of the RGCS Workbench (v4.5, P04).

Constructs the real MainWindow under the Qt 'offscreen' platform and
grabs the whole window plus each panel tab to PNG. No display server,
no user interaction, safe in CI. Writes to release/v45/screenshots/.

    python tools/v45_screenshots.py [out_dir]
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def capture(out_dir: Path) -> list[Path]:
    from rgcs_desktop.app.main import create_app
    create_app()
    from rgcs_desktop.app.context import AppContext
    from rgcs_desktop.app.main_window import MainWindow

    out_dir.mkdir(parents=True, exist_ok=True)
    window = MainWindow(AppContext())
    window.resize(1440, 900)
    window.show()
    written: list[Path] = []

    def _grab(widget, name: str) -> None:
        widget.repaint()
        pix = widget.grab()
        p = out_dir / name
        if pix.save(str(p)):
            written.append(p)

    _grab(window, "00_workbench_main.png")
    # each panel tab, selected in turn
    for i, title in enumerate(window.panels, start=1):
        try:
            window.show_panel(title) if hasattr(window, "show_panel") \
                else None
        except Exception:  # noqa: BLE001
            pass
        panel = window.panels[title]
        slug = "".join(c if c.isalnum() else "_"
                       for c in title.lower())[:40]
        _grab(panel, f"{i:02d}_{slug}.png")
    window.close()
    return written


def main() -> int:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else \
        ROOT / "release" / "v45" / "screenshots"
    shots = capture(out)
    print(f"wrote {len(shots)} screenshots to {out}")
    for p in shots:
        print(f"  {p.name}  ({p.stat().st_size} bytes)")
    return 0 if shots else 1


if __name__ == "__main__":
    raise SystemExit(main())
