"""Contract violations carrying the requirement ID they refer to.

docs/contracts/README.md: findings reference IDs. An error message without an
ID cannot be traced back to a norm, so the ID is a required field here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Violation:
    """A single broken requirement."""

    requirement_id: str
    message: str

    def __post_init__(self) -> None:
        from .contract import get_requirement

        get_requirement(self.requirement_id)  # unknown IDs fail loudly

    def __str__(self) -> str:
        return f"{self.requirement_id}: {self.message}"


class ContractViolation(Exception):
    """One or more violated requirements."""

    def __init__(self, violations: Iterable[Violation]) -> None:
        self.violations = tuple(violations)
        if not self.violations:
            raise ValueError("ContractViolation needs at least one violation")
        super().__init__("; ".join(str(v) for v in self.violations))

    @classmethod
    def single(cls, requirement_id: str, message: str) -> "ContractViolation":
        """Shorthand for the one-violation case."""
        return cls([Violation(requirement_id, message)])

    @property
    def requirement_ids(self) -> tuple[str, ...]:
        return tuple(v.requirement_id for v in self.violations)
