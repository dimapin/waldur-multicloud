"""Utilities and metadata for the waldur-multicloud project.

The modules mirror the normative contract in docs/contracts/ so that tests and
provider backends can reference CON-/CAP-IDs from code instead of restating
the prose.
"""

from importlib.metadata import PackageNotFoundError, version

from .components import (
    CANONICAL_UNITS,
    BillingType,
    Component,
    Offering,
    Plan,
    bytes_to_gib,
    check_offering,
    mb_to_gib,
    mib_to_gib,
    validate_offering,
)
from .contract import (
    CAPABILITIES,
    CONTRACT_VERSION,
    REQUIREMENTS,
    Capability,
    Level,
    Requirement,
    Status,
    active_requirements,
    get_capability,
    get_requirement,
    mandatory_capabilities,
    proposed_requirements,
)
from .errors import (
    BackendError,
    QuotaExceededError,
    ResourceNotFoundError,
    RetryPolicy,
    TerminalBackendError,
    TransientBackendError,
    redact,
    redact_text,
)
from .limits import WARNING_THRESHOLD, QuotaUsage, check_headroom, quota_exceeded
from .operations import (
    OperationFailedError,
    OperationState,
    OperationTimeoutError,
    Waiter,
    call_with_retry,
)
from .providers import (
    SERVICE_CLASSES,
    SUPPORTED_PROVIDERS,
    backend_name,
    is_supported_provider,
    list_supported_providers,
    parse_backend_name,
)
from .resources import (
    METADATA_MINIMA,
    WALDUR_UUID_TAG,
    CreateResult,
    SecretRef,
    TerminateOutcome,
    check_resource_metadata,
    find_adoptable,
    resource_tag,
    terminate,
    validate_resource_metadata,
)
from .usage import (
    ReportingSchedule,
    UnknownUsageComponentError,
    UsageRecord,
    validate_usage,
)
from .violations import ContractViolation, Violation

__all__ = [
    # contract registry
    "CONTRACT_VERSION",
    "REQUIREMENTS",
    "CAPABILITIES",
    "Requirement",
    "Capability",
    "Status",
    "Level",
    "get_requirement",
    "get_capability",
    "active_requirements",
    "proposed_requirements",
    "mandatory_capabilities",
    # providers
    "SUPPORTED_PROVIDERS",
    "SERVICE_CLASSES",
    "is_supported_provider",
    "list_supported_providers",
    "backend_name",
    "parse_backend_name",
    # components and pricing
    "BillingType",
    "CANONICAL_UNITS",
    "Component",
    "Plan",
    "Offering",
    "check_offering",
    "validate_offering",
    "bytes_to_gib",
    "mib_to_gib",
    "mb_to_gib",
    # resources
    "WALDUR_UUID_TAG",
    "METADATA_MINIMA",
    "CreateResult",
    "SecretRef",
    "TerminateOutcome",
    "resource_tag",
    "find_adoptable",
    "terminate",
    "check_resource_metadata",
    "validate_resource_metadata",
    # usage
    "UsageRecord",
    "UnknownUsageComponentError",
    "ReportingSchedule",
    "validate_usage",
    # errors and limits
    "BackendError",
    "TransientBackendError",
    "TerminalBackendError",
    "QuotaExceededError",
    "ResourceNotFoundError",
    "RetryPolicy",
    "redact",
    "redact_text",
    "QuotaUsage",
    "WARNING_THRESHOLD",
    "check_headroom",
    "quota_exceeded",
    # async operations
    "OperationState",
    "OperationFailedError",
    "OperationTimeoutError",
    "Waiter",
    "call_with_retry",
    # violations
    "Violation",
    "ContractViolation",
    "__version__",
]

try:
    __version__ = version("waldur-multicloud")
except PackageNotFoundError:  # pragma: no cover - used during editable local development
    __version__ = "0.1.0"
