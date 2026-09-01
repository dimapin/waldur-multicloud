"""Tests for the machine-readable contract registry (docs/contracts/README.md)."""

import pytest

from waldur_multicloud import (
    CONTRACT_VERSION,
    REQUIREMENTS,
    Level,
    Status,
    active_requirements,
    get_capability,
    get_requirement,
    mandatory_capabilities,
    proposed_requirements,
)
from waldur_multicloud.contract import UnknownRequirementError


def test_ids_are_unique_and_prefixed() -> None:
    """README ID rules: append-only IDs, one namespace each for CON- and CAP-."""
    assert all(key.startswith("CON-") for key in REQUIREMENTS)
    assert len(REQUIREMENTS) == len({r.id for r in REQUIREMENTS.values()})


def test_active_and_proposed_are_disjoint() -> None:
    """v0.3.0 proposals (D-003/D-004) are not binding at contract-v0.2.0."""
    assert CONTRACT_VERSION == "0.2.0"
    active = {r.id for r in active_requirements()}
    proposed = {r.id for r in proposed_requirements()}
    assert not active & proposed
    assert all(r.since <= CONTRACT_VERSION for r in active_requirements())
    assert all(r.status is Status.PROPOSED for r in proposed_requirements())


def test_unknown_id_is_an_error() -> None:
    """An ID that no requirement defines must fail loudly, not return None."""
    with pytest.raises(UnknownRequirementError):
        get_requirement("CON-999")  # meta: not-a-contract-id
    with pytest.raises(UnknownRequirementError):
        get_capability("CAP-999")  # meta: not-a-contract-id


def test_mandatory_capabilities_include_shared_rows() -> None:
    """CAP-001..CAP-004 apply to every service class ('alle')."""
    ids = {c.id for c in mandatory_capabilities("compute")}
    assert {"CAP-001", "CAP-002", "CAP-003", "CAP-004"} <= ids
    assert "CAP-010" not in ids  # KANN, Phase 2
    assert get_capability("CAP-020").level is Level.SHOULD
