"""Validaciones de caracteres.

- En IDs/tags de estructura → FATAL
- En contenido (labels) → WARNING
"""

from __future__ import annotations

import re

from ..registry import register_validator
from ..result import Severity, ValidationResult
from .base import BaseValidator, ValidationContext

# Caracteres validos para IDs tecnicos
_VALID_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_\-.:]+$")

# Caracteres de control (excepto tab/newline/carriage return)
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

# Caracteres problematicos en labels (encoding issues)
_ENCODING_ISSUES = re.compile(r"[\ufffd\ufffe\ufeff]")


@register_validator
class CharacterValidator(BaseValidator):
    """Verifica caracteres invalidos en IDs (FATAL) y en labels (WARNING)."""

    def validate(self, ctx: ValidationContext) -> list[ValidationResult]:
        issues: list[ValidationResult] = []

        self._check_field_ids(ctx.columns, issues)
        self._check_label_characters(ctx.columns, issues)

        return issues

    def _check_field_ids(self, columns: list[dict], issues: list[ValidationResult]) -> None:
        for col in columns:
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

    def _check_label_characters(self, columns: list[dict], issues: list[ValidationResult]) -> None:
        for col in columns:
            node = col.get("node", {})
            labels = node.get("labels", {}) if isinstance(node, dict) else {}
            element_id = col.get("element_id", "")
            field_id = col.get("field_id", "")

            for lang_key, label_text in labels.items():
                if not isinstance(label_text, str):
                    continue

                if _CONTROL_CHARS.search(label_text):
                    issues.append(ValidationResult(
                        severity=Severity.WARNING,
                        code="CHAR_003",
                        message=(
                            f"Caracteres de control en label ({lang_key}): "
                            f"'{label_text[:50]}'"
                        ),
                        element_id=element_id,
                        field_id=field_id,
                        validator=self.name,
                    ))

                if _ENCODING_ISSUES.search(label_text):
                    issues.append(ValidationResult(
                        severity=Severity.WARNING,
                        code="CHAR_004",
                        message=(
                            f"Problemas de encoding en label ({lang_key}): "
                            f"'{label_text[:50]}'"
                        ),
                        element_id=element_id,
                        field_id=field_id,
                        validator=self.name,
                    ))
