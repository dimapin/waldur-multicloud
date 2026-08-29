from waldur_multicloud import __version__, is_supported_provider, list_supported_providers


def test_supported_provider_list() -> None:
    providers = list_supported_providers()
    assert providers == ("hcloud", "proxmox", "ionos", "stackit")
    assert all(is_supported_provider(provider) for provider in providers)


def test_unknown_provider_is_rejected() -> None:
    assert not is_supported_provider("unknown")


def test_package_version() -> None:
    from importlib.metadata import PackageNotFoundError, version as dist_version

    try:
        assert __version__ == dist_version("waldur-multicloud")
    except PackageNotFoundError:
        assert isinstance(__version__, str) and __version__
