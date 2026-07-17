"""Application entry point (``python -m rgcs_desktop``)."""
from __future__ import annotations

import multiprocessing
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication


def create_app(argv: list[str] | None = None) -> QApplication:
    app = QApplication.instance() or QApplication(argv or sys.argv[:1])
    app.setOrganizationName("RGCS")
    app.setApplicationName("rgcs_desktop")
    return app


def _default_workspace() -> Path:
    """Per-user data location (installer contract): the user's
    Documents\\RGCS Workspace. No hardcoded personal path."""
    import os
    docs = os.environ.get("USERPROFILE")
    base = Path(docs) / "Documents" if docs else Path.home()
    return base / "RGCS Workspace"


def doctor() -> int:
    """`--doctor`: offline diagnostics for the Start-Menu shortcut and
    the first-run wizard. No network, no side effects."""
    import platform

    import rgcs_desktop
    lines = [f"RGCS Workbench diagnostics",
             f"  version        : {rgcs_desktop.__version__}",
             f"  python         : {sys.version.split()[0]}",
             f"  platform       : {platform.platform()}",
             f"  default workspace: {_default_workspace()}"]
    ok = True
    for mod in ("PySide6", "numpy", "scipy", "openpyxl"):
        try:
            m = __import__(mod)
            lines.append(f"  {mod:<15}: {getattr(m, '__version__', 'ok')}")
        except ImportError:
            lines.append(f"  {mod:<15}: MISSING")
            if mod != "openpyxl":       # workbook export is optional
                ok = False
    try:
        import rgcs_core.provenance as prov
        lines.append(f"  model version  : {prov.MODEL_VERSION}")
    except Exception as exc:            # noqa: BLE001
        lines.append(f"  model version  : ERROR {exc}")
        ok = False
    lines.append(f"  claim boundary : SOFTWARE only; no physical "
                 "result is validated")
    print("\n".join(lines))
    return 0 if ok else 1


def export_workbook(argv: list[str]) -> int:
    """`--export-workbook <path> [--private]`: regenerate the Master
    Evidence Workbook from canonical data (one-click regeneration)."""
    try:
        from rgcs_workbench.workbook import generate
    except ImportError:
        print("workbook export requires the 'workbook' extra "
              "(openpyxl); install it or use the packaged build",
              file=sys.stderr)
        return 2
    out = next((a for a in argv if a.endswith(".xlsx")),
               str(_default_workspace() /
                   "RGCS_Master_Evidence_Workbook.xlsx"))
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    generate(include_private="--private" in argv).save(out)
    print(f"workbook regenerated: {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    multiprocessing.freeze_support()  # required for frozen (PyInstaller) builds
    argv = argv if argv is not None else sys.argv[1:]

    # headless subcommands (no Qt event loop, safe in the packaged EXE)
    if "--doctor" in argv:
        return doctor()
    if "--export-workbook" in argv:
        return export_workbook(argv)

    app = create_app()

    if "--smoke-check" in argv:
        # packaging smoke check: construct the full window, print versions,
        # exit without entering the event loop
        import rgcs_core.provenance as prov

        import rgcs_desktop
        from rgcs_desktop.app.context import AppContext
        from rgcs_desktop.app.main_window import MainWindow

        context = AppContext()
        window = MainWindow(context)
        window.show()
        n_panels = len(window.panels)
        # frozen-multiprocessing check: a real spawn-based background job
        job_id = context.job_manager.submit("trivial", {"steps": 2},
                                            name="smoke job")
        rec = context.job_manager.wait(job_id, timeout_s=60.0)
        window.close()
        print(f"rgcs_desktop {rgcs_desktop.__version__} "
              f"(rgcs_core model version {prov.MODEL_VERSION}); "
              f"{n_panels} panels constructed OK; "
              f"background job {rec.status.value}")
        return 0 if rec.status.value == "succeeded" else 1

    from rgcs_desktop.app.context import AppContext
    from rgcs_desktop.app.main_window import MainWindow
    from rgcs_desktop.workspaces import Workspace, WorkspaceError

    def _guarded_open(ctx: AppContext, root: Path) -> bool:
        """Open a workspace without letting a corrupt db crash startup
        (QA-D-05). Tries a backup restore; on failure the app starts with
        no workspace instead of crash-looping."""
        try:
            ctx.open_workspace(root)
            return True
        except WorkspaceError as exc:
            print(f"warning: could not open workspace {root}: {exc}",
                  file=sys.stderr)
            try:
                Workspace.restore_latest_backup(root).close()
                ctx.open_workspace(root)
                print(f"restored workspace {root} from its newest intact "
                      f"backup", file=sys.stderr)
                return True
            except WorkspaceError as exc2:
                print(f"warning: backup restore failed for {root}: {exc2}; "
                      f"starting without a workspace", file=sys.stderr)
                ctx.settings.last_workspace = ""
                return False

    context = AppContext()
    # `--first-run` (used by the installer's post-install launch) forces
    # the wizard; it is a flag, never a workspace path.
    force_first_run = "--first-run" in argv
    positional = [a for a in argv if not a.startswith("-")]
    # reopen the last workspace when available
    last = context.settings.last_workspace
    if force_first_run:
        from rgcs_desktop.app.first_run import run_first_run
        run_first_run(context)
    elif positional:
        target = Path(positional[0])
        if (target / "workspace.db").exists():
            _guarded_open(context, target)
        else:
            context.create_workspace(target, target.name)
    elif last and (Path(last) / "workspace.db").exists():
        _guarded_open(context, Path(last))
    elif not context.settings.first_run_done:
        # first launch, no prior workspace: run the first-run wizard
        from rgcs_desktop.app.first_run import run_first_run
        run_first_run(context)

    window = MainWindow(context)
    window.show()
    return app.exec()


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
