"""Shared status, receipts, and privacy helpers for rgcs_lab."""

from rgcs_lab.common.privacy import PrivacyDefaults, privacy_banner
from rgcs_lab.common.receipts import build_receipt, receipt_sha256
from rgcs_lab.common.status import (
    CLAIM_CLASSES,
    ModuleResult,
    Status,
    module_catalog,
)

__all__ = [
    "CLAIM_CLASSES",
    "ModuleResult",
    "PrivacyDefaults",
    "Status",
    "build_receipt",
    "module_catalog",
    "privacy_banner",
    "receipt_sha256",
]
