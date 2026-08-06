"""V6 scoring model, required-output pointer.

The canonical, tested scoring model lives in the release cage:

    rgcs_workbench/public_cage/design_space_explorer.py

This shim satisfies the V6 required-output list without duplicating
code. Import from the cage module; regenerate every artifact in this
directory with:

    from rgcs_workbench.public_cage import design_space_explorer
    design_space_explorer.write_outputs("docs/research/v6_explorer")
"""

from rgcs_workbench.public_cage.design_space_explorer import (  # noqa: F401
    SCORE_WEIGHTS, explore, score_candidate, write_outputs)
