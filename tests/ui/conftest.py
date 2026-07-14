"""UI test fixtures: offscreen Qt platform and a fresh workspace/context."""
from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest


@pytest.fixture()
def app_context(tmp_path, qapp):
    from rgcs_desktop.app.context import AppContext
    ctx = AppContext()
    ctx.create_workspace(tmp_path / "ws", "test-workspace")
    yield ctx
    ctx.shutdown()


@pytest.fixture()
def main_window(app_context, qtbot):
    from rgcs_desktop.app.main_window import MainWindow
    win = MainWindow(app_context)
    qtbot.addWidget(win)
    win.show()
    # detach shutdown from closeEvent double-shutdown: context is closed by
    # the app_context fixture
    yield win
