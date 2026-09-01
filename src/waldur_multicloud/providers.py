"""Provider metadata and backend naming for the multi-cloud project.

Naming follows CON-001 (`<provider>-<service>`); the one-offering-per-backend
rule of CON-002 is enforced where an offering is validated
(:func:`waldur_multicloud.components.check_offering`).
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - import cycle avoidance
    from .violations import Violation

SUPPORTED_PROVIDERS = (
    "hcloud",
    "proxmox",
    "ionos",
    "stackit",
)

#: Service classes with a metadata minimum in capabilities.md.
SERVICE_CLASSES = (
    "compute",
    "k8s",
    "dbaas",
)

_SERVICE_SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def list_supported_providers() -> tuple[str, ...]:
    """Return the provider names the project currently supports."""
    return SUPPORTED_PROVIDERS


def is_supported_provider(name: str) -> bool:
    """Check whether a provider slug is part of the active project set."""
    return name in SUPPORTED_PROVIDERS


def is_known_service_class(name: str) -> bool:
    """Check whether a service class has a defined metadata minimum."""
    return name in SERVICE_CLASSES


def backend_name(provider: str, service: str) -> str:
    """Build a CON-001 backend name, rejecting unknown or malformed parts."""
    from .violations import ContractViolation

    if not is_supported_provider(provider):
        raise ContractViolation.single("CON-001", f"unknown provider {provider!r}")
    if not _SERVICE_SLUG.match(service):
        raise ContractViolation.single(
            "CON-001", f"service part {service!r} is not a lowercase slug"
        )
    return f"{provider}-{service}"


def parse_backend_name(name: str) -> tuple[str, str]:
    """Split a backend name into ``(provider, service)`` — CON-001.

    Raises :class:`~waldur_multicloud.violations.ContractViolation` when the
    name does not follow the scheme; a silently accepted name would surface
    much later, as an offering pointing at nothing.
    """
    from .violations import ContractViolation

    violations = check_backend_name(name)
    if violations:
        raise ContractViolation(violations)
    provider, service = name.split("-", 1)
    return provider, service


def check_backend_name(name: str) -> tuple["Violation", ...]:
    """Collect CON-001 violations of a backend name (empty tuple when valid)."""
    from .violations import Violation

    if "-" not in name:
        return (Violation("CON-001", f"backend {name!r} is not '<provider>-<service>'"),)
    provider, service = name.split("-", 1)
    if not is_supported_provider(provider):
        return (Violation("CON-001", f"backend {name!r} names unknown provider {provider!r}"),)
    if not _SERVICE_SLUG.match(service):
        return (Violation("CON-001", f"backend {name!r} has a malformed service part"),)
    return ()
