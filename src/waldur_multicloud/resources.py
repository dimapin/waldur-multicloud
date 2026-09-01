"""Resource identity, idempotency and metadata handed back to Waldur.

Covers CON-020..CON-023 (tagging, idempotent create, terminate semantics,
immediate backend_id) and CON-050/CON-053 with the metadata minima of
capabilities.md (CAP-004).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Iterable, Mapping, TypeVar

from .errors import ResourceNotFoundError, is_secret_key
from .violations import ContractViolation, Violation

#: Canonical tag/label key carrying the Waldur resource UUID (CON-020).
WALDUR_UUID_TAG = "waldur-resource-uuid"

#: Per-provider tag format. CON-020 requires the exact format to be fixed in
#: docs/providers/<provider>.md BEFORE the backend is implemented — none is
#: fixed yet, so this map stays empty on purpose. Inventing one here would be
#: exactly the "from memory" guess the repo rules forbid.
PROVIDER_TAG_FORMATS: dict[str, str] = {}


def provider_tag_key(provider: str) -> str:
    """The tag key to use for ``provider`` (CON-020).

    Raises when docs/providers/ has not fixed the format yet, instead of
    quietly falling back to the generic key and creating untaggable resources.
    """
    try:
        return PROVIDER_TAG_FORMATS[provider]
    except KeyError:
        raise ContractViolation.single(
            "CON-020",
            f"no tag format defined for provider {provider!r} — "
            f"fix it in docs/providers/{provider}.md before implementing",
        ) from None


def resource_tag(resource_uuid: str, provider: str | None = None) -> tuple[str, str]:
    """The ``(key, value)`` tag every created resource must carry (CON-020)."""
    if not resource_uuid:
        raise ContractViolation.single("CON-020", "resource UUID must not be empty")
    key = provider_tag_key(provider) if provider is not None else WALDUR_UUID_TAG
    return key, resource_uuid


T = TypeVar("T")


def find_adoptable(
    candidates: Iterable[T],
    resource_uuid: str,
    tags_of: Callable[[T], Mapping[str, str]],
    tag_key: str = WALDUR_UUID_TAG,
) -> T | None:
    """Find an existing resource to adopt instead of creating a second (CON-021).

    More than one match is a violation, not a "pick the first": duplicates mean
    a previous run created what it should have adopted, and silently choosing
    one would leak the other.
    """
    matches = [c for c in candidates if tags_of(c).get(tag_key) == resource_uuid]
    if len(matches) > 1:
        raise ContractViolation.single(
            "CON-021",
            f"{len(matches)} provider resources carry the tag {resource_uuid} — "
            "create was not idempotent",
        )
    return matches[0] if matches else None


class TerminateOutcome(str, Enum):
    """Result of a terminate call (CON-022)."""

    DELETED = "deleted"
    ALREADY_GONE = "already_gone"


def terminate(delete: Callable[[], object]) -> TerminateOutcome:
    """Run ``delete`` and treat an absent resource as success (CON-022)."""
    try:
        delete()
    except ResourceNotFoundError:
        return TerminateOutcome.ALREADY_GONE
    return TerminateOutcome.DELETED


@dataclass(frozen=True)
class SecretRef:
    """Reference to a credential delivered via the Waldur secret mechanism.

    Carries the lookup name only, never the value (CON-053/CON-032) — a secret
    that is never in the object cannot leak through a log line or a repr.
    """

    name: str

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("SecretRef needs a name")


@dataclass(frozen=True)
class CreateResult:
    """Outcome of a create, reported to Waldur before any further step (CON-023)."""

    backend_id: str
    metadata: Mapping[str, object]
    adopted: bool = False

    def __post_init__(self) -> None:
        if not self.backend_id:
            raise ContractViolation.single(
                "CON-023", "create must report a non-empty backend_id"
            )


#: Metadata minimum per service class (capabilities.md, CAP-004/CON-050).
METADATA_MINIMA: dict[str, tuple[str, ...]] = {
    "compute": ("provider_resource_id", "region", "vcpu", "ram_gib", "disk_gib"),
    "k8s": ("provider_resource_id", "kubernetes_version", "nodepools", "api_endpoint"),
    "dbaas": ("provider_resource_id", "engine", "engine_version", "endpoint", "port"),
}

#: Fields that must be a :class:`SecretRef` rather than a plain value (CON-053).
SECRET_METADATA_FIELDS: dict[str, tuple[str, ...]] = {
    "compute": (),
    "k8s": ("kubeconfig",),
    "dbaas": ("credentials",),
}

#: Optional fields the minimum mentions only "if present" (public IP, compute).
OPTIONAL_METADATA_FIELDS: dict[str, tuple[str, ...]] = {
    "compute": ("public_ip",),
    "k8s": (),
    "dbaas": (),
}


def check_resource_metadata(
    service_class: str, metadata: Mapping[str, object]
) -> tuple[Violation, ...]:
    """Collect CON-050/CON-053 violations of the metadata reported after create."""
    if service_class not in METADATA_MINIMA:
        raise ContractViolation.single(
            "CON-050", f"no metadata minimum defined for service class {service_class!r}"
        )

    violations: list[Violation] = []
    checked_secret_fields = set(SECRET_METADATA_FIELDS[service_class])
    for field_name in METADATA_MINIMA[service_class]:
        value = metadata.get(field_name)
        if value is None or value == "":
            violations.append(
                Violation(
                    "CON-050",
                    f"{service_class}: metadata field {field_name!r} is missing",
                )
            )

    for field_name in SECRET_METADATA_FIELDS[service_class]:
        if field_name in metadata and not isinstance(metadata[field_name], SecretRef):
            violations.append(
                Violation(
                    "CON-053",
                    f"{service_class}: {field_name!r} must be delivered as a "
                    "SecretRef via the Waldur secret mechanism, not inline",
                )
            )

    for key, value in metadata.items():
        if key in checked_secret_fields:
            continue  # already reported above, one finding per field
        if is_secret_key(str(key)) and not isinstance(value, SecretRef):
            violations.append(
                Violation("CON-053", f"metadata field {key!r} carries a raw secret value")
            )

    return tuple(violations)


def validate_resource_metadata(
    service_class: str, metadata: Mapping[str, object]
) -> None:
    """Raise :class:`ContractViolation` if the metadata minimum is not met."""
    violations = check_resource_metadata(service_class, metadata)
    if violations:
        raise ContractViolation(violations)
