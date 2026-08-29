from waldur_multicloud import __version__, is_supported_provider, list_supported_providers


def test_supported_provider_list() -> None:
    providers = list_supported_providers()
    assert providers == ("hcloud", "proxmox", "ionos", "stackit")
    assert all(is_supported_provider(provider) for provider in providers)


def test_unknown_provider_is_rejected() -> None:
    assert not is_supported_provider("unknown")


def test_package_version() -> None:
    assert __version__ == "0.1.0"
