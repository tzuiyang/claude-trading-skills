from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path

from engine.base_strategy import BaseStrategy

STRATEGY_REGISTRY: dict[str, type[BaseStrategy]] = {}


def _autodiscover() -> None:
    pkg_dir = Path(__file__).parent
    for _finder, module_name, _ in pkgutil.iter_modules([str(pkg_dir)]):
        if module_name.startswith("_"):
            continue
        module = importlib.import_module(f"strategies.{module_name}")
        for attr_name in dir(module):
            obj = getattr(module, attr_name)
            if (
                isinstance(obj, type)
                and issubclass(obj, BaseStrategy)
                and obj is not BaseStrategy
                and hasattr(obj, "metadata")
            ):
                STRATEGY_REGISTRY[obj.metadata.name] = obj


_autodiscover()
