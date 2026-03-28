"""Component registry for datasets, models, metrics, and retrievers."""

from typing import Any, Callable

_REGISTRY: dict[str, dict[str, Any]] = {}


def register(category: str, name: str) -> Callable:
    """Decorator to register a component."""
    def decorator(cls: Any) -> Any:
        if category not in _REGISTRY:
            _REGISTRY[category] = {}
        _REGISTRY[category][name] = cls
        return cls
    return decorator


def get(category: str, name: str) -> Any:
    """Retrieve a registered component."""
    if category not in _REGISTRY or name not in _REGISTRY[category]:
        available = list(_REGISTRY.get(category, {}).keys())
        raise KeyError(f"'{name}' not in {category} registry. Available: {available}")
    return _REGISTRY[category][name]


def list_registered(category: str) -> list[str]:
    """List all registered components in a category."""
    return list(_REGISTRY.get(category, {}).keys())
