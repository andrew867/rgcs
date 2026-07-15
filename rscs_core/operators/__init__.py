"""Flat facade over the 13 RSCS-O.* operators.

The operators live in the ledger-named subpackages (transforms, coupling,
modes, propagation, state_preparation, observation, uncertainty, provenance,
memory) so each concept has one home matching EXPECTED_TREE. This module
re-exports them as a single namespace for callers (Agents 04-08) who want the
operator set without knowing the internal layout. The OPERATORS map ties each
RSCS-O.* id to its primary callable for registry cross-checks.
"""

from __future__ import annotations

from ..transforms import frame_transform, time_to_frequency, space_to_phase
from ..coupling import (frequency_matrix, anti_hermitian_coupling,
                        couple_modes, hybrid_frequencies, apply_coupling)
from ..modes import parity_matrix, to_parity_basis, from_parity_basis
from ..propagation import (cascade, reverse_cascade, is_unitary, phase_match,
                           group_delay_imbalance, balance_group_delay)
from ..state_preparation import prepare_two_level
from ..observation import (coherence, insertion_loss_db, isolation_db,
                           nonreciprocal_contrast_db)
from ..uncertainty import scale, reciprocal_scale, combine_relative
from ..provenance import propagate as propagate_provenance
from ..memory import store as memory_store, recall as memory_recall

#: RSCS-O.* id -> a representative callable implementing it.
OPERATORS = {
    "RSCS-O.1": frame_transform,
    "RSCS-O.2": time_to_frequency,
    "RSCS-O.3": space_to_phase,
    "RSCS-O.4": couple_modes,
    "RSCS-O.5": to_parity_basis,
    "RSCS-O.6": cascade,
    "RSCS-O.7": phase_match,
    "RSCS-O.8": balance_group_delay,
    "RSCS-O.9": prepare_two_level,
    "RSCS-O.10": coherence,
    "RSCS-O.11": scale,
    "RSCS-O.12": propagate_provenance,
    "RSCS-O.13": memory_store,
}

__all__ = [
    "frame_transform", "time_to_frequency", "space_to_phase",
    "frequency_matrix", "anti_hermitian_coupling", "couple_modes",
    "hybrid_frequencies", "apply_coupling", "parity_matrix",
    "to_parity_basis", "from_parity_basis", "cascade", "reverse_cascade",
    "is_unitary", "phase_match", "group_delay_imbalance",
    "balance_group_delay", "prepare_two_level", "coherence",
    "insertion_loss_db", "isolation_db", "nonreciprocal_contrast_db",
    "scale", "reciprocal_scale", "combine_relative", "propagate_provenance",
    "memory_store", "memory_recall", "OPERATORS",
]
