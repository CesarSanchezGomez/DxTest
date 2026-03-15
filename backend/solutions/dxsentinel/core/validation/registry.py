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
    """Importa todos los modulos de validators/ y validators/country/ para
    activar los decoradores @register_validator."""
    global _DISCOVERED
    if _DISCOVERED:
        return
    _DISCOVERED = True

    from . import validators as validators_pkg

    # Importar validadores de primer nivel (structure, content, label, character)
    for _importer, module_name, _is_pkg in pkgutil.iter_modules(validators_pkg.__path__):
        if module_name.startswith("_") or module_name == "base":
            continue
        if module_name == "country":
            continue
        importlib.import_module(f".{module_name}", package=validators_pkg.__name__)

    # Importar validadores por pais
    from .validators import country as country_pkg
    for _importer, module_name, _is_pkg in pkgutil.iter_modules(country_pkg.__path__):
        if module_name.startswith("_") or module_name == "base":
            continue
        importlib.import_module(f".{module_name}", package=country_pkg.__name__)
