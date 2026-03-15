"""Validacion de formato de fechas en CSV → WARNING."""

from __future__ import annotations

import re

from ..registry import register_validator
from ..result import Severity, ValidationResult
from ..base import BaseValidator, ValidationContext

# Formatos de fecha aceptados
_DATE_PATTERNS = [
    re.compile(r"^\d{2}/\d{2}/\d{4}$"),           # DD/MM/YYYY
    re.compile(r"^\d{4}-\d{2}-\d{2}$"),            # YYYY-MM-DD (ISO)
    re.compile(r"^\d{2}\.\d{2}\.\d{4}$"),          # DD.MM.YYYY
    re.compile(r"^\d{2}-\d{2}-\d{4}$"),            # DD-MM-YYYY
    re.compile(r"^\d{4}/\d{2}/\d{2}$"),            # YYYY/MM/DD
    re.compile(r"^\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}"), # Con hora
]


@register_validator
class DateFormatValidator(BaseValidator):
    """Verifica formato de fechas en campos tipo date del CSV."""

    modes = ("split",)

    def validate(self, ctx: ValidationContext) -> list[ValidationResult]:
        issues: list[ValidationResult] = []

        if not ctx.csv_rows or not ctx.field_catalog:
            return issues

        # Campos tipo date
        date_fields = {
            fid for fid, entry in ctx.field_catalog.items()
            if entry.get("data_type") in ("date", "DATE")
        }

        date_in_csv = date_fields & set(ctx.csv_headers)

        for row_idx, row in enumerate(ctx.csv_rows, start=1):
            for field_id in date_in_csv:
                value = row.get(field_id, "").strip()
                if not value:
                    continue

                # Manejar pipe-separated
                values = [v.strip() for v in value.split("|")]
                for val in values:
                    if not val:
                        continue
                    if not any(p.match(val) for p in _DATE_PATTERNS):
                        entry = ctx.field_catalog.get(field_id, {})
                        issues.append(self._emit(
                            Severity.WARNING,
                            "DATE_001",
                            element_id=entry.get("element", ""),
                            field_id=field_id,
                            row=row_idx,
                            value=val[:30],
                        ))
                        break  # Un warning por campo por fila

        return issues
