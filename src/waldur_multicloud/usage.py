"""Usage reporting against the components an offering declares.

Covers CON-051 (only declared components, in their unit, unknown ones fail
loudly) and CON-052 (a missing report is a visible error state, not silently
ageing cost data).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Mapping

from .components import Offering
from .errors import TerminalBackendError


class UnknownUsageComponentError(TerminalBackendError):
    """Usage reported for a component the offering does not declare (CON-051).

    Deliberately an exception rather than a filtered-out entry: silent
    discarding is what CON-051 forbids, and it would show up as an unexplained
    gap in the invoice weeks later.
    """

    user_message = "Verbrauchsmeldung enthält eine unbekannte Komponente."


@dataclass(frozen=True)
class UsageRecord:
    """One reported amount for one component, in the component's unit."""

    component: str
    amount: Decimal
    unit: str

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise ValueError(f"usage for {self.component!r} must not be negative")


def validate_usage(offering: Offering, records: Mapping[str, UsageRecord]) -> None:
    """Check a usage report against the offering (CON-051).

    Raises :class:`UnknownUsageComponentError` for unknown components and for a
    unit that differs from the declared one — a mismatched unit is a wrong
    invoice, not a rounding detail.
    """
    for name, record in records.items():
        component = offering.component(name)
        if component is None:
            raise UnknownUsageComponentError(
                f"offering {offering.name!r} does not declare component {name!r}"
            )
        if record.unit != component.unit:
            raise UnknownUsageComponentError(
                f"component {name!r} is billed in {component.unit!r}, "
                f"report used {record.unit!r}"
            )
        if record.component != name:
            raise UnknownUsageComponentError(
                f"usage key {name!r} does not match record component {record.component!r}"
            )


@dataclass(frozen=True)
class ReportingSchedule:
    """Reporting interval of a backend (CON-052)."""

    interval: timedelta
    #: Grace added before a missing report counts as overdue.
    grace: timedelta = timedelta(minutes=5)

    def __post_init__(self) -> None:
        if self.interval <= timedelta(0):
            raise ValueError("reporting interval must be positive")

    def is_overdue(self, last_report_at: datetime | None, now: datetime) -> bool:
        """Whether usage reporting is overdue and must surface as an error state.

        ``None`` means nothing was ever reported — overdue by definition, so a
        backend that never reports does not look healthy.
        """
        if last_report_at is None:
            return True
        return now - last_report_at > self.interval + self.grace
