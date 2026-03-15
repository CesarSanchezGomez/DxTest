"""Validacion de formato de national-id contra format_groups del metadata → ERROR."""

from __future__ import annotations

import re

from ..registry import register_validator
from ..result import Severity, ValidationResult
from ..base import BaseValidator, ValidationContext

_TARGET_FIELD_ID = "national-id"
_TARGET_ENTITY_ID = "nationalIdCard"
_FORMAT_GROUP_KEY = "national-id"


@register_validator
class NationalIdFormatValidator(BaseValidator):
    """Valida national-id contra patrones regex de format_groups por pais."""

    modes = ("split",)

    def validate(self, ctx: ValidationContext) -> list[ValidationResult]:
        issues: list[ValidationResult] = []

        if not ctx.csv_rows or not ctx.format_groups:
            return issues

        country_codes = [c.upper() for c in (ctx.target_countries or [])]
        compiled = self._build_compiled_patterns(ctx.format_groups, country_codes)
        if not compiled:
            return issues

        # Buscar columna national-id
        nid_col = None
        for h in ctx.csv_headers:
            if h.startswith(f"{_TARGET_ENTITY_ID}_") and h.endswith(f"_{_TARGET_FIELD_ID}"):
                nid_col = h
                break
            if h == f"{_TARGET_ENTITY_ID}_{_TARGET_FIELD_ID}":
                nid_col = h
                break

        if not nid_col:
            return issues

        for row_idx, row in enumerate(ctx.csv_rows, start=1):
            value = row.get(nid_col, "")
            if not value or not str(value).strip():
                continue

            row_index = row_idx + 2
            values = [v.strip() for v in str(value).split("|")]

            for single_value in values:
                if not single_value:
                    continue

                # Valido si coincide con patron de CUALQUIER pais activo
                valid = False
                for patterns in compiled.values():
                    for pat in patterns:
                        if pat["regex"].match(single_value):
                            valid = True
                            break
                    if valid:
                        break

                if not valid:
                    expected_formats = [
                        f"{country}: {pat['display_format']}"
                        for country, patterns in compiled.items()
                        for pat in patterns
                        if pat["display_format"]
                    ]
                    countries = ", ".join(country_codes)
                    fmt_str = " | ".join(expected_formats) if expected_formats else ""

                    issues.append(self._emit(
                        Severity.ERROR,
                        "INVALID_NATIONAL_ID_FORMAT",
                        element_id=_TARGET_ENTITY_ID,
                        field_id=_TARGET_FIELD_ID,
                        row_index=row_index,
                        column_name=nid_col,
                        value=single_value,
                        countries=countries,
                        formats=fmt_str,
                    ))

        return issues

    @staticmethod
    def _build_compiled_patterns(
        format_groups: dict, country_codes: list[str],
    ) -> dict[str, list[dict]]:
        compiled: dict[str, list[dict]] = {}
        for country in country_codes:
            fg = format_groups.get(country, {}).get(_FORMAT_GROUP_KEY)
            if not fg:
                continue
            patterns = []
            for fmt in fg.get("formats", []):
                raw_regex = fmt.get("reg_ex")
                if not raw_regex:
                    continue
                try:
                    patterns.append({
                        "regex": re.compile(f"^(?:{raw_regex})$"),
                        "display_format": fmt.get("display_format", ""),
                        "format_id": fmt.get("id", ""),
                    })
                except re.error:
                    pass
            if patterns:
                compiled[country] = patterns
        return compiled
