"""Machine-readable mirror of docs/contracts/ (conventions + capabilities).

The prose in ``docs/contracts/conventions.md`` and
``docs/contracts/capabilities.md`` stays normative; this module only makes the
IDs referenceable from code and tests. Per docs/contracts/README.md the IDs are
append-only: never re-use, never re-interpret — deprecate and add a successor.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

CONTRACT_VERSION = "0.2.0"
"""Ratified contract version this package implements (contract-v0.2.0).

CON-060..CON-073 are carried as PROPOSED for the v0.3.0 draft (D-003/D-004) and
are excluded from :func:`active_requirements`.
"""


class Status(str, Enum):
    """Lifecycle of a requirement ID (docs/contracts/README.md, ID rules)."""

    ACTIVE = "aktiv"
    PROPOSED = "vorgeschlagen"
    DEPRECATED = "deprecated"


class Level(str, Enum):
    """Normative keyword of a requirement."""

    MUST = "MUSS"
    SHOULD = "SOLL"
    MAY = "KANN"


@dataclass(frozen=True)
class Requirement:
    """One normative statement from conventions.md or capabilities.md."""

    id: str
    status: Status
    level: Level
    section: str
    summary: str
    since: str
    superseded_by: str | None = None

    @property
    def is_active(self) -> bool:
        return self.status is Status.ACTIVE


def _con(
    id_: str,
    status: Status,
    level: Level,
    section: str,
    summary: str,
    since: str = "0.1.0",
) -> Requirement:
    return Requirement(id_, status, level, section, summary, since)


_REQUIREMENTS: tuple[Requirement, ...] = (
    # --- Namen und Struktur ---
    _con("CON-001", Status.ACTIVE, Level.MUST, "names",
         "Backend names follow '<provider>-<service>'."),
    _con("CON-002", Status.ACTIVE, Level.MUST, "names",
         "One marketplace offering maps to exactly one backend."),
    # --- Einheiten und Komponenten ---
    _con("CON-010", Status.ACTIVE, Level.MUST, "components",
         "Canonical units across providers: storage/RAM in GiB, vCPU as count."),
    _con("CON-011", Status.ACTIVE, Level.MUST, "components",
         "Like-for-like components share the same name across offerings."),
    # --- Idempotenz und Zustand ---
    _con("CON-020", Status.ACTIVE, Level.MUST, "idempotency",
         "Every provider resource carries the Waldur resource UUID as tag/label."),
    _con("CON-021", Status.ACTIVE, Level.MUST, "idempotency",
         "Create is idempotent: an existing tagged resource is adopted."),
    _con("CON-022", Status.ACTIVE, Level.MUST, "idempotency",
         "Terminating a missing resource counts as success."),
    _con("CON-023", Status.ACTIVE, Level.MUST, "idempotency",
         "backend_id is reported to Waldur immediately after create."),
    # --- Asynchronitaet und Fehler ---
    _con("CON-030", Status.ACTIVE, Level.MUST, "async",
         "Success requires a confirmed target state, not an accepted request."),
    _con("CON-031", Status.ACTIVE, Level.MUST, "async",
         "Order errors surface in the Waldur order state; retries are bounded."),
    _con("CON-032", Status.ACTIVE, Level.MUST, "async",
         "Secrets never appear in logs, errors or repr()."),
    # --- Preis- und Komponentensichtbarkeit (v0.2.0, D-002) ---
    _con("CON-040", Status.ACTIVE, Level.MUST, "pricing",
         "Components declare unit and billing type; incomplete ones do not load.",
         since="0.2.0"),
    _con("CON-041", Status.ACTIVE, Level.MUST, "pricing",
         "An active plan prices every component; free means explicit 0.",
         since="0.2.0"),
    _con("CON-042", Status.ACTIVE, Level.MUST, "pricing",
         "Displayed unit and billed unit are identical.", since="0.2.0"),
    _con("CON-043", Status.ACTIVE, Level.SHOULD, "pricing",
         "Limit-based components allow an order-time cost estimate.", since="0.2.0"),
    # --- Ressourcen-Sichtbarkeit (v0.2.0, D-002) ---
    _con("CON-050", Status.ACTIVE, Level.MUST, "resource-visibility",
         "Create reports the metadata minimum of the service class.", since="0.2.0"),
    _con("CON-051", Status.ACTIVE, Level.MUST, "resource-visibility",
         "Usage reports reference only declared components, in their unit.",
         since="0.2.0"),
    _con("CON-052", Status.ACTIVE, Level.MUST, "resource-visibility",
         "Usage is reported at least once per reporting interval.", since="0.2.0"),
    _con("CON-053", Status.ACTIVE, Level.MUST, "resource-visibility",
         "Access credentials ship via the Waldur metadata/secret mechanism only.",
         since="0.2.0"),
    # --- Provisionierungs-Engine (VORSCHLAG v0.3.0, D-003) ---
    _con("CON-060", Status.PROPOSED, Level.MUST, "engine",
         "The provisioning engine is an explicit, documented per-backend decision.",
         since="0.3.0"),
    _con("CON-061", Status.PROPOSED, Level.MUST, "engine",
         "Provisioning converges on the resource UUID and is resumable.",
         since="0.3.0"),
    _con("CON-062", Status.PROPOSED, Level.MUST, "engine",
         "Engine and module/composition version live in the resource metadata.",
         since="0.3.0"),
    _con("CON-063", Status.PROPOSED, Level.MUST, "engine",
         "Engine output never reaches Waldur or logs unfiltered.", since="0.3.0"),
    _con("CON-065", Status.PROPOSED, Level.MUST, "engine-opentofu",
         "Remote state with locking, one state per Waldur resource.", since="0.3.0"),
    _con("CON-066", Status.PROPOSED, Level.MUST, "engine-opentofu",
         "State storage is versioned and encrypted, agent-only access.", since="0.3.0"),
    _con("CON-067", Status.PROPOSED, Level.MUST, "engine-opentofu",
         "State loss is recoverable via the CON-020 tags.", since="0.3.0"),
    # --- Limits und Kapazitaet (VORSCHLAG v0.3.0, D-004) ---
    _con("CON-070", Status.PROPOSED, Level.MUST, "limits",
         "Quota errors are terminal: no retry, understandable order message.",
         since="0.3.0"),
    _con("CON-071", Status.PROPOSED, Level.SHOULD, "limits",
         "Where the API exposes quotas, check headroom before create (no guarantee).",
         since="0.3.0"),
    _con("CON-072", Status.PROPOSED, Level.MUST, "limits",
         "Offerings bound orderable sizes; unbounded inputs must not exist.",
         since="0.3.0"),
    _con("CON-073", Status.PROPOSED, Level.SHOULD, "limits",
         "Quota utilisation is a metric with a warning threshold (80 %).",
         since="0.3.0"),
)


@dataclass(frozen=True)
class Capability:
    """One row of docs/contracts/capabilities.md."""

    id: str
    service_class: str
    operation: str
    level: Level
    since: str = "0.1.0"


_CAPABILITIES: tuple[Capability, ...] = (
    Capability("CAP-001", "alle", "create", Level.MUST),
    Capability("CAP-002", "alle", "terminate", Level.MUST),
    Capability("CAP-003", "alle", "usage-report", Level.MUST),
    Capability("CAP-004", "alle", "resource-metadata", Level.MUST, since="0.2.0"),
    Capability("CAP-010", "compute", "start-stop", Level.MAY),
    Capability("CAP-020", "k8s", "kubeconfig-delivery", Level.SHOULD),
    Capability("CAP-030", "dbaas", "credential-delivery", Level.SHOULD),
)

REQUIREMENTS: dict[str, Requirement] = {r.id: r for r in _REQUIREMENTS}
CAPABILITIES: dict[str, Capability] = {c.id: c for c in _CAPABILITIES}


class UnknownRequirementError(KeyError):
    """Raised for an ID that the contract does not define."""


def get_requirement(requirement_id: str) -> Requirement:
    """Look up a CON-ID; unknown IDs are an error, never a silent miss."""
    try:
        return REQUIREMENTS[requirement_id]
    except KeyError:
        raise UnknownRequirementError(requirement_id) from None


def get_capability(capability_id: str) -> Capability:
    """Look up a CAP-ID; unknown IDs are an error, never a silent miss."""
    try:
        return CAPABILITIES[capability_id]
    except KeyError:
        raise UnknownRequirementError(capability_id) from None


def active_requirements() -> tuple[Requirement, ...]:
    """Requirements binding at :data:`CONTRACT_VERSION` (proposals excluded)."""
    return tuple(r for r in _REQUIREMENTS if r.is_active)


def proposed_requirements() -> tuple[Requirement, ...]:
    """Requirements drafted for the next contract version (D-003/D-004)."""
    return tuple(r for r in _REQUIREMENTS if r.status is Status.PROPOSED)


def mandatory_capabilities(service_class: str) -> tuple[Capability, ...]:
    """MUST-level capabilities for a service class, including the 'alle' rows."""
    return tuple(
        c
        for c in _CAPABILITIES
        if c.level is Level.MUST and c.service_class in ("alle", service_class)
    )
