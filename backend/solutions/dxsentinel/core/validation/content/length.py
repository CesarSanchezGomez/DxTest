"""Validacion de longitud maxima de campos → ERROR."""

from __future__ import annotations

from ..registry import register_validator
from ..result import Severity, ValidationResult
from ..base import BaseValidator, ValidationContext

_VALID_BOOLEANS = {"yes", "no", "true", "false", "1", "0", "y", "n", "si", "sí"}

_MULTI_VALUE_ENTITIES = {
    "homeAddress", "phoneInfo", "emailInfo", "nationalIdCard",
    "workPermitInfo", "personRelationshipInfo", "emergencyContactPrimary",
    "payComponentRecurring", "payComponentNonRecurring",
}


@register_validator
class LengthValidator(BaseValidator):
    """Verifica que valores no excedan max_length del field_catalog."""

    modes = ("split",)

    def validate(self, ctx: ValidationContext) -> list[ValidationResult]:
        issues: list[ValidationResult] = []

        if not ctx.csv_rows or not ctx.field_catalog:
            return issues

        analyzer = ctx.get_entity_analyzer()
        empty_global = ctx.get_empty_entities_global()

        for row_idx, row in enumerate(ctx.csv_rows, start=1):
            row_index = row_idx + 2
            for col in ctx.csv_headers:
                value = row.get(col)
                if value is None or (isinstance(value, str) and value.strip() == ""):
                    continue

                meta = ctx.field_catalog.get(col, {})
                max_length = meta.get("max_length")
                if not max_length:
                    continue

                entity_id = meta.get("element", "")

                # Skip entidades vacias
                if entity_id in empty_global:
                    continue
                if analyzer.is_entity_empty_for_row(row, entity_id):
                    continue

                field_id = meta.get("field", "")
                is_multi = entity_id in _MULTI_VALUE_ENTITIES

                values = [v.strip() for v in str(value).split("|")] if is_multi else [str(value).strip()]

                for single_value in values:
                    if not single_value:
                        continue

                    # Exception: boolean con max_length=1
                    if max_length == 1 and single_value.lower().strip() in _VALID_BOOLEANS:
                        continue

                    actual = len(single_value)
                    if actual > max_length:
                        issues.append(self._emit(
                            Severity.ERROR,
                            "MAX_LENGTH_EXCEEDED",
                            element_id=entity_id,
                            field_id=field_id,
                            row_index=row_index,
                            column_name=col,
                            value=single_value[:50] + "..." if len(single_value) > 50 else single_value,
                            max_length=max_length,
                            actual_length=actual,
                        ))

        return issues
