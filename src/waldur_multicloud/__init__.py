"""Utilities and metadata for the waldur-multicloud project."""

from importlib.metadata import PackageNotFoundError, version

from .providers import SUPPORTED_PROVIDERS, is_supported_provider, list_supported_providers

__all__ = [
    "SUPPORTED_PROVIDERS",
    "is_supported_provider",
    "list_supported_providers",
    "__version__",
]

try:
    __version__ = version("waldur-multicloud")
except PackageNotFoundError:  # pragma: no cover - used during editable local development
    __version__ = "0.1.0"
