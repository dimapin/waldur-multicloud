"""Component, unit and price rules: CON-010, CON-011, CON-040..CON-043, CON-072."""

from decimal import Decimal

import pytest

from waldur_multicloud import (
    BillingType,
    Component,
    ContractViolation,
    Offering,
    Plan,
    bytes_to_gib,
    check_offering,
    mb_to_gib,
    mib_to_gib,
    validate_offering,
)


def _components() -> tuple[Component, ...]:
    return (
        Component("cpu", "vCPU", BillingType.LIMIT, Decimal(1), Decimal(8)),
        Component("ram", "GiB", BillingType.LIMIT, Decimal(1), Decimal(32)),
    )


def _offering(**overrides: object) -> Offering:
    defaults: dict[str, object] = {
        "name": "Small VM",
        "backend": "hcloud-compute",
        "service_class": "compute",
        "components": _components(),
        "plans": (Plan("basic", {"cpu": Decimal("1.5"), "ram": Decimal("0")}),),
    }
    defaults.update(overrides)
    return Offering(**defaults)  # type: ignore[arg-type]


def test_conforming_offering_has_no_violations() -> None:
    """CON-040/CON-041: complete components plus a plan pricing each of them."""
    assert check_offering(_offering()) == ()


def test_canonical_unit_is_enforced() -> None:
    """CON-010: RAM is GiB everywhere; provider units are converted in the backend."""
    with pytest.raises(ContractViolation) as excinfo:
        Component("ram", "MB", BillingType.LIMIT, Decimal(1), Decimal(4))
    assert excinfo.value.requirement_ids == ("CON-010",)


def test_unit_conversions_land_on_gib() -> None:
    """CON-010: conversion helpers, so no backend rolls its own factor."""
    assert bytes_to_gib(1024**3) == Decimal(1)
    assert mib_to_gib(2048) == Decimal(2)
    assert mb_to_gib(1000) == Decimal(10**9) / Decimal(1024**3)


def test_component_without_billing_type_does_not_load() -> None:
    """CON-040: a component with incomplete data must not load at all."""
    with pytest.raises(ContractViolation) as excinfo:
        Component("extra", "Stück", "fest")  # type: ignore[arg-type]
    assert excinfo.value.requirement_ids == ("CON-040",)


def test_duplicate_component_name_is_a_violation() -> None:
    """CON-011: like-for-like components are named once, comparably."""
    duplicated = _components() + (Component("cpu", "vCPU", BillingType.FIXED),)
    violations = check_offering(_offering(components=duplicated))
    assert "CON-011" in {v.requirement_id for v in violations}


def test_missing_price_is_a_violation_free_means_explicit_zero() -> None:
    """CON-041: every component is priced; free is 0, never an omission."""
    violations = check_offering(_offering(plans=(Plan("basic", {"cpu": Decimal(1)}),)))
    assert [v.requirement_id for v in violations] == ["CON-041"]
    assert "ram" in violations[0].message


def test_active_offering_without_active_plan_is_a_violation() -> None:
    """CON-041: an active offering always has at least one active plan."""
    inactive = Plan("old", {"cpu": Decimal(1), "ram": Decimal(0)}, active=False)
    violations = check_offering(_offering(plans=(inactive,)))
    assert [v.requirement_id for v in violations] == ["CON-041"]


def test_displayed_unit_must_equal_billed_unit() -> None:
    """CON-042: no conversion factor between what is shown and what is billed."""
    with pytest.raises(ContractViolation) as excinfo:
        Component("disk", "GiB", BillingType.LIMIT, Decimal(1), Decimal(10), display_unit="TB")
    assert excinfo.value.requirement_ids == ("CON-042",)


def test_usage_based_component_needs_a_description() -> None:
    """CON-043: purely usage-based components are recognisable as such."""
    traffic = Component("traffic", "GiB", BillingType.USAGE)
    violations = check_offering(
        _offering(components=_components() + (traffic,),
                  plans=(Plan("basic", {"cpu": Decimal(1), "ram": Decimal(0),
                                        "traffic": Decimal("0.01")}),))
    )
    assert [v.requirement_id for v in violations] == ["CON-043"]


def test_proposed_limit_bounds_are_not_enforced() -> None:
    """CON-072 is not active in contract-v0.2.0."""
    assert Component("cpu", "vCPU", BillingType.LIMIT).min_value is None


def test_ordered_amount_is_checked_against_bounds() -> None:
    """CON-072 (proposed): an order outside min/max is rejected."""
    cpu = _components()[0]
    cpu.check_limit(8)
    with pytest.raises(ContractViolation) as excinfo:
        cpu.check_limit(9)
    assert excinfo.value.requirement_ids == ("CON-072",)


def test_validate_offering_reports_every_violation_at_once() -> None:
    """An operator fixing an offering needs the full list, not the first entry."""
    broken = _offering(backend="unknown-compute", plans=(Plan("basic", {}),))
    with pytest.raises(ContractViolation) as excinfo:
        validate_offering(broken)
    assert set(excinfo.value.requirement_ids) == {"CON-001", "CON-041"}
