from typing import Callable, Dict, List, Optional


class EngineRegistry:
    """Lightweight registry for calculator engines."""

    def __init__(self) -> None:
        self._engines: Dict[str, Callable] = {}

    def register(self, name: str, factory: Callable) -> None:
        if name in self._engines:
            raise ValueError(f"Engine '{name}' already registered")
        self._engines[name] = factory

    def get(self, name: str) -> Callable:
        if name not in self._engines:
            raise KeyError(f"Engine '{name}' not found")
        return self._engines[name]

    def available(self) -> List[str]:
        return sorted(self._engines.keys())


registry = EngineRegistry()


def register_engine(name: str):
    """Decorator for registering calculator engines."""

    def decorator(factory: Callable):
        registry.register(name, factory)
        return factory

    return decorator


def resolve_engine(name: Optional[str]) -> Callable:
    target = name or "thermocalc"
    return registry.get(target)

