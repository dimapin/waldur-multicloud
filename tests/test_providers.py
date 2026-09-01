"""Provider set and backend naming: CON-001, CON-002."""

import pytest

from waldur_multicloud import (
    SERVICE_CLASSES,
    ContractViolation,
    __version__,
    backend_name,
    is_supported_provider,
    list_supported_providers,
    parse_backend_name,
)
from waldur_multicloud.components import BillingType, Component, Offering, Plan, check_offering
from decimal import Decimal


def test_supported_provider_list() -> None:
    providers = list_supported_providers()
    assert providers == ("hcloud", "proxmox", "ionos", "stackit")
    assert all(is_supported_provider(provider) for provider in providers)


def test_unknown_provider_is_rejected() -> None:
    assert not is_supported_provider("unknown")


def test_backend_name_follows_the_scheme() -> None:
    """CON-001: backends are named '<provider>-<service>'."""
    assert backend_name("ionos", "dbaas") == "ionos-dbaas"
    assert parse_backend_name("hcloud-compute") == ("hcloud", "compute")
    assert set(SERVICE_CLASSES) == {"compute", "k8s", "dbaas"}


def test_malformed_backend_name_is_rejected() -> None:
    """CON-001: an unknown provider or a malformed service part fails loudly."""
    for name in ("hcloud", "aws-compute", "hcloud-Compute"):
        with pytest.raises(ContractViolation) as excinfo:
            parse_backend_name(name)
        assert excinfo.value.requirement_ids == ("CON-001",)


def test_offering_maps_to_exactly_one_backend() -> None:
    """CON-002: one offering, one backend — services stay separately orderable."""
    offering = Offering(
        name="Managed Postgres",
        backend="ionos-dbaas",
        service_class="dbaas",
        components=(Component("storage", "GiB", BillingType.LIMIT, Decimal(5), Decimal(100)),),
        plans=(Plan("basic", {"storage": Decimal("0.1")}),),
    )
    assert check_offering(offering) == ()
    assert parse_backend_name(offering.backend)[0] == "ionos"


def test_package_version() -> None:
    from importlib.metadata import PackageNotFoundError, version as dist_version

    try:
        assert __version__ == dist_version("waldur-multicloud")
    except PackageNotFoundError:
        assert isinstance(__version__, str) and __version__
