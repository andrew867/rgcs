"""Frozen-app entry point (PyInstaller target).

A thin wrapper so the spec has a stable script path and so
freeze_support runs before anything else on Windows spawn."""
import multiprocessing

if __name__ == "__main__":
    multiprocessing.freeze_support()
    from rgcs_desktop.app.main import main
    raise SystemExit(main())
