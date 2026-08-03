"""Executable-namespace and result-language firewall."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
import re


_IDENTIFIER_FRAGMENTS = ("force", "thrust", "propulsion", "wall_power")
_POSITIVE_CLAIM = re.compile(
    r"\b(?:force|thrust|lift|propulsion|antigravity|over-unity|craft)\b"
    r".{0,24}\b(?:confirmed|detected|demonstrated|produced|achieved|works)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ExecutableAudit:
    files_scanned: int
    identifiers_scanned: int
    leaks: tuple[str, ...]

    @property
    def clean(self) -> bool:
        return not self.leaks


def _identifiers(tree: ast.AST) -> list[str]:
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.append(node.name)
        elif isinstance(node, ast.Name):
            names.append(node.id)
        elif isinstance(node, ast.Attribute):
            names.append(node.attr)
        elif isinstance(node, ast.arg):
            names.append(node.arg)
    return names


def audit_executable_tree(root: str | Path | None = None) -> ExecutableAudit:
    package_root = Path(root) if root is not None else Path(__file__).parents[1]
    files = [
        path
        for path in sorted(package_root.rglob("*.py"))
        if "tests" not in path.relative_to(package_root).parts
    ]
    leaks: list[str] = []
    count = 0
    for path in files:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for name in _identifiers(tree):
            count += 1
            lowered = name.lower()
            if any(fragment in lowered for fragment in _IDENTIFIER_FRAGMENTS):
                leaks.append(f"{path.relative_to(package_root).as_posix()}:{name}")
    return ExecutableAudit(len(files), count, tuple(leaks))


def validate_claim_text(text: str) -> None:
    if _POSITIVE_CLAIM.search(text):
        raise ValueError("claim exceeds the field-asymmetry boundary")
