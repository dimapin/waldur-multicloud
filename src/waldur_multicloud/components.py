"""Billing components, units and plans of an offering.

Implements the checkable part of CON-010/011 (canonical names and units),
CON-040/041/042/043 (component and price visibility, D-002) and the component
bounds of the proposed CON-072 (D-004).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum

from .violations import ContractViolation, Violation


class BillingType(str, Enum):
    """Billing type a component must declare (CON-040)."""

    FIXED = "fest"
    LIMIT = "limitbasiert"
    USAGE = "nutzungsbasiert"


#: Canonical unit per canonical component name (CON-010/CON-011). Providers
#: converting from their own units do so in the backend, never in the plan.
CANONICAL_UNITS: dict[str, str] = {
    "cpu": "vCPU",
    "ram": "GiB",
    "storage": "GiB",
}

GIB = 1024**3


def bytes_to_gib(value: int) -> Decimal:
    """Convert provider bytes to the canonical GiB unit (CON-010)."""
    return Decimal(value) / Decimal(GIB)


def mib_to_gib(value: float | int | Decimal) -> Decimal:
    """Convert provider MiB to the canonical GiB unit (CON-010)."""
    return Decimal(str(value)) / Decimal(1024)


def mb_to_gib(value: float | int | Decimal) -> Decimal:
    """Convert provider MB (10^6 bytes) to the canonical GiB unit (CON-010)."""
    return Decimal(str(value)) * Decimal(10**6) / Decimal(GIB)


@dataclass(frozen=True)
class Component:
    """One billing component of an offering.

    A component without unit or billing type must not load (CON-040), so the
    invalid state is rejected in the constructor rather than reported later.
    """

    name: str
    unit: str
    billing_type: BillingType
    min_value: Decimal | None = None
    max_value: Decimal | None = None
    display_unit: str | None = None
    description: str = ""

    def __post_init__(self) -> None:
        if not self.name:
            raise ContractViolation.single("CON-040", "component name must not be empty")
        if not self.unit:
            raise ContractViolation.single(
                "CON-040", f"component {self.name!r} has no unit"
            )
        if not isinstance(self.billing_type, BillingType):
            raise ContractViolation.single(
                "CON-040", f"component {self.name!r} has no billing type"
            )
        canonical = CANONICAL_UNITS.get(self.name)
        if canonical is not None and self.unit != canonical:
            raise ContractViolation.single(
                "CON-010",
                f"component {self.name!r} must use unit {canonical!r}, got {self.unit!r}",
            )
        if self.display_unit is not None and self.display_unit != self.unit:
            raise ContractViolation.single(
                "CON-042",
                f"component {self.name!r}: displayed unit {self.display_unit!r} "
                f"differs from billed unit {self.unit!r}",
            )
        if self.billing_type is BillingType.LIMIT:
            if self.min_value is None or self.max_value is None:
                raise ContractViolation.single(
                    "CON-072",
                    f"limit-based component {self.name!r} needs min and max per order",
                )
            if self.min_value < 0:
                raise ContractViolation.single(
                    "CON-072", f"component {self.name!r}: min_value must be >= 0"
                )
            if self.max_value < self.min_value:
                raise ContractViolation.single(
                    "CON-072", f"component {self.name!r}: max_value below min_value"
                )

    @property
    def shown_unit(self) -> str:
        """Unit shown to the customer — identical to the billed one (CON-042)."""
        return self.display_unit or self.unit

    def check_limit(self, value: Decimal | int | float) -> None:
        """Validate an ordered amount against the offering bounds (CON-072)."""
        amount = Decimal(str(value))
        if self.min_value is not None and amount < self.min_value:
            raise ContractViolation.single(
                "CON-072",
                f"{self.name}: {amount} below the minimum {self.min_value}",
            )
        if self.max_value is not None and amount > self.max_value:
            raise ContractViolation.single(
                "CON-072",
                f"{self.name}: {amount} above the maximum {self.max_value}",
            )


@dataclass(frozen=True)
class Plan:
    """A price plan of an offering (CON-041)."""

    name: str
    prices: dict[str, Decimal] = field(default_factory=dict)
    active: bool = True


@dataclass(frozen=True)
class Offering:
    """A marketplace offering — exactly one backend (CON-002)."""

    name: str
    backend: str
    service_class: str
    components: tuple[Component, ...]
    plans: tuple[Plan, ...] = ()
    active: bool = True
    description: str = ""

    def component(self, name: str) -> Component | None:
        """The component with ``name``, or ``None`` if the offering has none."""
        return next((c for c in self.components if c.name == name), None)

    @property
    def component_names(self) -> tuple[str, ...]:
        return tuple(c.name for c in self.components)


def check_offering(offering: Offering) -> tuple[Violation, ...]:
    """Collect every contract violation of an offering instead of failing fast.

    Fail-fast would hide the second problem behind the first; an operator
    fixing an offering wants the full list.
    """
    from .providers import check_backend_name  # local import: avoids a cycle

    violations: list[Violation] = list(check_backend_name(offering.backend))

    if not offering.components:
        violations.append(
            Violation("CON-040", f"offering {offering.name!r} declares no components")
        )

    seen: set[str] = set()
    for component in offering.components:
        if component.name in seen:
            violations.append(
                Violation("CON-011", f"component {component.name!r} declared twice")
            )
        seen.add(component.name)

    active_plans = [plan for plan in offering.plans if plan.active]
    if offering.active and not active_plans:
        violations.append(
            Violation("CON-041", f"active offering {offering.name!r} has no active plan")
        )

    for plan in active_plans:
        for component in offering.components:
            if component.name not in plan.prices:
                violations.append(
                    Violation(
                        "CON-041",
                        f"plan {plan.name!r} has no price for component "
                        f"{component.name!r} — free means an explicit 0",
                    )
                )
            elif plan.prices[component.name] < 0:
                violations.append(
                    Violation(
                        "CON-041",
                        f"plan {plan.name!r}: negative price for {component.name!r}",
                    )
                )
        for priced in plan.prices:
            if priced not in seen:
                violations.append(
                    Violation(
                        "CON-040",
                        f"plan {plan.name!r} prices unknown component {priced!r}",
                    )
                )

    usage_only = [c for c in offering.components if c.billing_type is BillingType.USAGE]
    if usage_only and not offering.description:
        violations.append(
            Violation(
                "CON-043",
                "usage-based components require a description that says so: "
                + ", ".join(c.name for c in usage_only),
            )
        )

    return tuple(violations)


def validate_offering(offering: Offering) -> None:
    """Raise :class:`ContractViolation` if the offering breaks the contract."""
    violations = check_offering(offering)
    if violations:
        raise ContractViolation(violations)
