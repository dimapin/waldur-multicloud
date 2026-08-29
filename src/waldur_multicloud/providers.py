"""Provider metadata for the multi-cloud project."""

from __future__ import annotations

SUPPORTED_PROVIDERS = (
    "hcloud",
    "proxmox",
    "ionos",
    "stackit",
)


def list_supported_providers() -> tuple[str, ...]:
    """Return the provider names the project currently supports."""
    return SUPPORTED_PROVIDERS


def is_supported_provider(name: str) -> bool:
    """Check whether a provider slug is part of the active project set."""
    return name in SUPPORTED_PROVIDERS
