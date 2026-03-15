"""Motor central de validacion."""

from __future__ import annotations

import logging

from .registry import get_registered_validators
from .result import Severity, ValidationReport, ValidationResult
from .base import BaseValidator, ValidationContext

logger = logging.getLogger(__name__)

# Orden de ejecucion: estructura primero (short-circuit si FATAL)
_PHASE_ORDER = [
    # structure/
    "UploadValidator",
    "XMLStructureValidator",
    "CharacterStructureValidator",
    # content/
    "FieldRulesValidator",
    "FieldFilterValidator",
    "FormatGroupValidator",
    "LabelValidator",
    # country/ validators se ejecutan al final automaticamente
]

# Validators que producen short-circuit en FATAL
_SHORT_CIRCUIT_ON_FATAL = {
    "UploadValidator",
    "XMLStructureValidator",
    "CharacterStructureValidator",
}


class ValidationEngine:
    """Ejecuta validadores registrados y recopila resultados.

    Flujo:
    1. Upload → si hay FATAL (archivo invalido), short-circuit.
    2. XMLStructure → si hay FATAL (modelo roto), short-circuit.
    3. CharacterStructure → FATAL en IDs detiene.
    4. FieldRules → ERROR en coherencia de tipos/visibility.
    5. FieldFilter → WARNING por campos excluidos.
    6. FormatGroup → ERROR/WARNING en format groups.
    7. Label → WARNING en labels.
    8. Country validators → filtrados por target_countries.
    """

    def validate(self, ctx: ValidationContext) -> ValidationReport:
        report = ValidationReport()
        validators = self._build_ordered_validators()

        for validator in validators:
            try:
                results = validator.validate(ctx)
                report.extend(results)
            except Exception as e:
                logger.error("Validator %s failed: %s", validator.name, e)
                report.add(ValidationResult(
                    severity=Severity.ERROR,
                    code="ENGINE_001",
                    message=f"Validator '{validator.name}' fallo: {e}",
                    validator=validator.name,
                ))

            if report.has_fatal and validator.name in _SHORT_CIRCUIT_ON_FATAL:
                logger.warning(
                    "Short-circuit: %s produjo FATAL, deteniendo validacion",
                    validator.name,
                )
                break

        return report

    def _build_ordered_validators(self) -> list[BaseValidator]:
        """Ordena validators: fases conocidas primero, country al final."""
        registered = get_registered_validators()
        by_name: dict[str, BaseValidator] = {}
        country_validators: list[BaseValidator] = []

        for cls in registered:
            instance = cls()
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

        # Validators custom no listados en _PHASE_ORDER
        for instance in by_name.values():
            ordered.append(instance)

        # Country validators al final
        ordered.extend(country_validators)

        return ordered
