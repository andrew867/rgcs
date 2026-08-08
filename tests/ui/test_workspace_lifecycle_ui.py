"""Workspace lifecycle from the UI (v8.5.2): close/switch commands,
teardown, welcome-state survival."""


def test_lifecycle_commands_exist(main_window):
    names = main_window.command_names()
    for cmd in ("Workspace: close", "Workspace: switch…",
                "Workspace: reveal folder",
                "Workspace: repair factory content"):
        assert cmd in names


def test_close_workspace_returns_home_and_survives(main_window):
    assert main_window.context.workspace is not None
    main_window.run_command("Workspace: close")
    assert main_window.context.workspace is None
    assert main_window.tabs.currentWidget() is \
        main_window.panels["Design Studio"]
    # every panel survived refresh with no workspace open
    for title, panel in main_window.panels.items():
        info = panel.inspector_info()
        assert "properties" in info, title
    # closing again is a no-op
    main_window.run_command("Workspace: close")


def test_switch_workspace_installs_factory_content(main_window,
                                                   tmp_path):
    root = tmp_path / "second-ws"
    main_window.context.create_workspace(root, "second")
    factory = root / "library" / "frequency_sessions" / "factory" / \
        "aha_halo_curated"
    assert len(list(factory.glob("*.json"))) == 61


def test_repair_command_reports_without_workspace(main_window):
    main_window.run_command("Workspace: close")
    # must log a refusal, not raise
    main_window.run_command("Workspace: repair factory content")
    main_window.run_command("Workspace: reveal folder")


def test_teardown_is_repeat_safe(main_window):
    for panel in main_window.panels.values():
        panel.teardown()
        panel.teardown()
