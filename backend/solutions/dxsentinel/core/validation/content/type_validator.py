"""Validacion de tipos de datos (date, integer, decimal, boolean) → ERROR/WARNING."""

from __future__ import annotations

import re
from datetime import datetime

from ..registry import register_validator
from ..result import Severity, ValidationResult
from ..base import BaseValidator, ValidationContext
from .country_date_formats import resolve_date_formats

_MULTI_VALUE_ENTITIES = {
    "homeAddress", "phoneInfo", "emailInfo", "nationalIdCard",
    "workPermitInfo", "personRelationshipInfo", "emergencyContactPrimary",
    "payComponentRecurring", "payComponentNonRecurring",
}


@register_validator
class TypeValidator(BaseValidator):
    """Valida coherencia de tipos de datos en campos del CSV."""

    modes = ("split",)

    def validate(self, ctx: ValidationContext) -> list[ValidationResult]:
        issues: list[ValidationResult] = []

        if not ctx.csv_rows or not ctx.field_catalog:
            return issues

        country_codes = ctx.target_countries or []
        analyzer = ctx.get_entity_analyzer()
        empty_global = ctx.get_empty_entities_global()

        for row_idx, row in enumerate(ctx.csv_rows, start=1):
            row_index = row_idx + 2
            for col in ctx.csv_headers:
                value = row.get(col)
                if value is None or (isinstance(value, str) and value.strip() == ""):
                    continue

                meta = ctx.field_catalog.get(col, {})
                if not meta:
                    continue

                data_type = meta.get("data_type", "string")
                if data_type == "string":
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

                    error = self._validate_type(
                        single_value, data_type, field_id, entity_id,
                        col, row_index, country_codes,
                    )
                    if error:
                        issues.append(error)

        return issues

    def _validate_type(
        self, value: str, data_type: str, field_id: str,
        entity_id: str, column_name: str, row_index: int,
        country_codes: list[str],
    ) -> ValidationResult | None:
        if data_type == "date":
            return self._validate_date(value, field_id, entity_id, column_name, row_index, country_codes)
        elif data_type == "integer":
            return self._validate_integer(value, field_id, entity_id, column_name, row_index)
        elif data_type == "decimal":
            return self._validate_decimal(value, field_id, entity_id, column_name, row_index)
        elif data_type == "boolean":
            return self._validate_boolean(value, field_id, entity_id, column_name, row_index)
        return None

    def _validate_date(
        self, value: str, field_id: str, entity_id: str,
        column_name: str, row_index: int, country_codes: list[str],
    ) -> ValidationResult | None:
        expected_label, patterns = resolve_date_formats(country_codes)

        for regex, fmt in patterns:
            if re.match(regex, value):
                try:
                    datetime.strptime(value, fmt)
                    return None
                except ValueError:
                    continue

        return self._emit(
            Severity.ERROR,
            "INVALID_DATE_FORMAT",
            element_id=entity_id,
            field_id=field_id,
            row_index=row_index,
            column_name=column_name,
            value=value,
            expected=expected_label or "DD/MM/YYYY, YYYY-MM-DD, DD-MM-YYYY",
            countries=", ".join(c.upper() for c in country_codes) if country_codes else "",
        )

    def _validate_integer(
        self, value: str, field_id: str, entity_id: str,
        column_name: str, row_index: int,
    ) -> ValidationResult | None:
        cleaned = re.sub(r"[,\s]", "", value)
        if re.match(r"^-?\d+$", cleaned):
            return None

        return self._emit(
            Severity.ERROR,
            "INVALID_INTEGER",
            element_id=entity_id,
            field_id=field_id,
            row_index=row_index,
            column_name=column_name,
            value=value,
        )

    def _validate_decimal(
        self, value: str, field_id: str, entity_id: str,
        column_name: str, row_index: int,
    ) -> ValidationResult | None:
        cleaned = re.sub(r"[,\s]", "", value)
        if re.match(r"^-?\d+(\.\d+)?$", cleaned):
            return None

        return self._emit(
            Severity.ERROR,
            "INVALID_DECIMAL",
            element_id=entity_id,
            field_id=field_id,
            row_index=row_index,
            column_name=column_name,
            value=value,
        )

    def _validate_boolean(
        self, value: str, field_id: str, entity_id: str,
        column_name: str, row_index: int,
    ) -> ValidationResult | None:
        valid = {"yes", "no", "true", "false", "1", "0", "y", "n", "si", "sí"}
        if value.lower().strip() in valid:
            return None

        return self._emit(
            Severity.WARNING,
            "INVALID_BOOLEAN",
            element_id=entity_id,
            field_id=field_id,
            row_index=row_index,
            column_name=column_name,
            value=value,
        )
