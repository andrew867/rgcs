"""KiCad-oriented Board A and Board B artifact generation."""

from typing import Any

from .model import BoardDefinition, BoardVariant, board_definition, net_registry


def generate_boards(*args: Any, **kwargs: Any):
    from .generator import generate_boards as implementation

    return implementation(*args, **kwargs)


def render_board(*args: Any, **kwargs: Any):
    from .generator import render_board as implementation

    return implementation(*args, **kwargs)

__all__ = [
    "BoardDefinition",
    "BoardVariant",
    "board_definition",
    "generate_boards",
    "net_registry",
    "render_board",
]
