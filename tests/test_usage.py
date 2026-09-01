"""Usage reporting: CON-051 (only declared components) and CON-052 (no silent gap)."""

from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from waldur_multicloud import (
    BillingType,
    Component,
    Offering,
    Plan,
    ReportingSchedule,
    UnknownUsageComponentError,
    UsageRecord,
    validate_usage,
)

OFFERING = Offering(
    name="Small VM",
    backend="hcloud-compute",
    service_class="compute",
    components=(
        Component("cpu", "vCPU", BillingType.LIMIT, Decimal(1), Decimal(8)),
        Component("storage", "GiB", BillingType.USAGE),
    ),
    plans=(Plan("basic", {"cpu": Decimal(1), "storage": Decimal("0.05")}),),
    description="storage is billed by usage",
)


def test_declared_components_pass() -> None:
    """CON-051: a report on declared components in their unit is accepted."""
    validate_usage(OFFERING, {"storage": UsageRecord("storage", Decimal(40), "GiB")})


def test_unknown_component_is_visible_not_dropped() -> None:
    """CON-051: the negative case — an unknown component fails, never silently drops."""
    with pytest.raises(UnknownUsageComponentError):
        validate_usage(OFFERING, {"traffic": UsageRecord("traffic", Decimal(1), "GiB")})


def test_wrong_unit_is_rejected() -> None:
    """CON-051: reporting in another unit than the declared one is a wrong invoice."""
    with pytest.raises(UnknownUsageComponentError):
        validate_usage(OFFERING, {"storage": UsageRecord("storage", Decimal(40960), "MiB")})


def test_quota_error_class_is_terminal_for_usage_reports() -> None:
    """CON-051/CON-031: the failure is a terminal backend error, so no retry loop."""
    error = UnknownUsageComponentError("component 'traffic' is unknown")
    assert error.terminal is True


def test_missing_report_is_an_error_state() -> None:
    """CON-052: absent usage reports surface, they do not just age quietly."""
    schedule = ReportingSchedule(interval=timedelta(hours=1))
    now = datetime(2026, 9, 1, 12, 0)
    assert schedule.is_overdue(None, now) is True
    assert schedule.is_overdue(now - timedelta(minutes=59), now) is False
    assert schedule.is_overdue(now - timedelta(hours=2), now) is True
