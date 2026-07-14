"""Shared fixtures for the rgcs_core test suites."""

from __future__ import annotations

import json
import os

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOLDEN_COHERENCE_DIR = os.path.join(REPO_ROOT, "experiments", "sample_data",
                                    "golden_coherence")


@pytest.fixture(scope="session")
def repo_root() -> str:
    return REPO_ROOT


@pytest.fixture(scope="session")
def golden_dir() -> str:
    return GOLDEN_COHERENCE_DIR


@pytest.fixture(scope="session")
def manifest() -> dict:
    path = os.path.join(GOLDEN_COHERENCE_DIR, "manifest.json")
    with open(path) as fh:
        return json.load(fh)
