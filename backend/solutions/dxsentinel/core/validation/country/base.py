"""Clase base para validadores especificos por pais."""

from __future__ import annotations

from abc import abstractmethod

from ..result import ValidationResult
from ..base import BaseValidator, ValidationContext


class CountryValidator(BaseValidator):
    """Validador que solo se ejecuta si su pais esta en target_countries."""

    @property
    @abstractmethod
    def country_code(self) -> str:
        """Codigo ISO del pais (ej: 'MX', 'DE')."""

    def validate(self, ctx: ValidationContext) -> list[ValidationResult]:
        if ctx.target_countries and self.country_code not in ctx.target_countries:
            return []
        return self.validate_country(ctx)

    @abstractmethod
    def validate_country(self, ctx: ValidationContext) -> list[ValidationResult]:
        """Validaciones especificas del pais."""
