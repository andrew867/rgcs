"""Shared program contracts — status vocabulary, receipts, privacy.

The canonical contract is :mod:`rgcs_lab.common.status_schema`
(Claude authority): one ``ModuleStatus``, one claim vocabulary, one
packaged ``receipt_schema.json`` with :func:`validate_receipt`.
:mod:`rgcs_lab.common.status` provides the UI envelope
(``ModuleResult``) which validates THROUGH the canonical contract —
it does not redefine it.
"""

from rgcs_lab.common.privacy import PrivacyDefaults, privacy_banner
from rgcs_lab.common.receipts import build_receipt, receipt_sha256
from rgcs_lab.common.status import (
    CLAIM_CLASSES,
    ModuleResult,
    Status,
    module_catalog,
)
from rgcs_lab.common.status_schema import (
    ALLOWED_WORDING,
    BANNED_WORDING,
    MODULES,
    STATUSES,
    ClaimClass,
    ModuleStatus,
    SchemaError,
    receipt_schema,
    validate_receipt,
)

__all__ = [
    "ALLOWED_WORDING",
    "BANNED_WORDING",
    "CLAIM_CLASSES",
    "ClaimClass",
    "MODULES",
    "ModuleResult",
    "ModuleStatus",
    "PrivacyDefaults",
    "STATUSES",
    "SchemaError",
    "Status",
    "build_receipt",
    "module_catalog",
    "privacy_banner",
    "receipt_schema",
    "receipt_sha256",
    "validate_receipt",
]
