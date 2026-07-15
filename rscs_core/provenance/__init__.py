"""RSCS-O.12 provenance-propagation operator (the claim firewall in action).

Combines the provenance tags of operator inputs into the tag of the output,
enforcing that the output class is never STRONGER than the weakest input
(EST > DER > HYP/ENG > SRC). This is the runtime enforcement of design
principle 4: an SRC/HYP input cannot be laundered into an EST/DER result. The
process path (e.g. a fabrication history, EP-03-01) is concatenated and the
operator name appended.
"""

from __future__ import annotations

from ..coordinates import ProvenanceTag
from ..registry import CLASS_RANK, assert_no_src_upgrade, rscs_classified

__all__ = ["propagate", "weakest_class"]


def weakest_class(*labels: str) -> str:
    """Return the weakest (lowest-rank) class among the inputs."""
    if not labels:
        raise ValueError("need at least one class label")
    return min(labels, key=lambda lbl: CLASS_RANK[lbl])


@rscs_classified("EST", registry=("RSCS-O.12",), units="metadata",
                 note="output class capped at the weakest input; SRC/HYP "
                      "never upgraded to EST/DER (design principle 4)")
def propagate(operator_name: str, output_class: str,
              *inputs: ProvenanceTag) -> ProvenanceTag:
    """Combine input provenance tags into an output tag under ``operator_name``.

    ``output_class`` is the operator's declared class. It must not exceed the
    weakest input class; a violation raises (the firewall). The returned tag's
    path is the merged input paths plus the operator step."""
    if not inputs:
        raise ValueError("need at least one input ProvenanceTag")
    for t in inputs:
        if not isinstance(t, ProvenanceTag):
            raise TypeError("inputs must be ProvenanceTag (RSCS-C.13)")
    input_classes = [t.claim_class for t in inputs]
    # Firewall: output may not out-rank the weakest input.
    assert_no_src_upgrade(output_class, weakest_class(*input_classes))
    merged_path: tuple[str, ...] = ()
    for t in inputs:
        merged_path = (*merged_path, *t.path)
    merged_path = (*merged_path, f"op:{operator_name}")
    source = inputs[0].source_id if len(inputs) == 1 else "+".join(
        sorted({t.source_id for t in inputs}))
    return ProvenanceTag(source, output_class, merged_path)
