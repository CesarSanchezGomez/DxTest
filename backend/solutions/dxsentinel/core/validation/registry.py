"""Registro y descubrimiento automatico de validadores."""

from __future__ import annotations

import importlib
import pkgutil
from typing import Type

_REGISTRY: list[type] = []


def register_validator(cls: type) -> type:
    """Decorador para registrar un validador automaticamente."""
    if cls not in _REGISTRY:
        _REGISTRY.append(cls)
    return cls


def get_registered_validators() -> list[type]:
    """Retorna todos los validadores registrados, descubriendolos si es necesario."""
    _discover_all()
    return list(_REGISTRY)


_DISCOVERED = False


def _discover_all() -> None:
    """Importa todos los modulos de structure/, content/ y country/
    para activar los decoradores @register_validator."""
    global _DISCOVERED
    if _DISCOVERED:
        return
    _DISCOVERED = True

    _discover_package("structure")
    _discover_package("content")
    _discover_package("country")


def _discover_package(subpackage: str) -> None:
    """Importa todos los modulos de un subpaquete de validation/."""
    try:
        pkg = importlib.import_module(f".{subpackage}", package=__package__)
    except ImportError:
        return

    for _importer, module_name, _is_pkg in pkgutil.iter_modules(pkg.__path__):
        if module_name.startswith("_") or module_name == "base":
            continue
        importlib.import_module(f".{module_name}", package=pkg.__name__)
