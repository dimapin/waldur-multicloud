"""Identity, idempotency and resource metadata: CON-020..CON-023, CON-050, CON-053."""

from decimal import Decimal

import pytest

from waldur_multicloud import (
    WALDUR_UUID_TAG,
    ContractViolation,
    CreateResult,
    ResourceNotFoundError,
    SecretRef,
    TerminateOutcome,
    check_resource_metadata,
    find_adoptable,
    resource_tag,
    terminate,
    validate_resource_metadata,
)
from waldur_multicloud.resources import provider_tag_key

UUID = "11111111-2222-3333-4444-555555555555"


def test_resource_carries_the_waldur_uuid() -> None:
    """CON-020: the Waldur resource UUID is the tag every resource carries."""
    assert resource_tag(UUID) == (WALDUR_UUID_TAG, UUID)
    with pytest.raises(ContractViolation) as excinfo:
        resource_tag("")
    assert excinfo.value.requirement_ids == ("CON-020",)


def test_undefined_provider_tag_format_is_refused() -> None:
    """CON-020: the per-provider tag format comes from docs/providers/, not from a guess."""
    with pytest.raises(ContractViolation) as excinfo:
        provider_tag_key("hcloud")
    assert excinfo.value.requirement_ids == ("CON-020",)


def test_existing_resource_is_adopted_not_duplicated() -> None:
    """CON-021: create finds the tagged resource and reports it instead of creating."""
    existing = {"id": "srv-1", "labels": {WALDUR_UUID_TAG: UUID}}
    other = {"id": "srv-2", "labels": {WALDUR_UUID_TAG: "other-uuid"}}
    found = find_adoptable([other, existing], UUID, lambda r: r["labels"])
    assert found is existing
    assert find_adoptable([other], UUID, lambda r: r["labels"]) is None


def test_duplicate_tagged_resources_are_a_violation() -> None:
    """CON-021: two resources with the same tag mean create was not idempotent."""
    twin = [{"labels": {WALDUR_UUID_TAG: UUID}} for _ in range(2)]
    with pytest.raises(ContractViolation) as excinfo:
        find_adoptable(twin, UUID, lambda r: r["labels"])
    assert excinfo.value.requirement_ids == ("CON-021",)


def test_terminating_a_missing_resource_is_success() -> None:
    """CON-022: terminate of an absent resource succeeds; the retry must be safe."""
    def gone() -> None:
        raise ResourceNotFoundError("srv-1 does not exist")

    assert terminate(gone) is TerminateOutcome.ALREADY_GONE
    assert terminate(lambda: None) is TerminateOutcome.DELETED


def test_create_result_requires_backend_id() -> None:
    """CON-023: a create without a reportable backend_id is not a create."""
    with pytest.raises(ContractViolation) as excinfo:
        CreateResult("", {})
    assert excinfo.value.requirement_ids == ("CON-023",)
    assert CreateResult("srv-1", {"region": "eu-central"}).backend_id == "srv-1"


def test_metadata_minimum_per_service_class() -> None:
    """CON-050 / CAP-004: the ordering user can identify and use the resource."""
    complete = {
        "provider_resource_id": "srv-1",
        "region": "eu-central",
        "vcpu": 2,
        "ram_gib": Decimal(4),
        "disk_gib": Decimal(40),
    }
    assert check_resource_metadata("compute", complete) == ()

    incomplete = dict(complete)
    del incomplete["region"]
    violations = check_resource_metadata("compute", incomplete)
    assert [v.requirement_id for v in violations] == ["CON-050"]


def test_unknown_service_class_has_no_minimum() -> None:
    """CON-050: an undefined service class is an error, not an empty check."""
    with pytest.raises(ContractViolation) as excinfo:
        check_resource_metadata("serverless", {})
    assert excinfo.value.requirement_ids == ("CON-050",)


def test_credentials_ship_as_secret_reference() -> None:
    """CON-053: kubeconfig and DB credentials travel by reference, never inline."""
    metadata = {
        "provider_resource_id": "db-1",
        "engine": "postgresql",
        "engine_version": "16",
        "endpoint": "db.example.invalid",
        "port": 5432,
        "credentials": "user:PLACEHOLDER@db.example.invalid",
    }
    violations = check_resource_metadata("dbaas", metadata)
    assert {v.requirement_id for v in violations} == {"CON-053"}

    metadata["credentials"] = SecretRef("db-1-credentials")
    validate_resource_metadata("dbaas", metadata)
