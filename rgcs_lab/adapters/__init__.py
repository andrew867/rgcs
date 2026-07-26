"""Domain adapters — prefer installed Codex packages, else reference demos."""

from __future__ import annotations

from importlib import import_module
from typing import Any, Callable


def resolve(preferred: str, fallback: str) -> Any:
    """Import preferred package/module; fall back to lab reference."""
    try:
        return import_module(preferred)
    except ImportError:
        return import_module(fallback)


def call_or_reference(
    preferred: str,
    attr: str,
    fallback_mod: str,
    fallback_attr: str,
    *args: Any,
    **kwargs: Any,
) -> Any:
    mod = resolve(preferred, fallback_mod)
    fn: Callable[..., Any]
    if hasattr(mod, attr):
        fn = getattr(mod, attr)
    else:
        fb = import_module(fallback_mod)
        fn = getattr(fb, fallback_attr)
    return fn(*args, **kwargs)
