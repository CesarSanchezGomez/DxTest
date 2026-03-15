"""Validacion de formato de email → ERROR."""

from __future__ import annotations

import re

from ..registry import register_validator
from ..result import Severity, ValidationResult
from ..base import BaseValidator, ValidationContext

_EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

_EMAIL_SUFFIXES = (
    "email", "email-address", "email_address", "emailaddress",
    "-email", "_email",
)

_MULTI_VALUE_ENTITIES = {
    "homeAddress", "phoneInfo", "emailInfo", "nationalIdCard",
    "workPermitInfo", "personRelationshipInfo", "emergencyContactPrimary",
    "payComponentRecurring", "payComponentNonRecurring",
}


def _is_email_field(column_name: str) -> bool:
    lower = column_name.lower()
    return any(lower.endswith(s) for s in _EMAIL_SUFFIXES)


@register_validator
class EmailValidator(BaseValidator):
    """Valida formato de email en campos email (ERROR)."""

    modes = ("split",)

    def validate(self, ctx: ValidationContext) -> list[ValidationResult]:
        issues: list[ValidationResult] = []

        if not ctx.csv_rows:
            return issues

        email_columns = [h for h in ctx.csv_headers if _is_email_field(h)]
        if not email_columns:
            return issues

        for row_idx, row in enumerate(ctx.csv_rows, start=1):
            row_index = row_idx + 2
            for col in email_columns:
                value = row.get(col, "")
                if not value or not str(value).strip():
                    continue

                meta = ctx.field_catalog.get(col, {})
                entity_id = meta.get("element", "")
                field_id = meta.get("field", "")
                is_multi = entity_id in _MULTI_VALUE_ENTITIES

                values = [v.strip() for v in str(value).split("|")] if is_multi else [str(value).strip()]

                for email in values:
                    if not email:
                        continue
                    if not _EMAIL_PATTERN.match(email):
                        issues.append(self._emit(
                            Severity.ERROR,
                            "INVALID_EMAIL_FORMAT",
                            element_id=entity_id,
                            field_id=field_id,
                            row_index=row_index,
                            column_name=col,
                            value=email,
                        ))

        return issues
