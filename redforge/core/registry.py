"""redforge.core.registry - attack auto-discovery.

The registry imports every module in the attacks package and collects every
BaseAttack subclass that declares real metadata.

The payoff: adding a new attack = dropping one file in redforge/attacks/.
No registration table, no imports to edit. This is what makes the toolkit
extensible by design.
"""
from __future__ import annotations

import importlib
import inspect
import pkgutil

from redforge.core.base_attack import BaseAttack, PromptAttack

ATTACK_PACKAGE = "redforge.attacks"


def discover_attacks(package: str = ATTACK_PACKAGE) -> list[type[BaseAttack]]:
    """Import the attacks package and return every usable attack class."""
    pkg = importlib.import_module(package)
    found: list[type[BaseAttack]] = []

    for mod_info in pkgutil.iter_modules(pkg.__path__, prefix=package + "."):
        module = importlib.import_module(mod_info.name)
        for _, obj in inspect.getmembers(module, inspect.isclass):
            # Skip the abstract bases themselves.
            if obj is BaseAttack or obj is PromptAttack:
                continue
            if not issubclass(obj, BaseAttack):
                continue
            meta = getattr(obj, "meta", None)
            if meta is not None and getattr(meta, "id", ""):
                found.append(obj)

    # Dedupe by id (safe against modules re-exporting the same class).
    unique: dict[str, type[BaseAttack]] = {}
    for cls in found:
        unique.setdefault(cls.meta.id, cls)
    return list(unique.values())


def filter_by_suites(
    attack_classes: list[type[BaseAttack]], suites: list[str]
) -> list[type[BaseAttack]]:
    """Keep only attacks whose category is in `suites`. Empty = keep all."""
    if not suites:
        return attack_classes
    wanted = set(suites)
    return [c for c in attack_classes if c.meta.category in wanted]


def instantiate(attack_classes: list[type[BaseAttack]]) -> list[BaseAttack]:
    """Turn attack classes into runnable instances."""
    return [cls() for cls in attack_classes]
