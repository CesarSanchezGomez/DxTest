"""Motor central de validacion."""

from __future__ import annotations

import logging

from .registry import get_registered_validators
from .result import Severity, ValidationReport, ValidationResult
from .base import BaseValidator, ValidationContext
from .messages import Messages

logger = logging.getLogger(__name__)

# Orden de ejecucion: estructura primero (short-circuit si FATAL)
_PHASE_ORDER = [
    # structure/ (solo mode=generation)
    "UploadValidator",
    "XMLStructureValidator",
    "CharacterStructureValidator",
    # content/ (ambos modos, segun su .modes)
    "FieldRulesValidator",
    "FieldFilterValidator",
    "FormatGroupValidator",
    "LabelValidator",
    # csv data validators (solo mode=split)
    "RequiredFieldsValidator",
    "DateFormatValidator",
    # country/ validators se ejecutan al final automaticamente
]

# Validators que producen short-circuit en FATAL
_SHORT_CIRCUIT_ON_FATAL = {
    "UploadValidator",
    "XMLStructureValidator",
    "CharacterStructureValidator",
}


class ValidationEngine:
    """Ejecuta validadores registrados, filtrando por ctx.mode."""

    def validate(self, ctx: ValidationContext) -> ValidationReport:
        report = ValidationReport()
        validators = self._build_ordered_validators(ctx.mode)

        for validator in validators:
            try:
                results = validator.validate(ctx)
                report.extend(results)
            except Exception as e:
                logger.error("Validator %s failed: %s", validator.name, e)
                report.add(ValidationResult(
                    severity=Severity.ERROR,
                    code="ENGINE_001",
                    message=Messages.get("ENGINE_001", validator=validator.name, error=e),
                    validator=validator.name,
                ))

            if report.has_fatal and validator.name in _SHORT_CIRCUIT_ON_FATAL:
                logger.warning(
                    "Short-circuit: %s produjo FATAL, deteniendo validacion",
                    validator.name,
                )
                break

        return report

    def _build_ordered_validators(self, mode: str) -> list[BaseValidator]:
        """Ordena validators y filtra por modo."""
        registered = get_registered_validators()
        by_name: dict[str, BaseValidator] = {}
        country_validators: list[BaseValidator] = []

        for cls in registered:
            instance = cls()
            # Filtrar por modo
            if mode not in instance.modes:
                continue
            name = instance.name
            from .country.base import CountryValidator
            if isinstance(instance, CountryValidator):
                country_validators.append(instance)
            else:
                by_name[name] = instance

        ordered: list[BaseValidator] = []

        for name in _PHASE_ORDER:
            if name in by_name:
                ordered.append(by_name.pop(name))

        for instance in by_name.values():
            ordered.append(instance)

        ordered.extend(country_validators)
        return ordered
