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


#: option flags the launcher understands; never workspace paths
KNOWN_FLAGS = frozenset({
    "--first-run", "--doctor", "--export-workbook", "--smoke-check",
    "--build-info", "--print-startup-plan", "--private",
})


def plan_startup(argv: list[str], last_workspace: str | None,
                 first_run_done: bool) -> tuple[str, Path | None]:
    """Decide what to do at launch, as a pure function so it is testable
    without a Qt event loop.

    Returns one of:
      ("first_run", None)      -> show the first-run wizard
      ("open", Path)           -> open an existing workspace
      ("create", Path)         -> create a workspace at a given path
      ("none", None)           -> start with no workspace

    ``--first-run`` (and any other ``--flag``) is NEVER treated as a
    workspace path. This is the v4.5.2 regression contract: the frozen
    binary must not create a directory named ``--first-run``.
    """
    if "--first-run" in argv:
        return ("first_run", None)
    # only bare positionals (no leading dash) can be a workspace path
    positional = [a for a in argv if not a.startswith("-")]
    if positional:
        target = Path(positional[0])
        if (target / "workspace.db").exists():
            return ("open", target)
        return ("create", target)
    if last_workspace and (Path(last_workspace) / "workspace.db").exists():
        return ("open", Path(last_workspace))
    if not first_run_done:
        return ("first_run", None)
    return ("none", None)


def build_info_cmd() -> int:
    """`--build-info`: print the frozen build's provenance (version, git
    commit, source hash) as JSON. Offline, no Qt."""
    import json

    from rgcs_desktop.build_meta import build_info
    print(json.dumps(build_info(), indent=2))
    return 0


def print_startup_plan_cmd(argv: list[str]) -> int:
    """`--print-startup-plan [args...]`: print the startup decision for
    the given args without launching the GUI. Used by the packaged
    regression test to prove ``--first-run`` is never a workspace path."""
    from rgcs_desktop.app.context import AppContext
    settings = AppContext().settings
    rest = [a for a in argv if a != "--print-startup-plan"]
    action, path = plan_startup(rest, settings.last_workspace,
                                settings.first_run_done)
    print(f"{action}\t{path if path is not None else ''}")
    return 0


def main(argv: list[str] | None = None) -> int:
    multiprocessing.freeze_support()  # required for frozen (PyInstaller) builds
    argv = argv if argv is not None else sys.argv[1:]

    # headless subcommands (no Qt event loop, safe in the packaged EXE)
    if "--doctor" in argv:
        return doctor()
    if "--build-info" in argv:
        return build_info_cmd()
    if "--print-startup-plan" in argv:
        return print_startup_plan_cmd(argv)
    if "--export-workbook" in argv:
        return export_workbook(argv)

    app = create_app()

    if "--first-run-selftest" in argv:
        # headless equivalent of accepting the wizard, to a given dir;
        # verifies workspace creation + demo + workbook without a GUI.
        import json

        from rgcs_desktop.app.first_run import first_run_selftest
        i = argv.index("--first-run-selftest")
        root = Path(argv[i + 1]) if i + 1 < len(argv) else \
            _default_workspace()
        result = first_run_selftest(root)
        print(json.dumps(result, indent=2))
        ok = (result["workspace_db_exists"] and result["workbook_seeded"]
              and "--first-run" not in Path(result["workspace_root"]).name)
        return 0 if ok else 1

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
    action, target = plan_startup(argv, context.settings.last_workspace,
                                  context.settings.first_run_done)
    if action == "first_run":
        # installer post-install launch (`--first-run`) or genuine first
        # launch: show the wizard. `--first-run` is a flag, never a path.
        from rgcs_desktop.app.first_run import run_first_run
        run_first_run(context)
    elif action == "open":
        _guarded_open(context, target)
    elif action == "create":
        context.create_workspace(target, target.name)
    # action == "none": start with no workspace

    window = MainWindow(context)
    window.show()
    return app.exec()


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
