"""Quota and capacity handling (proposed CON-070..CON-073, D-004)."""

from decimal import Decimal

import pytest

from waldur_multicloud import (
    WARNING_THRESHOLD,
    QuotaExceededError,
    QuotaUsage,
    check_headroom,
    quota_exceeded,
)


def test_headroom_check_rejects_before_the_provider_call() -> None:
    """CON-071: with a known quota, a hopeless create is rejected without a call."""
    quota = QuotaUsage("servers", used=Decimal(9), limit=Decimal(10))
    check_headroom(quota, 1)
    with pytest.raises(QuotaExceededError) as excinfo:
        check_headroom(quota, 2)
    assert excinfo.value.terminal is True


def test_unknown_limit_never_blocks() -> None:
    """CON-071: where the provider exposes no quota, the pre-check must not invent one."""
    quota = QuotaUsage("servers", used=Decimal(9), limit=None)
    assert quota.utilisation is None
    assert quota.has_headroom(1000) is True
    check_headroom(quota, 1000)


def test_provider_quota_error_maps_to_the_terminal_class() -> None:
    """CON-070: quota errors carry a comprehensible message, not the raw provider error."""
    error = quota_exceeded("provider said resource_limit_exceeded")
    assert error.terminal is True
    assert error.user_message == "Kapazitätsgrenze erreicht."


def test_utilisation_warning_threshold() -> None:
    """CON-073: utilisation is measurable and warns at 80 % — quota raises take lead time."""
    assert WARNING_THRESHOLD == Decimal("0.8")
    assert QuotaUsage("cores", Decimal(80), Decimal(100)).is_warning()
    assert not QuotaUsage("cores", Decimal(79), Decimal(100)).is_warning()
    assert not QuotaUsage("cores", Decimal(80), None).is_warning()
