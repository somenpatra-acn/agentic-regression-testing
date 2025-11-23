"""Application adapters for different application types."""

from adapters.base_adapter import BaseApplicationAdapter, Element, DiscoveryResult
from adapters.web_adapter import WebAdapter
from adapters.api_adapter import APIAdapter
from adapters.oracle_ebs_adapter import OracleEBSAdapter

# Adapter registry
ADAPTER_REGISTRY = {
    "web_adapter": WebAdapter,
    "web": WebAdapter,  # Alias for backwards compatibility
    "api_adapter": APIAdapter,
    "api": APIAdapter,  # Alias for backwards compatibility
    "oracle_ebs_adapter": OracleEBSAdapter,
    "oracle_ebs": OracleEBSAdapter,  # Alias for backwards compatibility
}


def get_adapter(adapter_name: str, app_profile) -> BaseApplicationAdapter:
    """
    Get adapter instance by name.

    Args:
        adapter_name: Name of the adapter
        app_profile: Application profile

    Returns:
        Adapter instance
    """
    adapter_class = ADAPTER_REGISTRY.get(adapter_name)
    if not adapter_class:
        raise ValueError(f"Unknown adapter: {adapter_name}")
    return adapter_class(app_profile)


def register_adapter(name: str, adapter_class: type) -> None:
    """
    Register a custom adapter.

    Args:
        name: Adapter name
        adapter_class: Adapter class
    """
    ADAPTER_REGISTRY[name] = adapter_class


__all__ = [
    "BaseApplicationAdapter",
    "Element",
    "DiscoveryResult",
    "WebAdapter",
    "APIAdapter",
    "OracleEBSAdapter",
    "get_adapter",
    "register_adapter",
    "ADAPTER_REGISTRY",
]
