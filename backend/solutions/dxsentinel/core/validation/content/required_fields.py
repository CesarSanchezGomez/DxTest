"""Validacion de campos required vacios en CSV → ERROR."""

from __future__ import annotations

from ..registry import register_validator
from ..result import Severity, ValidationResult
from ..base import BaseValidator, ValidationContext


@register_validator
class RequiredFieldsValidator(BaseValidator):
    """Verifica que campos marcados como required tengan valor en el CSV."""

    modes = ("split",)

    def validate(self, ctx: ValidationContext) -> list[ValidationResult]:
        issues: list[ValidationResult] = []

        if not ctx.csv_rows or not ctx.field_catalog:
            return issues

        # Campos required del catalogo
        required_fields = {
            fid for fid, entry in ctx.field_catalog.items()
            if entry.get("required")
        }

        # Solo verificar required que estan en el CSV
        required_in_csv = required_fields & set(ctx.csv_headers)

        for row_idx, row in enumerate(ctx.csv_rows, start=1):
            for field_id in required_in_csv:
                value = row.get(field_id, "").strip()
                if not value:
                    entry = ctx.field_catalog.get(field_id, {})
                    issues.append(self._emit(
                        Severity.ERROR,
                        "REQ_001",
                        element_id=entry.get("element", ""),
                        field_id=field_id,
                        row=row_idx,
                    ))

        return issues
