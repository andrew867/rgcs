"""Factory content: packaged demo/curated files installed into a
workspace, idempotently.

The package ships a factory manifest (``rgcs_desktop/data/
factory_manifest.json``) listing every factory file with its sha256 and
an install policy. ``sync_factory_content`` applies it to a workspace
folder so that first runs, re-runs, and upgrades all converge:

- missing files are added,
- files the user has edited are never touched,
- unmodified factory files are updated in place when the package ships
  a newer version,
- an existing workspace folder is never a reason to fail.

Curated sessions are source-language frequency records: claimed uses
are recorded, not endorsed. No Qt imports here.
"""
from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
FACTORY_MANIFEST = DATA_DIR / "factory_manifest.json"

# Workspace-relative state file recording the factory hash each file had
# when we installed/updated it. A file whose current hash differs from
# the recorded one is user-modified and untouchable.
STATE_RELPATH = "library/factory_state.json"

INSTALL_POLICIES = ("add_if_missing", "update_if_unmodified",
                    "never_overwrite_user_file", "deprecated_hide")


class FactoryContentError(RuntimeError):
    """A factory manifest entry is malformed or unreadable."""


@lru_cache(maxsize=1)
def load_factory_manifest() -> dict:
    body = json.loads(FACTORY_MANIFEST.read_text(encoding="utf-8"))
    for item in body["items"]:
        if item["install_policy"] not in INSTALL_POLICIES:
            raise FactoryContentError(
                f"{item['factory_id']}: unknown install policy "
                f"{item['install_policy']!r}")
    return body


def factory_items() -> list[dict]:
    return list(load_factory_manifest()["items"])


def factory_file_bytes(item: dict) -> bytes:
    src = DATA_DIR / item["package_relpath"]
    if not src.is_file():
        raise FactoryContentError(
            f"{item['factory_id']}: packaged file missing "
            f"({item['package_relpath']})")
    return src.read_bytes()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_factory_state(workspace_root: str | Path) -> dict:
    path = Path(workspace_root) / STATE_RELPATH
    if not path.is_file():
        return {}
    try:
        body = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return body.get("installed", {}) if isinstance(body, dict) else {}


def _write_factory_state(workspace_root: Path, installed: dict) -> Path:
    path = workspace_root / STATE_RELPATH
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps({"schema_version": "1.0.0",
                               "state_kind": "rgcs.factory_state/v1",
                               "installed": installed},
                              indent=2, sort_keys=True) + "\n",
                   encoding="utf-8")
    tmp.replace(path)
    return path


def sync_factory_content(workspace_root: str | Path,
                         manifest: dict | None = None) -> dict:
    """Install/refresh factory content in ``workspace_root``.

    Idempotent: safe to run on a brand-new folder, an existing
    workspace, or repeatedly. Never raises because a folder or file
    already exists, and never overwrites a user-modified file.

    Returns a report: {"added": [...], "updated": [...],
    "kept_user_modified": [...], "unchanged": [...], "hidden": [...],
    "state_path": str}.
    """
    workspace_root = Path(workspace_root)
    workspace_root.mkdir(parents=True, exist_ok=True)
    body = manifest if manifest is not None else load_factory_manifest()
    installed = load_factory_state(workspace_root)

    report: dict = {"added": [], "updated": [], "kept_user_modified": [],
                    "unchanged": [], "hidden": [],
                    "migrated_legacy": _migrate_legacy_factory_dirs(
                        workspace_root, body)}

    # PLAN pass: decide every action before touching anything, so a
    # tiny backup manifest can record the prior state first (v8.5.3).
    plan: list[tuple[str, dict, bytes]] = []   # (action, item, payload)
    for item in body["items"]:
        fid = item["factory_id"]
        if item["install_policy"] not in INSTALL_POLICIES:
            raise FactoryContentError(
                f"{fid}: unknown install policy "
                f"{item['install_policy']!r}")
        target = workspace_root / item["relative_path"]
        if item["install_policy"] == "deprecated_hide":
            report["hidden"].append(fid)
            continue

        payload = factory_file_bytes(item)
        if not target.exists():
            plan.append(("add", item, payload))
            continue

        current = _sha256(target.read_bytes())
        recorded = installed.get(fid)
        if recorded is not None and current != recorded:
            # user edited this file after we installed it — untouchable
            report["kept_user_modified"].append(fid)
            continue
        if recorded is None and current != item["sha256"]:
            # pre-existing file we never installed and don't recognize:
            # treat as the user's, regardless of policy
            report["kept_user_modified"].append(fid)
            continue
        if current == item["sha256"]:
            installed[fid] = current
            report["unchanged"].append(fid)
            continue
        # unmodified factory copy of an older version
        if item["install_policy"] in ("add_if_missing",
                                      "never_overwrite_user_file"):
            report["unchanged"].append(fid)
            continue
        plan.append(("update", item, payload))

    if any(action == "update" for action, _i, _p in plan) \
            or report["migrated_legacy"]:
        report["backup_manifest"] = str(_write_backup_manifest(
            workspace_root, plan, installed, report["migrated_legacy"]))
    else:
        report["backup_manifest"] = None

    # APPLY pass
    for action, item, payload in plan:
        fid = item["factory_id"]
        target = workspace_root / item["relative_path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
        installed[fid] = _sha256(payload)
        report["added" if action == "add" else "updated"].append(fid)

    report["state_path"] = str(_write_factory_state(workspace_root,
                                                    installed))
    return report


def _write_backup_manifest(workspace_root: Path, plan, installed: dict,
                           migrated: list[str]) -> Path:
    """Tiny pre-upgrade record: what is about to change and the hash it
    had before. Written under library/factory_backup/."""
    import time
    backup_dir = workspace_root / "library" / "factory_backup"
    backup_dir.mkdir(parents=True, exist_ok=True)
    entries = [{"factory_id": item["factory_id"],
                "relative_path": item["relative_path"],
                "action": action,
                "prior_sha256": installed.get(item["factory_id"]),
                "new_sha256": item["sha256"]}
               for action, item, _payload in plan]
    body = {"schema_version": "1.0.0",
            "backup_kind": "rgcs.factory_backup/v1",
            "migrated_legacy_dirs": migrated,
            "changes": entries}
    stamp = time.strftime("%Y%m%d-%H%M%S")
    target = backup_dir / f"factory_backup_{stamp}.json"
    n = 2
    while target.exists():
        target = backup_dir / f"factory_backup_{stamp}_{n}.json"
        n += 1
    target.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8")
    return target


def _migrate_legacy_factory_dirs(workspace_root: Path,
                                 manifest: dict) -> list[str]:
    """Move factory subdirs the manifest no longer references into the
    workspace trash (never delete). The factory tree is fully managed:
    renamed factory families from older releases would otherwise list
    duplicate sessions forever. User files live under user/, which is
    never touched.
    """
    import time
    factory = workspace_root / "library" / "frequency_sessions" / \
        "factory"
    if not factory.is_dir():
        return []
    known = set()
    for item in manifest.get("items", []):
        rel = Path(item["relative_path"])
        parts = rel.parts
        if "factory" in parts:
            idx = parts.index("factory")
            if idx + 1 < len(parts) - 1:
                known.add(parts[idx + 1])
    migrated = []
    for sub in factory.iterdir():
        if not sub.is_dir() or sub.name in known:
            continue
        trash = workspace_root / "library" / "trash"
        trash.mkdir(parents=True, exist_ok=True)
        stamp = time.strftime("%Y%m%d-%H%M%S")
        target = trash / f"legacy_factory_{sub.name}_{stamp}"
        n = 2
        while target.exists():
            target = trash / f"legacy_factory_{sub.name}_{stamp}_{n}"
            n += 1
        sub.rename(target)
        migrated.append(sub.name)
    return migrated


def repair_factory_content(workspace_root: str | Path) -> dict:
    """Restore missing factory files (a sync run does exactly this)."""
    return sync_factory_content(workspace_root)
