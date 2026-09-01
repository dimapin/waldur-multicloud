"""Provider quotas and capacity handling (proposed CON-070..CON-073, D-004).

Quota exhaustion is a terminal error class, never a retry loop; where the
provider API exposes quotas, the backend checks headroom before create — as a
fast rejection, not as a guarantee.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .errors import QuotaExceededError

#: Utilisation from which a quota should raise a warning (CON-073).
WARNING_THRESHOLD = Decimal("0.8")


@dataclass(frozen=True)
class QuotaUsage:
    """Used vs. limit for one provider quota (CON-071/CON-073)."""

    name: str
    used: Decimal
    limit: Decimal | None

    def __post_init__(self) -> None:
        if self.used < 0:
            raise ValueError("used must be >= 0")
        if self.limit is not None and self.limit < 0:
            raise ValueError("limit must be >= 0")

    @property
    def utilisation(self) -> Decimal | None:
        """Used/limit, or ``None`` when the provider reports no limit."""
        if self.limit is None or self.limit == 0:
            return None
        return self.used / self.limit

    @property
    def headroom(self) -> Decimal | None:
        """Remaining amount, or ``None`` when the provider reports no limit."""
        if self.limit is None:
            return None
        return self.limit - self.used

    def is_warning(self, threshold: Decimal = WARNING_THRESHOLD) -> bool:
        """Whether utilisation has reached the warning threshold (CON-073)."""
        utilisation = self.utilisation
        return utilisation is not None and utilisation >= threshold

    def has_headroom(self, requested: Decimal | int | float) -> bool:
        """Whether ``requested`` still fits — best effort, never a guarantee.

        CON-071: parallel orders race here, so the provider answer stays
        authoritative. This only avoids a call that is certain to fail.
        """
        amount = Decimal(str(requested))
        headroom = self.headroom
        return headroom is None or amount <= headroom


def check_headroom(quota: QuotaUsage, requested: Decimal | int | float) -> None:
    """Reject a create before calling the provider when the quota cannot fit it.

    Raises :class:`~waldur_multicloud.errors.QuotaExceededError`, which is
    terminal (CON-070): the caller must not retry it.
    """
    if not quota.has_headroom(requested):
        raise QuotaExceededError(
            f"quota {quota.name!r}: requested {requested}, "
            f"headroom {quota.headroom} of limit {quota.limit}"
        )


def quota_exceeded(message: str) -> QuotaExceededError:
    """Wrap a provider quota error in the terminal class (CON-070).

    Backends map their provider-specific code (e.g. a limit-exceeded response)
    onto this instead of letting a generic error reach the retry loop.
    """
    return QuotaExceededError(message)
