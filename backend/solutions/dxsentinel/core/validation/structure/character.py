"""Validacion de caracteres en IDs tecnicos → FATAL.

Los IDs de elementos y campos deben contener solo caracteres validos
para garantizar que el CSV y el split funcionen correctamente.
"""

from __future__ import annotations

import re

from ..registry import register_validator
from ..result import Severity, ValidationResult
from ..base import BaseValidator, ValidationContext

_VALID_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_\-.:]+$")
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


@register_validator
class CharacterStructureValidator(BaseValidator):
    """Verifica caracteres invalidos en IDs tecnicos → FATAL."""

    def validate(self, ctx: ValidationContext) -> list[ValidationResult]:
        issues: list[ValidationResult] = []

        for col in ctx.columns:
            field_id = col.get("field_id", "")
            full_id = col.get("full_id", "")
            element_id = col.get("element_id", "")

            if field_id and not _VALID_ID_PATTERN.match(field_id):
                issues.append(ValidationResult(
                    severity=Severity.FATAL,
                    code="CHAR_001",
                    message=f"Field ID contiene caracteres invalidos: '{field_id}'",
                    element_id=element_id,
                    field_id=field_id,
                    validator=self.name,
                ))

            if full_id and not _VALID_ID_PATTERN.match(full_id):
                issues.append(ValidationResult(
                    severity=Severity.FATAL,
                    code="CHAR_002",
                    message=f"Full field ID contiene caracteres invalidos: '{full_id}'",
                    element_id=element_id,
                    field_id=field_id,
                    validator=self.name,
                ))

            if field_id and _CONTROL_CHARS.search(field_id):
                issues.append(ValidationResult(
                    severity=Severity.FATAL,
                    code="CHAR_003",
                    message=f"Caracteres de control en field ID: '{field_id}'",
                    element_id=element_id,
                    field_id=field_id,
                    validator=self.name,
                ))

        return issues
